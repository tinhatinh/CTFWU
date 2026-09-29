# Justified — Web (Medium)

**Flag:** `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` · Submitted on WebVerse (the page returned SOLVED)

## Challenge

Marlowe & Sons is a thesis bookbinding shop. The "Instant Cover Proof" tool takes thesis details from a form, typesets the cover on the shop's own typesetter, and returns a PDF along with the typesetter's log for the printer to read before running the blade. The challenge's tag is `CMDI`, and the wording "read what the typesetter reports back" points straight at the log channel.

No accounts, no upload: just one `POST /proof.php` form.

## Initial Analysis

The form has 9 fields: `title`, `author`, `degree`, `department`, `institution`, `supervisor`, `year`,
`abstract`, `reference`. The `reference` field is described as "names your download", while `title` comes with a very
notable hint:

> Tip: type accented characters and symbols using LaTeX, e.g. `M\"uller`, `\'Etienne`, `\OE`.
> Our typesetter renders them for you.

That is both a feature and a confession: the user-supplied string is spliced straight into the LaTeX source.

Sending one valid request and reading the log block in the response tells us exactly what is running:

```
This is pdfTeX, Version 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)
(preloaded format=pdflatex) \write18 enabled.
entering extended mode
(./main.tex
```

Three decisive details:

1. The app generates `main.tex` from our input and then calls `pdflatex`.
2. `\write18 enabled.` - shell escape is fully on, not in `restricted` mode.
3. The entire log (stderr included) is echoed back to the sender.

## Approaches Ruled Out

1. Direct shell injection in the text fields (`$(id)`, backtick, `|id`, `;id` in `title`/`year`):
   the log changes not at all. Ruled out - these fields never pass through a shell.
2. Injection through `reference` (the field that "names the download", the likeliest place to be spliced into
   `mv`/`-jobname`): every payload `ref1;id`, `ref1$(id)`, `ref1|id`, `ref1&&id`, `ref1\nid` produces the same jobname
   `ref1id.pdf`. This field is whitelisted down to `[A-Za-z0-9_-]`. Ruled out - and this is the challenge's trap:
   the field that looks most vulnerable is the most sanitised one.
3. Needing `restricted \write18`: under restricted mode only commands on an allow list would run.
   The string `\write18 enabled.` (with no "restricted") in the log's first line already refutes this.

## Exploit Chain

**Step 1 - Proving `title` is a LaTeX injection.** plant a harmless but observable macro:

```
A\typeout{ZZMARKERZZ}
```

`ZZMARKERZZ` appears verbatim in the log. That means our backslash is not filtered and TeX parses and executes
user-supplied macros.

The technical trap at this step: when calling through `fetch()` in devtools, the JS string `'A\typeout{...}'` loses
the backslash right at JS's escape layer (`\t` becomes a tab), which made the first probe wrongly conclude that
`title` is filtered as well. The payload had to be built with `String.fromCharCode(92)` before any conclusion.

**Step 2 - Firing the shell escape.** With full `\write18`, one macro is enough to run a system command:

```
\immediate\write18{<command>}
```

**Step 3 - Choosing the data channel.** Once the command finishes, where is the result? Three options:
write it to a file and `\input` it into the document (the result lands in the PDF, so you must download and read the
PDF), or redirect into pdflatex's stderr - which the app already shows us for free. The last channel is chosen:

```
C\immediate\write18{cat /flag.txt 1>&2}
```

`\write18` spawns a child process that inherits pdflatex's file descriptors, so `1>&2` sends `cat`'s stdout into the
stream the app collects into the log. No need to touch the PDF, no need to write a file.

The result comes back directly in the log:

```
WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```

**Step 4 - Packaging and re-running standalone.** `exploit.py` uses `requests`, no cookies or accounts needed;
it probes `id` to confirm the shell escape still works and then runs the command. Two small bugs found while packaging
were fixed: the log sits inside `<pre class=...>` so the regex must be `<pre[^>]*>`, and the server returns a different
page when a browser-style `User-Agent` is missing.

## Flag
```bash
python exploit.py https://978870f9-5765-justified-06d98.mystery-challenges.webverselabs-pro.com
```

```
[*] shell escape works: uid=33(www-data) gid=33(www-data) groups=33(www-data)
[+] flag: WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```

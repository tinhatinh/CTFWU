---
title: "Don't fill me"
category: "Misc"
tags: ["google-form", "fb_public_load_data", "language-parameter", "plaintext-reading"]
solve_date: "2026-10-09"
language: "en"
---

# Don't fill me

**Flag:** `OWASP{Thank_you_for_participating!!}`
**Target:** `https://docs.google.com/forms/d/e/1FAIpQLSdm3ndV0ZckRmnABXjalIcRu6Dc46dowK5q0OY1EG-cjT1mGQ/viewform` — a Google Form titled "ByteMe CTF FeedBack Form", 31 questions.

## Challenge

The description line on the challenge card:

```text
fill this we need to submit it to our faculty :(
```

Expert, 500 points, author Suyog Jadhav. The card showed 0 solves at the time of the work.

## Analysis

### The target

The page is a public Google Form titled `ByteMe CTF FeedBack Form` with 31 questions and no login required to view it. No response was ever submitted during the work: the flag sits in the page, no interaction with the form is needed.

Every Google viewform page embeds an `FB_PUBLIC_LOAD_DATA_` array. The relevant layout:

```text
FB_PUBLIC_LOAD_DATA_[1][1]    item list (questions)
FB_PUBLIC_LOAD_DATA_[1][2][0] post-submission message slot
```

### The hl observation

The form was built by a Vietnamese organizer, so its default render is `vi`. Requesting it with `?hl=en` puts a different string in the very same slot:

```text
default render (vi) : "Your response has been recorded"
render with hl=en   : "OWASP{Thank_you_for_participating!!}"
```

Both renders are the same page and the same position in the data structure; only the value of that slot differs. The captures saved in the workspace make this countable:

```console
$ for f in viewform.html viewform_en.html v2.html fbld.json fbld_en.json; do
>   printf "%-18s OWASP{=%d  recorded=%d\n" "$f" \
>     "$(grep -o 'OWASP{' $f | wc -l)" "$(grep -o 'Your response has been recorded' $f | wc -l)"
> done
viewform.html      OWASP{=0  recorded=1
viewform_en.html   OWASP{=1  recorded=0
v2.html            OWASP{=1  recorded=0
fbld.json          OWASP{=0  recorded=1
fbld_en.json       OWASP{=1  recorded=0
```

`viewform.html` is the `vi` render, `viewform_en.html` and `v2.html` are two separate fetches with `hl=en`, and `fbld.json`/`fbld_en.json` are the `FB_PUBLIC_LOAD_DATA_` arrays taken from the two renders respectively. The `recorded` column counts the string `Your response has been recorded`.

Several other `hl` values were tried during the work — `en`, `en-US`, `hi`, `fr`, `es`, `de`, `ja`, `pt-BR` — and all returned the same `OWASP{...}` string; only the original `vi` render differs.

### Why the string is most likely author-planted

This is reasoning from the observations above, not a claim verified against the platform:

- Slot `[1][2][0]` is the free-text field the form owner fills in for the "after submitting" step in the form builder, i.e. an organizer-managed field.
- The `vi` render of that same slot shows `Your response has been recorded`, Google's default text for the field; since the form's display language was not switched, the default is what stays visible.
- Google does not insert `OWASP{...}`-style text into confirmation messages.

The explanation requiring the fewest assumptions across all three observations is that `OWASP{Thank_you_for_participating!!}` was planted by the challenge author in the confirmation message, and it only surfaces when the render is not `vi`.

## Solution

No response needs to be submitted; the confirmation field is read from the English render:

```console
$ curl -s "https://docs.google.com/forms/d/e/1FAIpQLSdm3ndV0ZckRmnABXjalIcRu6Dc46dowK5q0OY1EG-cjT1mGQ/viewform?hl=en" -o viewform_en.html
$ grep -o 'OWASP{[^}]*}' viewform_en.html
OWASP{Thank_you_for_participating!!}
```

Reading the exact slot in the data structure, over both extracted `FB_PUBLIC_LOAD_DATA_` arrays:

```console
$ python -c "
import json
for f in ('fbld.json','fbld_en.json'):
    d=json.load(open(f,encoding='utf8')); print(f,'items=%d'%len(d[1][1]),'slot[1][2][0]=',repr(d[1][2][0]))"
fbld.json items=31 slot[1][2][0]= 'Your response has been recorded'
fbld_en.json items=31 slot[1][2][0]= 'OWASP{Thank_you_for_participating!!}'
```

Both arrays carry the same number of items (31), which confirms the two files are renders of one form rather than two different content versions.

## Result

```text
OWASP{Thank_you_for_participating!!}
```

The flag was read from the remote page, from slot `FB_PUBLIC_LOAD_DATA_[1][2][0]` of the `hl=en` render; no response was submitted and no login step was involved. The event's solved table lists this challenge as solved.

## Reproduce

Requires `curl` or `requests`, and the form URL must still be reachable — the solution depends on the page being online, not on a local artifact.

```console
$ curl -s ".../viewform"       -o viewform.html
$ curl -s ".../viewform?hl=en" -o viewform_en.html
$ grep -o 'OWASP{[^}]*}' viewform_en.html
```

If the form changes or becomes unavailable, reproduction requires a saved HTML capture.

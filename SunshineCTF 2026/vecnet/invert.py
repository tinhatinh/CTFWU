#!/usr/bin/env python
"""Invert the one embedding in VecNetDB that has no stored document.

`user_password_requirements` is `type: embedding_only` -- the author deliberately withheld its
text, so it is the vec2text target. The metadata names `jxm/gtr__nq__32`, which is exactly the
checkpoint vec2text's supported "gtr-base" path loads, and Greg's mail supplies the two knobs
that make the search reproducible: num_steps=4, sequence_beam_width=5.

Control first: re-invert a string whose vector we also have (`magic_string` / `sunshinectf8_`).
If the pipeline cannot recover that, nothing the pipeline says about the target means anything.
Then a cosine oracle from the corrector's own frozen GTR lets us repair single-token errors in
the hypothesis without guessing.
"""
import json, os, sys, time, types
sys.modules.setdefault("resource", types.ModuleType("resource"))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import numpy as np
import torch
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
torch.set_num_threads(os.cpu_count() or 4)

def log(*a):
    print(*a, flush=True)

d = json.load(open("analysis/chroma_dump.json"))
VEC = {}
for rid, e in zip(d["ids"], d["embeddings"]):
    arr = e["embedding"] if isinstance(e, dict) and "embedding" in e else e
    VEC[rid] = np.asarray(arr, dtype=np.float32)

import vec2text
import transformers

# vec2text was written against transformers 4: it pins low_cpu_mem_usage=True, and transformers 5
# honours that by building the model inside an `init_empty_weights()` block, which sets the global
# default device to `meta`. vec2text's own InversionModel.__init__ then loads a *real* T5
# checkpoint from that nested context and transformers 5 refuses to load weights on meta.
# Materialising on cpu for the duration of each nested from_pretrained is what a normal, non-
# memory-optimized load would have done anyway.
def _no_meta(f):
    def g(cls, *a, **kw):
        prev = torch.get_default_device()
        if prev == torch.device("meta"):
            torch.set_default_device(torch.device("cpu"))
        kw.pop("device_map", None)
        kw["low_cpu_mem_usage"] = False
        try:
            return f(cls, *a, **kw)
        finally:
            if prev == torch.device("meta"):
                torch.set_default_device(prev)
    return classmethod(g)

for _cls in (transformers.AutoModelForSeq2SeqLM, transformers.AutoModel,
             transformers.AutoModelForCausalLM, transformers.PreTrainedModel):
    _cls.from_pretrained = _no_meta(_cls.from_pretrained.__func__)

log("[*] loading gtr-base corrector ...")
t0 = time.time()
corrector = vec2text.load_pretrained_corrector("gtr-base")
log("[*] loaded in %.1fs, device=%s" % (time.time() - t0, corrector.inversion_trainer.model.device))

def cos(rid, text):
    inp = corrector.embedder_tokenizer([text], return_tensors="pt", max_length=128,
                                       truncation=True, padding="max_length")
    inp = {k: v.to(corrector.inversion_trainer.model.device) for k, v in inp.items()}
    with torch.no_grad():
        e = corrector.inversion_trainer.call_embedding_model(**inp)[0].float().cpu().numpy()
    a, b = VEC[rid], e
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))

STEPS, BEAM = 4, 5

def inv(rid):
    emb = torch.tensor(VEC[rid]).unsqueeze(0).to(corrector.inversion_trainer.model.device)
    t = time.time()
    out = vec2text.invert_embeddings(emb, corrector, num_steps=STEPS, sequence_beam_width=BEAM)
    log("   (%.1fs)" % (time.time() - t))
    return out

log("[*] control: does the pipeline reproduce a text we already know?")
log("    round-trip re-embed of the known string -> %r"
    % (vec2text.invert_strings(["sunshinectf8_"], corrector, num_steps=0,
                               sequence_beam_width=0),))
hyp = inv("magic_string")
log("    inversion of magic_string vec -> %r  cos=%.4f"
    % (hyp, cos("magic_string", hyp[0]) if hyp else -1))

log("[*] target: user_password_requirements")
hyp = inv("user_password_requirements")
log("    -> %r" % (hyp,))
for h in hyp:
    log("    cos(target vec | %-70r) = %.4f" % (h, cos("user_password_requirements", h)))
json.dump({"hyp": hyp}, open("analysis/inversion_target.json", "w"))

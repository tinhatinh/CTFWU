#!/usr/bin/env python
"""Positive control before trusting any inversion.

The collection says embedding_fn = jxm/gtr__nq__32, which is also the exact checkpoint vec2text
inverts. If loading that model with sentence-transformers reproduces the two *known* stored
vectors (`magic_string`, `user_hash_sha256`) to ~1.0 cosine, then (a) our pooling matches the
author's, and (b) we get a free oracle: any candidate password can be embedded and compared
against the stored unknown vector instead of relying on the inversion to be letter-perfect.
"""
import json, sys, types
sys.modules.setdefault("resource", types.ModuleType("resource"))
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import numpy as np
from sentence_transformers import SentenceTransformer

d = json.load(open("analysis/chroma_dump.json"))
V = {}
for rid, e in zip(d["ids"], d["embeddings"]):
    arr = e["embedding"] if isinstance(e, dict) and "embedding" in e else e
    V[rid] = np.asarray(arr, dtype=np.float64)

m = SentenceTransformer("jxm/gtr__nq__32", device="cpu")
print("[*] loaded", flush=True)
known = {"magic_string": "sunshinectf8_",
         "user_hash_sha256": "d8dd241199d2617765d7613fdd1df5358297b55f258647fe463de586bbfe3ebf"}
for rid, text in known.items():
    for tag, kw in [("plain", {}), ("padded", {"truncate_normalized_embeddings_": False})]:
        try:
            v = m.encode([text], convert_to_numpy=True, **kw)[0].astype(np.float64)
        except TypeError:
            v = m.encode([text], convert_to_numpy=True)[0].astype(np.float64)
        a, b = V[rid], v
        print("%-26s %-7s dim=%d cos=%.6f" % (rid, tag, len(b), float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))), flush=True)

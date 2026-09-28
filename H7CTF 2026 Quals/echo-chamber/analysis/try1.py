"""Thu: nop mot record vao collection roi chay /analyze de xem Atlas danh gia the nao."""
import json
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cli


def analyze(tag):
    c, o = cli.req("POST", "/api/incidents/INC-7421/analyze")
    print("[%s] analyze -> %s %s" % (tag, c, json.dumps(o)[:600]))
    c, inc = cli.req("GET", "/api/incidents/INC-7421")
    print("    state:", {k: inc[k] for k in ("status", "corroboration_status",
                                             "diagnostic_depth", "corroborated_root_cause")})
    c, an = cli.req("GET", "/api/incidents/INC-7421/analyses")
    top = an[0]
    print("    top analysis: rel=%s conf=%s sup=%s ret=%s status=%s"
          % (top["relation"], top["confidence"], top["supporting_count"],
             top["retrieved_count"], top["status"]))
    for cit in top["citations"]:
        print("       %-9s %-12s %s" % (cit["evidence_id"], cit["relation"],
                                        cit["claim"][:110]))
    for cit in top.get("rejected_citations", []):
        print("       REJECT %-9s %-12s %s" % (cit["evidence_id"], cit["relation"],
                                               cit["claim"][:110]))
    c, rp = cli.req("GET", "/api/incidents/INC-7421/reports")
    print("    reports:", [(r["report_id"], r["diagnostic_depth"]) for r in rp])
    return top


def submit(title, content, product="StreamForge", version="4.8"):
    c, o = cli.req("POST", "/api/research/submissions",
                   dict(product=product, version=version, title=title, content=content))
    print("submit -> %s %s" % (c, json.dumps(o)[:800]))
    return o


if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else \
        "Postmortem: 4.8 worker-runtime allocator regression"
    body = sys.argv[2] if len(sys.argv) > 2 else (
        "During a StreamForge 4.8 rollout the customer recorded repeated unexpected worker "
        "terminations in the worker-runtime tier. Core files and allocator telemetry showed "
        "heap and allocator corruption inside the 4.8 allocator, and the same workloads ran "
        "for weeks without a single exit after rolling back to 4.7. The regression is the "
        "allocator change shipped in the 4.8 worker-runtime branch. Recommendation: roll back "
        "to 4.7 or apply the vendor allocator fix, and keep comparing worker restart rates."
    )
    r = submit(title, body)
    analyze("after-submit")

import z3

from hdl import parse, build, WIDTH

SAMPLE_BITS = 16


def certify(reference_src, submission_src):
    ref = parse(reference_src)
    sub = parse(submission_src)
    sample = z3.BitVec("sample", SAMPLE_BITS)
    a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)
    solver = z3.Solver()
    solver.set("timeout", 15000)
    solver.add(build(ref, a) != build(sub, a))
    return solver.check() == z3.unsat

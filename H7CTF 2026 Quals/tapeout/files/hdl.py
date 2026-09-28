import z3

WIDTH = 32
MASK = (1 << WIDTH) - 1

UNARY = {"not"}
SHIFTS = {"shl", "shr"}
BINARY = {"and", "or", "xor", "add", "eq"}


def parse_int(s):
    v = int(s, 0)
    if v < 0 or v > MASK:
        raise ValueError("literal out of range: " + s)
    return v


def parse(src, max_gates=4096):
    inp = None
    out = None
    order = []
    defs = {}

    def ref(name):
        if name not in defs:
            raise ValueError("undefined signal: " + name)

    for raw in src.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tok = line.split()
        if tok[0] == "input":
            if inp is not None or len(tok) != 2:
                raise ValueError("bad input decl")
            inp = tok[1]
            defs[inp] = ("input",)
            continue
        if tok[0] == "output":
            if out is not None or len(tok) != 2:
                raise ValueError("bad output decl")
            out = tok[1]
            continue
        if len(tok) < 3 or tok[1] != "=":
            raise ValueError("bad statement: " + line)
        name, op, args = tok[0], tok[2], tok[3:]
        if name in defs:
            raise ValueError("redefined signal: " + name)
        if op == "const":
            if len(args) != 1:
                raise ValueError("const arity")
            defs[name] = ("const", parse_int(args[0]))
        elif op in UNARY:
            if len(args) != 1:
                raise ValueError(op + " arity")
            ref(args[0])
            defs[name] = (op, args[0])
        elif op in SHIFTS:
            if len(args) != 2:
                raise ValueError(op + " arity")
            ref(args[0])
            n = parse_int(args[1])
            if n >= WIDTH:
                raise ValueError("shift amount too large")
            defs[name] = (op, args[0], n)
        elif op == "mux":
            if len(args) != 3:
                raise ValueError("mux arity")
            for a in args:
                ref(a)
            defs[name] = ("mux", args[0], args[1], args[2])
        elif op in BINARY:
            if len(args) != 2:
                raise ValueError(op + " arity")
            for a in args:
                ref(a)
            defs[name] = (op, args[0], args[1])
        else:
            raise ValueError("unknown op: " + op)
        order.append(name)
        if len(order) > max_gates:
            raise ValueError("too many gates")

    if inp is None or out is None:
        raise ValueError("need one input and one output")
    if out not in defs:
        raise ValueError("output signal undefined")
    return {"input": inp, "output": out, "order": order, "defs": defs}


def _sim(d, env):
    op = d[0]
    if op == "const":
        return d[1]
    if op == "not":
        return (~env[d[1]]) & MASK
    if op == "shl":
        return (env[d[1]] << d[2]) & MASK
    if op == "shr":
        return env[d[1]] >> d[2]
    if op == "mux":
        s = env[d[1]]
        return (env[d[2]] & s) | (env[d[3]] & (~s & MASK))
    x, y = env[d[1]], env[d[2]]
    if op == "and":
        return x & y
    if op == "or":
        return x | y
    if op == "xor":
        return x ^ y
    if op == "add":
        return (x + y) & MASK
    if op == "eq":
        return MASK if x == y else 0
    raise ValueError(op)


def simulate(net, a_val):
    env = {net["input"]: a_val & MASK}
    for name in net["order"]:
        env[name] = _sim(net["defs"][name], env)
    return env[net["output"]] & MASK


def _z3(d, env):
    op = d[0]
    if op == "const":
        return z3.BitVecVal(d[1], WIDTH)
    if op == "not":
        return ~env[d[1]]
    if op == "shl":
        return env[d[1]] << z3.BitVecVal(d[2], WIDTH)
    if op == "shr":
        return z3.LShR(env[d[1]], z3.BitVecVal(d[2], WIDTH))
    if op == "mux":
        s = env[d[1]]
        return (env[d[2]] & s) | (env[d[3]] & ~s)
    x, y = env[d[1]], env[d[2]]
    if op == "and":
        return x & y
    if op == "or":
        return x | y
    if op == "xor":
        return x ^ y
    if op == "add":
        return x + y
    if op == "eq":
        return z3.If(x == y, z3.BitVecVal(MASK, WIDTH), z3.BitVecVal(0, WIDTH))
    raise ValueError(op)


def build(net, a_sym):
    env = {net["input"]: a_sym}
    for name in net["order"]:
        env[name] = _z3(net["defs"][name], env)
    return env[net["output"]]

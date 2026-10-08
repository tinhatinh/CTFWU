"""Compare the pure SHA-256 length extension to hashlib without network access."""
from pathlib import Path
import ast
import hashlib
import struct

source = Path(__file__).resolve().parents[1] / 'solve_draw.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
nodes = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('K', 'M') for t in node.targets):
        nodes.append(node)
    if isinstance(node, ast.FunctionDef) and node.name in ('ror', 'compress', 'len_extend'):
        nodes.append(node)
namespace = {'hashlib': hashlib, 'struct': struct}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
count = 0
for secret_len in (0, 1, 13, 15, 31, 64):
    for body_len in (0, 1, 55, 56, 63, 64, 76, 127):
        for suffix_len in (0, 1, 55, 56, 64, 129):
            secret, body, suffix = b'S' * secret_len, b'B' * body_len, b'A' * suffix_len
            extra, forged = namespace['len_extend'](hashlib.sha256(secret + body).digest(), secret_len + body_len, suffix)
            if forged != hashlib.sha256(secret + body + extra).hexdigest():
                raise SystemExit(f'Mismatch: secret={secret_len}, body={body_len}, suffix={suffix_len}')
            count += 1
print(f'PASS: {count} offline length-extension vectors')

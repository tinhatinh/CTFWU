# Severed Symmetry - Crypto (Expert)

**Flag:** `CSSCTF{P35T0_5CH3M3_4TT4CK2026}`
**Attached file:** `source.py` (Size: 10,103 B, SHA256: `b1945c90...`), `out.txt` (Size: 31,778,814 B, SHA256: `5bd759a0...`)

## Problem Description

The system provides an encryption source code `source.py` and a single data file `out.txt`. The `out.txt` file contains the public key structure comprising 34 polynomials along with 3 ciphertext blocks. The private key has been destroyed; thus, the challenge demands recovering the preimage of the ciphertext blocks based entirely on the public data. The flag is embedded directly within the plaintext block, its length strictly constrained by the standard `CSSCTF{...}` format.

## Initial Analysis

The `keygen` generation function architecture constructs a cipher scheme adhering to the VLG model: The random initialization process of two independent affine transformations `A1` (size 34x34) and `A2` (size 32x32), combined with 16 homogeneous quadratic polynomials `q_a` on 16 variables. The system additionally utilizes 18 auxiliary polynomials `U_j` designed according to a vinegar-oil structure (a structural constraint demanding each term contain at least one variable from the first 20 structural variables group). The Central map is defined via two expressions:

```python
w = [z[i] - substitute(qmap[i], z[t:], p) for i in range(t)]
central = w + [substitute(poly, w + z[t:], p) for poly in umap]
```

With configuration `z = A2(x)`. Because the `U_j` function directly accepts the input parameter `w` (where `w` itself is quadratic), the polynomial `U_j(w, v)` has the capability to expand up to a maximum degree of 4. The data extracted from the `out.txt` file confirms this trait: Each exported public polynomial contains 49,320 terms belonging to the degree 4 group, and 5,626 terms belonging to the degree 3 group.

The decoding and attack process relies on three core configuration parameters:
- Parameter `t = 16`: Denotes the existence of exactly 16 degree-preserving analysis directions (degree <= 2) in the public span.
- Parameter `s = 4`: Defines the search space limit, a valid decoding process only requires traversing `17^4 = 83521` cases.
- Equation coefficient `m - t = 18` applied on 12 oil group variables: Ensures absolute statistical uniqueness for each obtained solution.

## Exploitation Chain

**Step 1 - Recover the combinatorial space `W` (Degree <= 2 format).** 
Establish a coefficient matrix for all monomials with degree >= 3 (Dimensions 34 rows, 70,906 columns), apply null space calculation. The system asserts: The degree 4 component of a linear combination is annihilated if and only if the `U` element of that combination is 0. Therefore, the null space perfectly coincides with the `span{w_a}` partition (dimension limit is 16).

```python
vec = {mon: c for mon, c in poly.items() if len(mon) >= 3}   # Preserve only terms with degree >= 3
dep, comb = reduce_track(pivots, vec, comb)                   # Gaussian elimination integrating combinatorial structure tracking mechanism
```

**Step 2 - Interpolate the structural frame `(u, v)`.** 
Each element belonging to array `W_a` is decomposed into the expression `const_a + u_a - q_a(v)`. Here, the linear part (first degree) represents 16 linear transformations `u`, and the quadratic part provides 16 mathematical forms `q_a(v)`. Proceed to test random combinations of the `q_a` set until a 32x32 matrix with a rank equal to 16 is formed. The kernel of this matrix precisely identifies the set `{x : v(x) = 0}`. From there, the annihilator of the kernel will furnish the spanning space of the variable `v`.

```text
step2  Quadric matrix rank reaches 16 after only 1 attempt; ker dimension (dim) = 16
step2  Validate frame: t=16 v dimension (dim(v))=16
```

**Step 3 - Degree reduction of equations independent of `A1`.** 
The polynomial `W_a` is an explicit representation with respect to variable `x`. Mathematical properties dictate: The value of the polynomial on the preimage must be identical to the value of that combination calculated on the ciphertext block. Equivalent expression: `t_a = (comb_a . c) - const_a`. When substituting `u_a = t_a + q_a(v)` back into the original system of equations, all degree 3 and degree 4 terms will be annihilated (Inherently the vanishing process of `U_j(t, v)`). The reduced equation system maintains at degree 2 with 16 unknowns `v`. The technical solution applies a function interpolation mechanism (instead of traditional polynomial interpolation): Utilizing 153 evaluation points (`0`, `e_i`, `2e_i`, `e_i+e_j`), providing sufficient basis to reconstruct all 153 coefficients of the quadratic equation.

**Step 4 - Mine the Oil space.** 
Identify `E_g` as the quadratic block matrix (dependent on variable `v`) constituted from the 18 obtained equations. According to the theoretical structure: With `o` belonging to the oil space partition `O`, the product `E_g o` must fall into a vinegar space with a dimension equal to 4. Conversely, if `v` does not belong to `O`, the vectors `E_g v` will generate a structure spanning 12 or more dimensions. Inductive formula: `O = {v : dim span{E_g v} <= 4}`. The system will proceed to randomly test `17^4` evaluation samples (the sample probability hitting exactly on `O` is `17^-4`) to isolate and cluster the image space `Vtil`. Finally, the expression `O = {v : E_g v in Vtil}` will be simplified into a standard linear equation system.

```text
step4  Quadric family partition reaches dimension 18, max rank 8 => parameter s=4, O dimension (dim(O))=12
step4  Oil space successfully recovered (tested 0, 2 evaluation samples matched)
```

**Step 5 - Scan the Vinegar partition via valid simulation mechanism.** 
On each data block, proceed to fix the `t*` cluster and apply a brute-force method over all `17^4` vinegar values. Each value generates an 18x12 linear equation system corresponding to the 12 oil variables. The equation system is solved using Gaussian elimination vectorized on data batches of 4096 parameters per batch.

**Verification stage.** 
Each obtained candidate set will have to undergo an independent check step by re-evaluating the 34 public polynomials with respect to variable `x` and reverse cross-referencing with the corresponding data block. The evidence data shows each block yields only 1 candidate meeting the standard. The combination of 3 consecutive data blocks must assemble into a consistent frame structure: The 8 leading digits are decoded to determine the length `L`. Parameter constraint requires `2(4+L) <= 96`, and concurrently all values following index position `2(4+L)` must be absolute 0.

## Flag

Executing the system script:

```bash
python exploit.py files/out.txt
```

```text
step1  dim(W) = 16 = t
step2  quadric rank 16 after 1 attempt; dim ker = 16
step2  frame: t=16 dim(v)=16
step3  18 auxiliary polynomials, 153 interpolation points
step4  quadric family dim 18, max rank 8 => s=4, dim(O)=12
step4  oil space recovered (tested 0, 2 samples matched)
step5  83521 vinegar -> 1 linear solution
step5  1 solution satisfies all public polynomials
step5  83521 vinegar -> 1 linear solution
step5  1 solution satisfies all public polynomials
step5  83521 vinegar -> 1 linear solution
step5  1 solution satisfies all public polynomials
FLAG: CSSCTF{P35T0_5CH3M3_4TT4CK2026}
(33.9 s)
```

To ensure solution consistency, the entire exploitation algorithm was cross-verified by running tests on two instances generated from the original `source.py` source code: Environment one established with small configuration parameters (`p=17, n=9, m=11, t=3, s=2`, producing 7 data blocks); environment two synced with the exact configuration required by the challenge (`n=32, m=34`, 3 data blocks and a known mock/bait flag). Both independent tests accurately recovered the original plaintext block. A supplementary test by re-encrypting the plaintext text with the public key extracted from `out.txt` also successfully outputted 3 ciphertext blocks equivalent to the provided challenge file.

## Reproduce

Automated re-establishment process using script:

```bash
python exploit.py files/out.txt
```

Note: The environment mandatorily requires the `numpy` library. The execution runtime is approximately 35 seconds. The `analysis/` directory includes two auxiliary scripts `quartic.py` and `vinegar.py`; these are scripts responsible for the scanning operations in the preprocessing stage (surveying the degree 4 space and the linear function space of the variable `W`).

"""Robustly fit the two cobblestone-lattice vanishing points."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# --- joint enhancement -------------------------------------------------------
bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh, (5, 5), 0)
edges = cv2.Canny(bh, 30, 90)

# --- mask: keep only the sett paving, drop slab band / bird / shadow ---------
yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False           # ribbed slab band, top right
keep[:60, :] = False
cv2.rectangle(keep, (820, 1330), (2600, 3020), False, -1)              # bird + its shadow
edges[~keep] = 0

seg = cv2.HoughLinesP(edges, 1, np.pi / 900, threshold=110, minLineLength=300, maxLineGap=12)
seg = np.asarray(seg).reshape(-1, 4).astype(np.float64)
d = seg[:, 2:4] - seg[:, 0:2]
ang = np.arctan2(d[:, 1], d[:, 0])
L = np.hypot(d[:, 0], d[:, 1])
print("segments:", len(seg), " total length:", int(L.sum()))

# line in normal form n.x = c
nrm = np.stack([np.sin(ang), -np.cos(ang)], 1)      # unit normal
c = np.einsum("ij,ij->i", nrm, seg[:, 0:2])


def fit_vp(idx, w):
    """Least-squares point minimising weighted squared distance to the lines."""
    A = (w[:, None, None] * (nrm[idx][:, :, None] * nrm[idx][:, None, :])).sum(0)
    b = (w[:, None] * (nrm[idx] * c[idx][:, None])).sum(0)
    return np.linalg.solve(A, b)


# --- initialise two families by orientation, then alternate assign / refit ---
a_deg = (np.degrees(ang) + 180) % 180
fam = ((a_deg > 90) & (a_deg < 150)).astype(int)     # the cross-row family
for it in range(12):
    vps = []
    for f in (0, 1):
        idx = np.where(fam == f)[0]
        w = L[idx]
        v = fit_vp(idx, w)
        # robust: drop lines whose residual is > 3 px at their own leverage
        for _ in range(4):
            r = np.abs(nrm[idx] @ v - c[idx])
            good = r < max(6.0, np.percentile(r, 85))
            idx, w = idx[good], L[idx][good]
            v = fit_vp(idx, w)
        vps.append(v)
    # reassign every segment to the nearer VP (by the direction it subtends)
    p = (seg[:, 0:2] + seg[:, 2:4]) / 2
    dirs = np.stack([(v - p) for v in vps])                  # 2 x N x 2
    nd = dirs / np.linalg.norm(dirs, axis=2, keepdims=True)
    ua = np.stack([np.cos(ang), np.sin(ang)], 1)
    score = [None, None]
    for i in range(2):
        cx = dirs[i][..., 0] * ua[..., 1] - dirs[i][..., 1] * ua[..., 0]
        score[i] = np.abs(cx / np.linalg.norm(dirs[i], axis=1))
    new = (np.stack(score).argmin(0)).astype(int)
    if (new == fam).all():
        fam = new
        break
    fam = new

for f in (0, 1):
    idx = np.where(fam == f)[0]
    print(f"family {f}: {len(idx)} segs, len={L[idx].sum():.0f}, VP=({vps[f][0]:10.1f}, {vps[f][1]:10.1f})")
    r = np.abs(nrm[idx] @ vps[f] - c[idx])
    print(f"          residual px: median={np.median(r):.2f} p90={np.percentile(r,90):.2f}")

np.save("vps.npy", np.array(vps))
np.save("fam.npy", fam)

vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
for s, f in zip(seg, fam):
    cv2.line(vis, tuple(s[:2].astype(int)), tuple(s[2:].astype(int)), (255, 60, 60) if f else (60, 60, 255), 3)
cv2.imwrite("vp_families.png", cv2.resize(vis, (750, 1000)))

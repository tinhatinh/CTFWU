/* collide.c - AlphaSOUP-32 preimage finder for soupOS stage 2.
 *
 * users_check() compares HASHES, so any string that hashes to the stored
 * headchef value logs in. AlphaSOUP-32 is a bijection per byte (xor, rotl,
 * odd multiply, xor-shift are all invertible), so instead of the author's
 * 36^7 exhaustive scan we split the 7-char string 3 + 4 and meet in the
 * middle: ~4.7e4 forward states vs ~1.7e6 backward states.
 *
 *   gcc -O2 -o collide.exe collide.c ../soupos/src/alphasoup.c
 *   ./collide.exe -selftest
 *   ./collide.exe <8 hex digits from /etc/kitchen>
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

uint32_t alphasoup_hash(const void *data, uint32_t len);   /* the real kernel hash */

#define SOUPSEED 0xB07B0C2Du
#define NOODLE   0x9E3779B9u
#define FIN_A    0x85EBCA6Bu
#define FIN_B    0xC2B2AE35u

static const char ALPHA[] = "abcdefghijklmnopqrstuvwxyz0123456789";
#define NA ((int)(sizeof(ALPHA) - 1))

static uint32_t rotl(uint32_t x, int n) { return (x << n) | (x >> (32 - n)); }
static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

/* x = z ^ (x >> s), solved by iteration; 4 rounds cover 32 bits for any s>=8 */
static uint32_t unxorshift_r(uint32_t z, int s) {
    uint32_t x = z;
    for (int i = 0; i < 4; i++) x = z ^ (x >> s);
    return x;
}

static uint32_t modinv32(uint32_t c) {           /* c must be odd */
    uint32_t x = c;
    for (int i = 0; i < 5; i++) x *= (2u - c * x);
    return x;
}

static uint32_t I_NOODLE, I_FINA, I_FINB;

/* one forward byte step */
static uint32_t step(uint32_t h, uint8_t b) {
    uint32_t x = rotl(h ^ b, 13);
    uint32_t y = x * NOODLE;
    return y ^ (y >> 17);
}

/* its exact inverse: given the state AFTER the byte, return the state BEFORE */
static uint32_t unstep(uint32_t out, uint8_t b) {
    uint32_t y = unxorshift_r(out, 17);
    uint32_t x = y * I_NOODLE;
    return rotr(x, 13) ^ b;
}

static uint32_t finalize(uint32_t h) {
    h ^= h >> 16; h *= FIN_A;
    h ^= h >> 13; h *= FIN_B;
    h ^= h >> 16;
    return h;
}

static uint32_t unfinalize(uint32_t v) {
    uint32_t t = unxorshift_r(v, 16);
    t *= modinv32(FIN_B);
    t = unxorshift_r(t, 13);
    t *= modinv32(FIN_A);
    t = unxorshift_r(t, 16);
    return t;
}

#define L        7          /* preimage length */
#define FLEN     3          /* forward half */
#define BLEN     (L - FLEN) /* backward half */
#define FSPACE   (NA * NA * NA)
#define TBITS    18
#define TSIZE    (1 << TBITS)
#define TMASK    (TSIZE - 1)

static uint32_t t_key[TSIZE];
static int32_t  t_val[TSIZE];   /* forward index + 1; 0 = empty */

static void table_insert(uint32_t key, int32_t val) {
    uint32_t i = (key * 2654435761u) & TMASK;
    while (t_val[i]) { if (t_key[i] == key) return; i = (i + 1) & TMASK; }
    t_key[i] = key; t_val[i] = val;
}

static int32_t table_get(uint32_t key) {
    uint32_t i = (key * 2654435761u) & TMASK;
    while (t_val[i]) { if (t_key[i] == key) return t_val[i]; i = (i + 1) & TMASK; }
    return 0;
}

/* Build the forward half once: all NA^3 prefixes, state after FLEN bytes. */
static void build_table(uint32_t h0) {
    memset(t_val, 0, sizeof(t_val));
    for (int a = 0; a < NA; a++) {
        uint32_t ha = step(h0, (uint8_t)ALPHA[a]);
        for (int b = 0; b < NA; b++) {
            uint32_t hb = step(ha, (uint8_t)ALPHA[b]);
            for (int c = 0; c < NA; c++) {
                uint32_t hc = step(hb, (uint8_t)ALPHA[c]);
                int32_t idx = (a * NA + b) * NA + c;
                table_insert(hc, idx + 1);
            }
        }
    }
}

/* Returns 1 and writes the typeable preimage into out[L]; 0 on no hit. */
static int find_preimage(uint32_t target, char *out) {
    uint32_t h0 = SOUPSEED ^ (L * NOODLE);
    uint32_t hL = unfinalize(target);
    build_table(h0);

    for (int i7 = 0; i7 < NA; i7++) {
        uint32_t h6 = unstep(hL, (uint8_t)ALPHA[i7]);
        for (int i6 = 0; i6 < NA; i6++) {
            uint32_t h5 = unstep(h6, (uint8_t)ALPHA[i6]);
            for (int i5 = 0; i5 < NA; i5++) {
                uint32_t h4 = unstep(h5, (uint8_t)ALPHA[i5]);
                for (int i4 = 0; i4 < NA; i4++) {
                    uint32_t h3 = unstep(h4, (uint8_t)ALPHA[i4]);
                    int32_t v = table_get(h3);
                    if (!v) continue;
                    int32_t f = v - 1;
                    int a = f / (NA * NA), b = (f / NA) % NA, c = f % NA;
                    out[0] = ALPHA[a]; out[1] = ALPHA[b]; out[2] = ALPHA[c];
                    out[3] = ALPHA[i4]; out[4] = ALPHA[i5];
                    out[5] = ALPHA[i6]; out[6] = ALPHA[i7];
                    out[L] = '\0';
                    if (alphasoup_hash(out, L) == target) return 1;
                }
            }
        }
    }
    return 0;
}

static void rnd_seed(void) { srand(0xC0FFEEu); }

static int selftest(void) {
    int fails = 0;

    /* 1. unstep must undo step, on random (state, byte) pairs */
    for (int i = 0; i < 200000; i++) {
        uint32_t h = ((uint32_t)rand() << 16) ^ (uint32_t)rand();
        uint8_t b = (uint8_t)(rand() & 0xFF);
        if (unstep(step(h, b), b) != h) { printf("FAIL unstep h=%08x b=%02x\n", h, b); fails++; break; }
    }
    printf("[1] unstep inverts step on 2e5 random pairs ... %s\n", fails ? "FAIL" : "ok");

    /* 2. unfinalize must undo the real final avalanche */
    int f2 = 0;
    for (int i = 0; i < 200000; i++) {
        uint32_t h = ((uint32_t)rand() << 16) ^ (uint32_t)rand();
        if (unfinalize(finalize(h)) != h) { f2 = 1; break; }
    }
    printf("[2] unfinalize inverts finalize on 2e5 states .... %s\n", f2 ? "FAIL" : "ok");
    fails += f2;

    /* 3. the harness forward path must equal the kernel's own hash */
    int f3 = 0;
    for (int i = 0; i < 2000; i++) {
        char s[8]; uint32_t h = SOUPSEED ^ (L * NOODLE);
        for (int k = 0; k < L; k++) { s[k] = ALPHA[rand() % NA]; h = step(h, (uint8_t)s[k]); }
        s[L] = 0;
        if (finalize(h) != alphasoup_hash(s, L)) { f3 = 1; break; }
    }
    printf("[3] my step/finalize == kernel alphasoup_hash ... %s\n", f3 ? "FAIL" : "ok");
    fails += f3;

    /* 4. the real attack: random targets, every hit must verify against the
     *    kernel hash. Returning the original string is allowed too - any
     *    preimage logs you in - but it should be rare, so report it. */
    int f4 = 0, hits = 0, same = 0;
    for (int i = 0; i < 12; i++) {
        char orig[L + 1], got[L + 1];
        for (int k = 0; k < L; k++) orig[k] = ALPHA[rand() % NA];
        orig[L] = 0;
        uint32_t t = alphasoup_hash(orig, L);
        if (find_preimage(t, got)) {
            if (alphasoup_hash(got, L) != t) { printf("FAIL preimage does not verify\n"); f4 = 1; }
            hits++;
            if (!strcmp(got, orig)) same++;
            printf("    target %08x (%s) -> preimage %s%s\n", t, orig, got,
                   !strcmp(got, orig) ? "  (same as original)" : "");
        } else { printf("FAIL no preimage for %08x (%s)\n", t, orig); f4 = 1; }
    }
    printf("[4] 12 live targets verified preimages ............ %s (%d/12, %d coincided)\n",
           (f4 || hits != 12) ? "FAIL" : "ok", hits, same);
    fails += f4 + (hits != 12);

    printf("\n%s\n", fails ? "SELFTEST FAILED" : "SELFTEST PASSED - tool is trustworthy");
    return fails ? 1 : 0;
}

int main(int argc, char **argv) {
    I_NOODLE = modinv32(NOODLE);
    I_FINA   = modinv32(FIN_A);
    I_FINB   = modinv32(FIN_B);
    rnd_seed();

    if (argc >= 2 && !strcmp(argv[1], "-selftest")) return selftest();

    /* -p  <string> : print its kernel hash (to sanity-check a roster line) */
    if (argc >= 3 && !strcmp(argv[1], "-p")) {
        printf("%s -> %08x\n", argv[2], alphasoup_hash(argv[2], (uint32_t)strlen(argv[2])));
        return 0;
    }

    if (argc < 2) {
        printf("usage: %s <8 hex digits>   |   -selftest   |   -p <string>\n", argv[0]);
        return 2;
    }
    uint32_t target = (uint32_t)strtoul(argv[1], NULL, 16);
    char got[L + 1];
    if (!find_preimage(target, got)) { printf("no collision found for %08x\n", target); return 1; }
    printf("target      : 0x%08x\n", target);
    printf("preimage    : %s\n", got);
    printf("verify      : alphasoup(\"%s\") = %08x\n", got, alphasoup_hash(got, L));
    return 0;
}

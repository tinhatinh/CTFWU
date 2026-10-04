/* Stage-2 gate test: drive the REAL users.c so the verdict comes from the
 * kernel's own users_check(), not from my re-implementation. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int  fat_read (const char *path, uint8_t *buf, uint32_t bufsize, uint32_t *out_size);
int  fat_write(const char *path, const uint8_t *buf, uint32_t size);
int  fat_mkdir(const char *path);

void users_init(void);
int  users_check(const char *name, const char *secret);
int  users_count(void);
const char *users_name_at(int i);
uint8_t users_uid_at(int i);
uint32_t alphasoup_hash(const void *d, uint32_t len);
int  fsK_add(const char *name, const char *content);
void fsK_dump(void);

static void show_roster(void) {
    for (int i = 0; i < users_count(); i++)
        printf("    loaded uid %u = %s\n", users_uid_at(i), users_name_at(i));
}

int main(int argc, char **argv) {
    int fails = 0;

    /* ---- A. fresh volume: no /etc/kitchen -> kernel seeds it ---- */
    printf("A) boot with no /etc/kitchen (kernel seeds the roster)\n");
    users_init();
    show_roster();
    fsK_dump();

    /* The cook account the card hands us. */
    if (users_check("cook", "soup") != 1) { printf("  FAIL: cook/soup rejected\n"); fails++; }
    else printf("  ok  cook/soup -> uid 1  (positive control)\n");
    if (users_check("headchef", "soup") >= 0) { printf("  FAIL: headchef accepted the cook secret\n"); fails++; }
    else printf("  ok  headchef/soup -> denied (negative control)\n");

    /* ---- B. arbitrary hash on disk, collision from the MITM tool ----
     * argv[1] is either the plaintext secret (its hash is written to disk)
     * or "0xHEX" to plant a hash directly, e.g. the live f63a9eb7. */
    uint32_t h;
    const char *secret = argc > 1 ? argv[1] : "correcthorse";
    if (!strncmp(secret, "0x", 2)) {
        h = (uint32_t)strtoul(secret, NULL, 16);
    } else {
        h = alphasoup_hash(secret, (uint32_t)strlen(secret));
    }
    char line[64];
    sprintf(line, "headchef:0:%08x\ncook:1:e7d471fc\n", h);
    fsK_add("kitchen", line);
    users_init();
    printf("B) reloaded roster with headchef hash %08x (disk secret unknown to us = %s)\n",
           h, secret);
    show_roster();

    if (argc > 2) {
        const char *coll = argv[2];
        int uid = users_check("headchef", coll);
        printf("  users_check(\"headchef\", \"%s\") -> %d\n", coll, uid);
        if (uid != 0) { printf("  FAIL: collision not accepted\n"); fails++; }
        else          { printf("  ok  COLLISION ACCEPTED AS uid 0 (headchef)\n"); }
        if (users_check("headchef", "definitely-wrong") >= 0) { printf("  FAIL: wrong secret accepted\n"); fails++; }
        else printf("  ok  wrong secret still denied\n");
    }

    printf("\n%s\n", fails ? "GATE TEST FAILED" : "GATE TEST PASSED");
    return fails ? 1 : 0;
}

/* --- minimal volume stub (fat_read contract: 0 = ok, -1 = missing) --- */
#define N 4
static struct { char name[16]; char data[512]; int used; } vol[N];

int fsK_add(const char *name, const char *content) {
    for (int i = 0; i < N; i++)
        if (!vol[i].used || !strcmp(vol[i].name, name)) {
            strncpy(vol[i].name, name, 15); vol[i].name[15] = 0;
            strncpy(vol[i].data, content, 511); vol[i].data[511] = 0;
            vol[i].used = 1; return i;
        }
    return -1;
}
void fsK_dump(void) {
    for (int i = 0; i < N; i++)
        if (vol[i].used) printf("    on-disk %s: %s", vol[i].name, vol[i].data);
}
static const char *leaf(const char *p) {
    const char *s = 0;
    for (const char *q = p; *q; q++) if (*q == '/') s = q;
    return s ? s + 1 : p;
}
int fat_read(const char *path, uint8_t *buf, uint32_t bufsize, uint32_t *out_size) {
    const char *l = leaf(path);
    for (int i = 0; i < N; i++)
        if (vol[i].used && !strcmp(vol[i].name, l)) {
            uint32_t n = (uint32_t)strlen(vol[i].data);
            if (n > bufsize) n = bufsize;
            memcpy(buf, vol[i].data, n);
            if (out_size) *out_size = n;
            return 0;
        }
    return -1;
}
int fat_write(const char *path, const uint8_t *buf, uint32_t size) {
    char nm[16];
    strncpy(nm, leaf(path), 15); nm[15] = 0;
    for (int i = 0; i < N; i++)
        if (!vol[i].used || !strcmp(vol[i].name, nm)) {
            strncpy(vol[i].name, nm, 15);
            memcpy(vol[i].data, buf, size < 511 ? size : 511);
            vol[i].data[size < 511 ? size : 511] = 0;
            vol[i].used = 1; return 0;
        }
    return -1;
}
int fat_mkdir(const char *path) { (void)path; return 0; }

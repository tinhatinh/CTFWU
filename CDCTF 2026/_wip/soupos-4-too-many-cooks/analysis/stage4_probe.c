/* Stage-4 proof: link the REAL soupyc.c + challenge.c and drive the negative
 * index write so sc_state.after_hook is hit. Controls prove the offset is
 * exact and that the hook really is what runs. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "fat.h"
#include "users.h"
#include "klog.h"
#include "soupyc.h"

int  fs_add(const char *name, const char *content);

/* ---- FAT/users/klog shims challenge.c calls ---- */
int fat_read(const char *path, uint8_t *buf, uint32_t bufsize, uint32_t *out_size) {
    (void)path; (void)buf; (void)bufsize;
    if (out_size) *out_size = 0;
    return -1;                      /* no FLAG1.TXT on this volume */
}
int fat_exists(const char *p) { (void)p; return 0; }
int fat_mkdir(const char *p)  { (void)p; return 0; }
int fat_chmod(const char *p, uint8_t m) { (void)p; (void)m; return 0; }
int fat_chown(const char *p, uint8_t o) { (void)p; (void)o; return 0; }
int users_is_headchef(void)   { return 0; }
void klog(const char *fmt, ...) { (void)fmt; }

/* ---- decoy: proves a value written at the hook offset is actually called ---- */
void decoy(void) { printf("DECOY-CALLED\n"); }

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("usage: %s <script>   (use %s for the decoy address)\n", argv[0], argv[0]);
        printf("decoy addr = %u\n", (unsigned)(uintptr_t)&decoy);
        return 2;
    }
    printf("decoy addr = %u\n", (unsigned)(uintptr_t)&decoy);
    soupyc_run(argv[1]);
    printf("--- soupyc_run returned ---\n");
    return 0;
}

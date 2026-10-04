#include <stdint.h>
#include <stdio.h>
/* message_encoder.c with the deleted string restored from the decode,
 * widened to the 64 bytes the loop actually reads (61 chars + NUL + "%l"
 * of the adjacent "%lu " format string). */
int main() {
	char message[64] = "Meet me at the Tom Bevill Building at noon next week Thursday\0%l";
	uint64_t nums[8] = {0};
	for (int j=0; j<8; j++) {
		for (int i=0; i<8; i++) {
			nums[j] += (unsigned char)message[i + 8 * j];
			if (i != 7) {
				nums[j] = nums[j] << 8;
			}
		}
	}
	for (int j=0; j<8; j++)
		printf("%llu ", (unsigned long long)nums[j]);
	printf("\n");
	return 0;
}

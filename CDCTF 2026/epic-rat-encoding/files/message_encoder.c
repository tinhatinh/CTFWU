#include <stdint.h>
#include <stdio.h>
int main() {
	char* message = ""; // I think that Ratón deleted this part.
	uint64_t nums[8];
	for (int j=0; j<8; j++) {
		for (int i=0; i<8; i++) {
			nums[j] += message[i + 8 * j];
			if (i != 7) {
				nums[j] = nums[j] << 8;
			}
		}
	}
	for (int j=0; j<8; j++)
		printf("%lu ", nums[j]);
	printf("\n");
	return 0;
}

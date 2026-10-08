# Eat your fruits and vegetables! - Crypto (500 points)

**Flag:** `cdctf{Carrot}` · **Files:** `data.db.enc`, 960000 bytes, sha256 `ea8bfa7cfc6f9f319ccf4f5efa12377beb84087ffb5885bd975656cc628e0374`

## Challenge

A stolen database encrypted with AES-128 in ECB mode is provided as `data.db.enc`. Once decrypted, each person occupies exactly 32 bytes: 8 bytes for the name, 8 for the car brand, 8 for the favourite produce item, 8 for the favourite operating system, all null padded. The statement gives the distribution of every field and states that everyone named Bob likes the same produce item. The task is to recover that item; the flag is `cdctf{Produce_Item}` and only two submissions are allowed.

No key and no decryption oracle are available, so every bit of information has to come out of the ciphertext itself.

## Analysis

The file is 960000 bytes, divisible by both 16 and 32. The statement specifies AES-ECB. The analysis uses repeated blocks and their frequencies, rather than inferring the mode from entropy.

Splitting the file into 16-byte blocks and counting distinct values:

```python
>>> d = open('files/data.db.enc', 'rb').read()
>>> len(set(d[i:i+16] for i in range(0, len(d), 16)))
54
```

Only 54 different values across 60000 ciphertext blocks. ECB maps each plaintext block to ciphertext independently, so equal blocks stay equal and the whole value space of the fields leaks without decrypting anything. 54 = 36 + 18, exactly `12 names x 3 car brands` for the first half of a record plus `6 produce items x 3 operating systems` for the second half, which confirms the 32-byte record split.

Call `A` the "name + car" block and `B` the "produce + OS" block. The problem reduces to finding the three `A` blocks that belong to Bob and then reading the `B` blocks next to them.

## Approaches tried

Before settling on the solution, the following channels were tested and discarded (full log in `notes.md`):

1. **Attacking AES itself to recover the key**: ciphertext-only, no oracle, and the security of the primitive is not the weakness being exploited. Discarded.
2. **Picking Bob's `A` block by frequency**: the 36 `A` blocks occur between 786 and 872 times, tightly around the expected 30000/36 = 833, so no block stands out. Discarded.
3. **Using the "Bob - 5%" figure from the statement**: the constrained group actually holds exactly 2500 rows, that is 1/12, not 5%. The observed name frequencies disagree with the statement; the produce table matches the data. Discarded.
4. **Comparing the first 8 bytes of `B` blocks against each other**: ECB encrypts the full 16-byte block, so two plaintexts differing only in the second half still produce completely different ciphertext. The three `B` blocks of one produce item share no byte. Discarded.

## Solution

**Step 1 - Count blocks by position within the record.** For each 32-byte record take `A = record[0:16]` and `B = record[16:32]`, and build two frequency tables plus a frequency table of the `(A, B)` pairs. Result: 36 distinct `A` blocks and 18 distinct `B` blocks.

**Step 2 - Group `A` blocks by the set of `B` blocks that immediately follow them.** For an unconstrained name, produce is independent of name and car, so every `A` block of that name must appear alongside all 18 `B` blocks. 33 of the 36 `A` blocks collapse into one such group. The remaining group is Bob's: three `A` blocks (three car brands) appear only with three `B` blocks, and those three cover exactly 2500 rows.

```python
from collections import Counter, defaultdict
d = open('files/data.db.enc', 'rb').read()
B, follow = Counter(), defaultdict(Counter)
for i in range(0, len(d), 32):
    a, b = d[i:i+16], d[i+16:i+32]
    B[b] += 1; follow[a][b] += 1

groups = defaultdict(list)
for a in follow:
    groups[frozenset(follow[a])].append(a)

for bset, alist in groups.items():
    if len(bset) < len(B):                     # a proper subset of the B blocks
        rows = sum(sum(follow[a][b] for b in bset) for a in alist)
        print(len(alist), len(bset), rows)
```

```
3 3 2500
```

3 `A` blocks x 3 `B` blocks x 2500 rows is a unique structure in the whole dataset: one name with a fixed produce item, still split evenly across three car brands and three operating systems.

**Step 3 - Read the produce item off the global frequency.** Inside Bob's group the three `B` blocks are nearly equal (885/805/810 rows) and carry no distinguishing signal; the signal is how much of the full 30000 rows those three blocks account for. Since they are the same produce item under three different operating systems, their combined frequency over the whole database is exactly that produce item's share:

```
1852 + 1780 + 1768 = 5400 rows = 18.00% of 30000
```

Against the table in the statement: Apple 10% = 3000, Orange 12% = 3600, Banana 15% = 4500, Carrot 18% = 5400, Onion 21% = 6300, Potato 24% = 7200. The 18% value maps to Carrot and to nothing else.

**Step 4 - Verification.** Sort the 18 `B` blocks by descending frequency and split them into clusters by gap:

```
      3 block, tong 7200 dong = 24.00% -> Potato
      3 block, tong 6300 dong = 21.00% -> Onion
      3 block, tong 5400 dong = 18.00% -> Carrot
      3 block, tong 4500 dong = 15.00% -> Banana
      3 block, tong 3600 dong = 12.00% -> Orange
      3 block, tong 3000 dong = 10.00% -> Apple
```

The 18 blocks separate into exactly six clusters of three, and the cluster totals match the statement's distribution row for row, including the 33.33% split of operating systems inside each cluster. Bob's three blocks sit together inside the 18% cluster, consistent with the constraint that Bob likes one produce item.

## Result

```bash
python exploit.py files/data.db.enc
```

```
[*] data.db.enc: 960000 bytes = 30000 record 32 byte
[*] block loai A (ten+xe) phan biet: 36 (ky vong 36)
[*] block loai B (hoa qua+OS) phan biet: 18 (ky vong 18)
[*] gom B-block theo khoang cach tan suat:
      3 block, tong 7200 dong = 24.00% -> Potato
      3 block, tong 6300 dong = 21.00% -> Onion
      3 block, tong 5400 dong = 18.00% -> Carrot
      3 block, tong 4500 dong = 15.00% -> Banana
      3 block, tong 3600 dong = 12.00% -> Orange
      3 block, tong 3000 dong = 10.00% -> Apple
[*] nhom A-block co tap B hong bo: 1
      3 A-block (= 3 xe cua cung mot ten), 3 B-block, 2500 dong
      483a10eb3d9fb3e96542da3c5348b7ae  tong 1852  trong nhom 885
      7ad7bda141552326c6ac06ac5ef29b0c  tong 1780  trong nhom 805
      30cbb1d20626d60fae57c430ec450bbf  tong 1768  trong nhom 810
[+] 3 B-block cua nhom nay chiem 5400/30000 dong = 18.00% -> Carrot
[+] flag: cdctf{Carrot}
```

## Reproduce

```bash
python exploit.py files/data.db.enc
# Expected output: [+] flag: cdctf{Carrot}, exit code 0, flag.txt written
```

The script uses only the standard library and checks the file length, the number of distinct blocks, the 3x3 size of the constrained group and the fit of all six frequency clusters; if any check fails it exits with an error instead of printing a flag.

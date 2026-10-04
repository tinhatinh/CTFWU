# Gerry the Larry (1/2) - Log Analysis (500 points)

**Flag:** `cdctf{12}`
**Attached file:** `catcounty_results.zip` (37,241 B, SHA256 `462c4d84…5a9cb4`), containing `gerry_final_files/{info.csv, check_in.log, votes.log}`
**Authors:** adlee7, reep236 (CDCTF)

## Problem Description

Three leaked election logs from Cat County. `info.csv` lists 1067 voters with their `id`, name and
the county block they live in. `check_in.log` records 1067 check-ins at the polling places.
`votes.log` records 1067 ballots cast for one of four parties. The question: how many blocks does
the Meowjority currently control, and which ones (the list is needed for part 2). The flag carries
only the count, in the form `cdctf{##}`.

## Initial Analysis

The three files look like this (first and last record of each):

```text
info.csv      31752947660,Luna,Midnight Zoomies Mile
              1067 data rows, 36 distinct block values
check_in.log  2026-10-01 07:45:27 550408395 11835863810
              2026-10-01 17:46:32 550409461 47281930635
votes.log     2026-10-01 08:00:45:381009204091:Nap Rights
              2026-10-01 17:59:50:381009205157:Meowjority
```

The 11-digit `voter_id` in `check_in.log` matches `info.csv` completely (1067/1067 ids, none extra,
none repeated), so every check-in can be traced to a block. The difficulty is `votes.log`: a ballot
carries only a sequence number and a party name. Receipts in `check_in.log` form the 9-digit range
550408395..550409461 while ballots in `votes.log` form the 12-digit range 381009204091..381009205157.
The two sets do not intersect, so the logs share no key.

The opening is structural: both logs are monotonic in time, their sequence numbers increase by
exactly 1 per line, and both hold exactly 1067 lines. A polling queue is first in, first out, so the
only order-preserving bijection between the two files pairs line i with line i. Re-checking that
against the timestamps, each ballot lands 560..1184 s (mean 869 s) after its check-in, and no pair is
reversed.

## Approaches Ruled Out

1. **Joining the two logs on their sequence numbers**: `set(receipt) & set(ballot)` is empty, the two
   ranges are independent numbering spaces. Rejected.
2. **Shifting the pairing by one line** (ballot i belongs to check-in i-1 or i+1): both shifts match
   only 1066 pairs, leaving one check-in and one ballot without a counterpart, which contradicts the
   data (every voter checks in exactly once, both files have 1067 lines). They also give different
   answers, 10 and 9 blocks (`analysis/sensitivity.py`), so this alignment had to be settled before
   trusting 12. Rejected.
3. **Absolute-majority rule** (a party must exceed 50% of the block to hold it): gives 9 blocks, three
   fewer than plurality, dropping Scratching Post Street 11/32, Tuna Terrace 11/25 and Windowsill Way
   6/20. The statement does not define the counting rule, but no block is tied and "most votes takes
   the block" is the rule that is consistent across all 36 blocks, so plurality was kept.

## Exploitation Chain

**Step 1 - Recover the ballot-to-voter relation.** The logs share no key, so monotonicity plus equal
length determines the pairing. The check prints the time gap for every candidate shift:

```text
[*] check_in : n=1067  don dieu thoi gian=True  so thu tu lien tiep=True  (550408395..550409461)
[*] votes    : n=1067  don dieu thoi gian=True  so thu tu lien tiep=True  (381009204091..381009205157)
[*] cua so mo cua: check_in 07:45:27..17:46:32, votes 08:00:45..17:59:50

[*] do lech (vote[i] - check_in[i+lag]) theo tung cach phoi:
     lag cap hop le    min    mean    max   am
      -2       1065    628   937.0   1252    0
      -1       1066    599   903.2   1216    0
      +0       1067    560   869.4   1184    0
      +1       1066    522   835.6   1160    0
      +2       1065    491   801.9   1128    0
```

Only lag 0 is usable because it is the only shift covering all 1067 lines of both files; lag ±1 drops
one entry at each end, lag ±2 drops two.

**Step 2 - Tally per block and decide each block.** Route each ballot to its block through `voter_id`,
then the party with the most votes in a block holds it:

```python
tally = collections.defaultdict(collections.Counter)
for (_, _, voter), (_, _, party) in zip(checkin, votes):
    tally[voter_block[voter]][party] += 1

meow = [b for b in sorted(tally) if tally[b]["Meowjority"] == max(tally[b].values())]
```

```text
    Cardboard Court          n= 34  Meowjority:21  Tuna Reform:6  Nap Rights:4  Domestic Loafs:3  <== Meowjority
    Catnip Corner            n= 23  Meowjority:12  Domestic Loafs:5  Nap Rights:3  Tuna Reform:3  <== Meowjority
    Hairball Heights         n= 34  Meowjority:21  Tuna Reform:6  Nap Rights:4  Domestic Loafs:3  <== Meowjority
    Mousetrap Alley          n= 23  Meowjority:14  Tuna Reform:5  Nap Rights:4  <== Meowjority
    Pawprint Plaza           n= 31  Meowjority:16  Tuna Reform:9  Domestic Loafs:4  Nap Rights:2  <== Meowjority
    Purrington Place         n= 35  Meowjority:19  Tuna Reform:8  Domestic Loafs:6  Nap Rights:2  <== Meowjority
    Scratching Post Street   n= 32  Meowjority:11  Domestic Loafs:9  Tuna Reform:8  Nap Rights:4  <== Meowjority
    Sunbeam Square           n= 24  Meowjority:16  Domestic Loafs:4  Nap Rights:2  Tuna Reform:2  <== Meowjority
    Tuna Terrace             n= 25  Meowjority:11  Nap Rights:5  Tuna Reform:5  Domestic Loafs:4  <== Meowjority
    Whisker Row              n= 25  Meowjority:13  Nap Rights:8  Tuna Reform:3  Domestic Loafs:1  <== Meowjority
    Windowsill Way           n= 20  Meowjority:6  Tuna Reform:5  Nap Rights:5  Domestic Loafs:4  <== Meowjority
    Yarnball Yard            n= 25  Meowjority:14  Tuna Reform:5  Domestic Loafs:5  Nap Rights:1  <== Meowjority

[*] 36 block, so block hoa phieu: 0
[*] Ghe theo plurality : Meowjority 12, Nap Rights 9, Domestic Loafs 9, Tuna Reform 6
[*] Phieu toan hat     : Domestic Loafs 293 (27.5%), Meowjority 286 (26.8%), Tuna Reform 254 (23.8%), Nap Rights 234 (21.9%)
```

**Step 3 - Verification.** Two cross-checks independent of the pairing, run inside `exploit.py`, which
aborts if either one fails:

```text
[*] doi chieu : 1067 cap, delay bo phieu min=560s max=1184s, so cap vote truoc check-in = 0
[*] kiem chung: 36/36 block co so phieu = so cu tri dang ky (tong 1067 = 1067 phieu)
```

Every block receives exactly as many ballots as it has registered voters, so no ballot was routed to
the wrong block and no voter was dropped. The seat distribution also matches the premise of the
challenge: the Meowjority holds 286 of 1067 votes (26.8%) yet keeps 12 of 36 blocks (33.3%), the most
seats of any party despite finishing second in the popular vote, while Domestic Loafs, with the most
votes (293), holds only 9 blocks. Winning margins in the twelve Meowjority blocks run from 1 to 15
votes; Windowsill Way 6-5 and Scratching Post Street 11-9 are the closest and both depend on the
pairing established in Step 1.

The flag is a computed count rather than a string present in the files, so `cdctf{12}` was not
confirmed by a submission; the evidence here is that all 1067 ballots reconcile with 1067 check-ins
across 36 blocks.

## Flag

```bash
python exploit.py files/catcounty_results.zip
```

```text
[+] Block Meowjority kiem soat:
      - Cardboard Court
      - Catnip Corner
      - Hairball Heights
      - Mousetrap Alley
      - Pawprint Plaza
      - Purrington Place
      - Scratching Post Street
      - Sunbeam Square
      - Tuna Terrace
      - Whisker Row
      - Windowsill Way
      - Yarnball Yard
[+] flag: cdctf{12}
```

## Reproduce

```bash
python exploit.py files/catcounty_results.zip                    # full solution, writes flag.txt
python analysis/alignment.py files/catcounty_results.zip         # pairing evidence per candidate lag
python analysis/sensitivity.py files/catcounty_results.zip       # Meowjority seats under lag -1 / 0 / +1
```

## The twelve blocks carried into Gerry the Larry (2/2)

Cardboard Court, Catnip Corner, Hairball Heights, Mousetrap Alley, Pawprint Plaza, Purrington Place,
Scratching Post Street, Sunbeam Square, Tuna Terrace, Whisker Row, Windowsill Way, Yarnball Yard.

The 36 block names in `info.csv` are the same precinct list the part 2/2 client renders: that client
uses a 6x6 table (36 cells) and three of its names (Treat Jar Terrace, Cushion Hill, Biscuit Bend) all
appear in the list above, so both challenges share one district map.

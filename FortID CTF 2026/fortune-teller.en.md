---
title: "Fortune Teller"
category: "Pwn"
tags: ["format-string", "pie-leak", "targeted-overwrite"]
solve_date: "2026-10-10"
language: "en"
---

# Fortune Teller

**Recorded flag:** `FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}`  
**Service:** `ncat --ssl fortune-teller-afeef2cf7bdb.inst15.ctf.fortid.com 1337` (TLS on port 1337). Handout: `fortune_teller_public.zip` 4.6 KB. Author: ipaljak.

## Challenge

The service is a `Fortune Teller`: it takes input from the player and prints a fortune, which includes a blessing line built from a string the program already holds. The objective is to take the flag from a running instance.

## Analysis

Two facts about the primitive:

1. **Read through the format string.** The input passes through a printf-style formatting function, so `%41$p` prints the value sitting at argument position 41 — in the runs of this challenge, a pointer belonging to the running process. From one such leaked value the driver derives the module base and the two addresses it needs: the return site recorded in the log (`ret`) and the address of the blessing string (`bless`).
2. **The write target is the blessing string.** `slot_idx=36` identifies the slot holding the blessing string, and that string lives in a writable region of the image; overwriting it in place is enough to change the fortune that gets printed. No code execution is involved.

In the recorded run, the differences from the module base are `ret = base + 0x1664` and `bless = base + 0x404c`; `base_aligned=True` is the driver's own check confirming the derived base is page-aligned, and `bad=[]` is that check's exclusion list (empty).

Those three hex values are PIE addresses of that single run, produced by the leak, not reusable constants.

## Solution

The sequence carried out on the instance; every step runs live:

1. Connect over TLS to the instance, send input containing `%41$p` to read the pointer that comes back, and derive the module base from it.
2. From that base, build the two addresses in use: the `ret` position and the address of the blessing string (`bless`), confirming the write slot is `slot_idx=36`.
3. Use the format string's write capability to overwrite the blessing string at `bless`, then let the service print the fortune again.

The three lines kept in the record, in the order they appear for the same run (`[1]` is the run index):

```text
[1] ret=0x56158039d664 base=0x56158039c000 bless=0x5615803a004c base_aligned=True bad=[] slot_idx=36
```

```text
[1] blessing says: The stars are aligned.
```

```text
FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}
```

The block above is the log of the driver that ran the session, not verbatim service output: the two `[1]` lines are printed by the driver to record the values it derived and the blessing line the service returned, while the last line is the flag that came back in the same session after the overwrite. The record does not retain the individual bytes sent in step 3, so the replacement string is not quoted here; what the evidence supports is that the write target was the blessing string in slot 36, and that the flag was returned in that same session after the write.

## Result

```text
FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

A TLS client that can talk to port 1337 (nmap-ncat or equivalent) plus a running instance:

```text
ncat --ssl fortune-teller-afeef2cf7bdb.inst15.ctf.fortid.com 1337
```

| Item | Role | Stable across runs |
|---|---|---|
| `%41$p` | token that reads a pointer through the format string | yes, constant in the payload |
| module base | origin of every other address | no, PIE, must come from the leak |
| `base + 0x1664` | the `ret` position in the recorded run | not verified across builds |
| `base + 0x404c` | address of the blessing string (`bless`) | not verified across builds |
| `slot_idx=36` | slot holding the writable blessing string | reported by the service through the leak |

The record is insufficient to rebuild a complete payload; this description is not a runnable solver.

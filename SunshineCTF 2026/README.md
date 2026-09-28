# SunshineCTF 2026

Writeups for challenges solved at [sunshinectf.games](https://sunshinectf.games).  
Flag format: `sun{…}`

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [cache-money](cache-money/writeup.md) | Pwn | Hard | `sun{s4fe_l1nk1ng_w0nt_s4ve_y0ur_tc4che}` |
| [code-breaker](code-breaker/writeup.md) | Crypto/Pwn | Hard | `sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}` |
| [cookiecorp](cookiecorp/writeup.md) | Web | Medium | `sun{c00kie_jar_0verfl0w_ev1cts_the_chief}` |
| [groundhog_day](groundhog_day/writeup.md) | Web | Hard | `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}` |
| [homemaker](homemaker/writeup.md) | Pwn | Hard | `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}` |
| [madlibs](madlibs/writeup.md) | Pwn | Medium | `sun{f1ll_iN_th3_g0T_eNtry}` |
| [my-eyes-burn](my-eyes-burn/writeup.md) | Misc | Medium | `sun{praisethesun}` |
| [nas-coal](nas-coal/writeup.md) | Forensics | Medium | `sun{yup_issa_gem}` |
| [planetary-probe](planetary-probe/writeup.md) | Web | Hard | `sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}` |
| [print-print-revolution](print-print-revolution/writeup.md) | Pwn | Hard | `sun{cust0m_fmtstr_n0_t00ls_4ll0wed}` |
| [robocall](robocall/writeup.md) | Pwn | Hard | `sun{you_must_be_some_sort_of_nimble_space_navigator}` |
| [safe-house](safe-house/writeup.md) | Pwn | Hard | `sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}` |
| [sitecheck](sitecheck/writeup.md) | Web | Hard | `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}` |
| [suntrail](suntrail/writeup.md) | Misc | Medium | `sun{qwerty_sucks}` |
| [total_recall](total_recall/writeup.md) | Pwn | Medium | `sun{r3caLl_ev3Ry_reGist3r_sR0p}` |
| [vecnet](vecnet/writeup.md) | Web | Hard | `sun{k33p_your_emb3ddings_secur3!}` |
| [welcome-call](welcome-call/writeup.md) | Forensics | Medium | `sun{thankyouforplaying}` |
| [you-cut-me-off](you-cut-me-off/writeup.md) | Forensics | Medium | `sun{totallyoriginalchallengeidea}` |

**Total: 18 solved**

## In Progress

| Directory | Status |
|-----------|--------|
| `_wip/planetary-probe` | Scripts and captures exist, no flag obtained |

## Challenge Structure

```
<challenge>/
  de.md          Original challenge description + verified metadata
  writeup.md     Solution: initial analysis → eliminated hypotheses → exploit chain → flag
  notes.md       Step-by-step investigation log (including dead ends)
  flag.txt       Captured flag string
  exploit.py     Reproducible solve script
  analysis/      Exploratory scripts for each phase
  files/         Original challenge artifacts (unmodified)
```

Template for new challenges: [`../_template/`](../_template/)

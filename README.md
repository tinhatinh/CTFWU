# CTF Writeups

My own writeups from competitive CTF events. I play with **R3:TURИ**
([CTFTime team 449538](https://ctftime.org/team/449538)): minhduc26122913, k4tpr02k5, Tikilazada,
tinhatinh, Lizamort1 - their solutions live in their own repos, this one is only mine.

**Rendered site:** <https://tinhatinh.github.io/CTFWU/> (custom Jekyll interface, deployed by GitHub Actions).

## Competitions

| Event | Date | Writeups | Categories |
|-------|------|----------|------------|
| [H7CTF 2026 Quals](H7CTF%202026%20Quals/README.md) | Sep 2026 | 29 | Pwn · Crypto · Web · Web3 · Hardware · Forensics · Mobile · Cloud · AI · Rev · OSINT · Misc |
| [SunshineCTF 2026](SunshineCTF%202026/README.md) | Sep 2026 | 18 | Pwn · Web · Crypto · Forensics · Misc |
| [Pointer Overflow CTF 2026](Pointer%20Overflow%20CTF%202026/writeup.md) | Sep 2026 | 8 | Crypto · EXP · Forensics · Misc · OSINT · RE · Steg · Web |
| [CSS CTF 2026: Return of Nexus](CSS%20CTF%202026/README.md) | Oct 2026 | 17 | Web · Pwn · Crypto · Forensics · OSINT · Misc · Reverse Engineering · Web3 |
| [CDCTF 2026](CDCTF%202026/README.md) | Oct 2026 | 41 | Crypto · Forensics · Log Analysis · Misc · NTA · OSINT · Password Cracking · Pwn · Reverse · Scanning · Web |
| [Cryovault 2026 Quals](Cryovault%202026%20Quals/README.md) | Oct 2026 | 26 | AI · Boot2Root · Crypto · Forensics · Hardware · Mobile · Pwn · Reverse · Web |
| [FooBar CTF 2026](FooBar%20CTF%202026/README.md) | Oct 2026 | 11 | Crypto · Pwn · Reverse · Web |
| [kBxAc CTF 2026](kBxAc%20CTF%202026/README.md) | Oct 2026 | 14 | Crypto · Forensics · Misc · Pwn · Reverse · Web |
| [ByteMe CTF 26](ByteMe%20CTF%2026/README.md) | Oct 2026 | 39 | Crypto · Forensics · Misc · Mobile · OSINT · Pwn · Reverse · Steg · Web |
| [FortID CTF 2026](FortID%20CTF%202026/README.md) | Oct 2026 | 22 | Crypto · Misc · OSINT · Pwn · Reverse · Web |

**Total: 225 writeups**

## Structure

From **Cryovault 2026 Quals** onward, each challenge has just two Markdown editions:

```text
<Event>/
  <challenge>.md       # VN
  <challenge>.en.md    # EN
  images/             # shared images only when needed
```

Templates: `_template/writeup.md` and `_template/writeup.en.md`. Create the pair with
`python _template/new_case.py "Cryovault 2026 Quals" <challenge> --category <Category> --solve-date <ISO-date>`.
No per-challenge statement, notes, flag or exploit sidecars are required. Both editions
carry the same known solve date and primary category; only prose is translated. Preserve
code, commands and recorded output. Older events keep their existing paths and layout:

```
<challenge-name>/
  writeup.md     Solution walkthrough with exploitation chain and flag
  writeup.en.md  English edition: prose translated, every fenced block byte-identical to the Vietnamese
  de.md          Original challenge description and verified metadata
  notes.md       Step-by-step investigation log (including dead ends)
  flag.txt       Captured flag string
  exploit.py     Reproducible solve script (reads artifacts from argv)
  analysis/      Exploratory scripts for each investigation phase
  files/         Original challenge artifacts (unmodified)
```

## Conventions

- Record flags and answers exactly as found in artifacts, readable images or captured output. Distinguish recovered values, issued markers and accepted submissions.
- Every claim in `writeup.md` traces back to a command logged in `notes.md`.
- Include only failed attempts that explain the solution. Keep detailed experiments and untested plans in `notes.md`.
- Solve scripts are self-contained and can be re-run against a live instance.
- Flag prefixes vary between challenges (even within the same event). Always verify before scanning.

## Quick Navigation

203 writeups across 9 competitions. Each challenge links to its Vietnamese and English editions.

<details>
<summary>ByteMe CTF 26 — 39 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Broken Soul Vault | Forensics | [VN](ByteMe%20CTF%2026/broken-soul-vault.md) | [EN](ByteMe%20CTF%2026/broken-soul-vault.en.md) |
| Chaos in the Plot | Misc | [VN](ByteMe%20CTF%2026/chaos-in-the-plot.md) | [EN](ByteMe%20CTF%2026/chaos-in-the-plot.en.md) |
| Don't fill me | Misc | [VN](ByteMe%20CTF%2026/dont-fill-me.md) | [EN](ByteMe%20CTF%2026/dont-fill-me.en.md) |
| Double Trouble | Crypto | [VN](ByteMe%20CTF%2026/double-trouble.md) | [EN](ByteMe%20CTF%2026/double-trouble.en.md) |
| Echoes of the Snap | Forensics | [VN](ByteMe%20CTF%2026/echoes-of-the-snap.md) | [EN](ByteMe%20CTF%2026/echoes-of-the-snap.en.md) |
| House of Water | Pwn | [VN](ByteMe%20CTF%2026/house-of-water.md) | [EN](ByteMe%20CTF%2026/house-of-water.en.md) |
| Infinity Echo | Crypto | [VN](ByteMe%20CTF%2026/infinity-echo.md) | [EN](ByteMe%20CTF%2026/infinity-echo.en.md) |
| Invisible Signal | Steg | [VN](ByteMe%20CTF%2026/invisible-signal.md) | [EN](ByteMe%20CTF%2026/invisible-signal.en.md) |
| The Keeper's Trail | OSINT | [VN](ByteMe%20CTF%2026/keepers-trail.md) | [EN](ByteMe%20CTF%2026/keepers-trail.en.md) |
| Level 0 — First Fragment | Misc | [VN](ByteMe%20CTF%2026/level-0-first-fragment.md) | [EN](ByteMe%20CTF%2026/level-0-first-fragment.en.md) |
| Mem-1 : When It Happened | Forensics | [VN](ByteMe%20CTF%2026/mem-1-when-it-happened.md) | [EN](ByteMe%20CTF%2026/mem-1-when-it-happened.en.md) |
| Mem-2 : Soul Hunt | Forensics | [VN](ByteMe%20CTF%2026/mem-2-soul-hunt.md) | [EN](ByteMe%20CTF%2026/mem-2-soul-hunt.en.md) |
| Mem-3 : The Painted Soul | Forensics | [VN](ByteMe%20CTF%2026/mem-3-the-painted-soul.md) | [EN](ByteMe%20CTF%2026/mem-3-the-painted-soul.en.md) |
| Mem-4 : A Fragment in Memory | Forensics | [VN](ByteMe%20CTF%2026/mem-4-a-fragment-in-memory.md) | [EN](ByteMe%20CTF%2026/mem-4-a-fragment-in-memory.en.md) |
| Mem-5 : The Last Trace | Forensics | [VN](ByteMe%20CTF%2026/mem-5-the-last-trace.md) | [EN](ByteMe%20CTF%2026/mem-5-the-last-trace.en.md) |
| Mem-6 : The Forgotten Note | Forensics | [VN](ByteMe%20CTF%2026/mem-6-the-forgotten-note.md) | [EN](ByteMe%20CTF%2026/mem-6-the-forgotten-note.en.md) |
| Red Skull's Trail | OSINT | [VN](ByteMe%20CTF%2026/red-skulls-trail.md) | [EN](ByteMe%20CTF%2026/red-skulls-trail.en.md) |
| Return to Win | Pwn | [VN](ByteMe%20CTF%2026/return-to-win.md) | [EN](ByteMe%20CTF%2026/return-to-win.en.md) |
| Sacrifice | Forensics | [VN](ByteMe%20CTF%2026/sacrifice.md) | [EN](ByteMe%20CTF%2026/sacrifice.en.md) |
| Soul Ascension | Mobile | [VN](ByteMe%20CTF%2026/soul-ascension.md) | [EN](ByteMe%20CTF%2026/soul-ascension.en.md) |
| Soul Echoes (The Stonekeeper's Chronicles) | Reverse | [VN](ByteMe%20CTF%2026/soul-echoes.md) | [EN](ByteMe%20CTF%2026/soul-echoes.en.md) |
| Soul Forge | Crypto | [VN](ByteMe%20CTF%2026/soul-forge.md) | [EN](ByteMe%20CTF%2026/soul-forge.en.md) |
| Soul Fragment Race | Web | [VN](ByteMe%20CTF%2026/soul-fragment-race.md) | [EN](ByteMe%20CTF%2026/soul-fragment-race.en.md) |
| Soul in the Shadows | Steg | [VN](ByteMe%20CTF%2026/soul-in-the-shadows.md) | [EN](ByteMe%20CTF%2026/soul-in-the-shadows.en.md) |
| Soul // Memory of Thanos | Pwn | [VN](ByteMe%20CTF%2026/soul-memory-of-thanos.md) | [EN](ByteMe%20CTF%2026/soul-memory-of-thanos.en.md) |
| Soul Memory | Forensics | [VN](ByteMe%20CTF%2026/soul-memory.md) | [EN](ByteMe%20CTF%2026/soul-memory.en.md) |
| Soul Vault: The Collector | Pwn | [VN](ByteMe%20CTF%2026/soul-vault-the-collector.md) | [EN](ByteMe%20CTF%2026/soul-vault-the-collector.en.md) |
| Soul's Weakness | Pwn | [VN](ByteMe%20CTF%2026/souls-weakness.md) | [EN](ByteMe%20CTF%2026/souls-weakness.en.md) |
| Soul's Whisper | Reverse | [VN](ByteMe%20CTF%2026/souls-whisper.md) | [EN](ByteMe%20CTF%2026/souls-whisper.en.md) |
| SoulStone (The Trial of Vormir) | Reverse | [VN](ByteMe%20CTF%2026/soulstone-trial-of-vormir.md) | [EN](ByteMe%20CTF%2026/soulstone-trial-of-vormir.en.md) |
| SoulVault | Reverse | [VN](ByteMe%20CTF%2026/soulvault-go.md) | [EN](ByteMe%20CTF%2026/soulvault-go.en.md) |
| SoulVault | Mobile | [VN](ByteMe%20CTF%2026/soulvault-mobile.md) | [EN](ByteMe%20CTF%2026/soulvault-mobile.en.md) |
| Traveller-1 : The First Stop | OSINT | [VN](ByteMe%20CTF%2026/traveller-1-the-first-stop.md) | [EN](ByteMe%20CTF%2026/traveller-1-the-first-stop.en.md) |
| Traveller-2 : Seven Stops | OSINT | [VN](ByteMe%20CTF%2026/traveller-2-seven-stops.md) | [EN](ByteMe%20CTF%2026/traveller-2-seven-stops.en.md) |
| Traveller-3 : The Road Ends Here | OSINT | [VN](ByteMe%20CTF%2026/traveller-3-the-road-ends-here.md) | [EN](ByteMe%20CTF%2026/traveller-3-the-road-ends-here.en.md) |
| Traveller-4 : Two Names, One Fort | OSINT | [VN](ByteMe%20CTF%2026/traveller-4-two-names-one-fort.md) | [EN](ByteMe%20CTF%2026/traveller-4-two-names-one-fort.en.md) |
| Traveller-5 : Two Shapes on the Horizon | OSINT | [VN](ByteMe%20CTF%2026/traveller-5-two-shapes-on-the-horizon.md) | [EN](ByteMe%20CTF%2026/traveller-5-two-shapes-on-the-horizon.en.md) |
| Traveller-6 : Across the Water | OSINT | [VN](ByteMe%20CTF%2026/traveller-6-across-the-water.md) | [EN](ByteMe%20CTF%2026/traveller-6-across-the-water.en.md) |
| Vormir Common Modulus | Crypto | [VN](ByteMe%20CTF%2026/vormir-common-modulus.md) | [EN](ByteMe%20CTF%2026/vormir-common-modulus.en.md) |

</details>

<details>
<summary>FooBar CTF 2026 — 11 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| The Debugger | Web | [VN](FooBar%20CTF%202026/The%20Debugger.md) | [EN](FooBar%20CTF%202026/The%20Debugger.en.md) |
| The Missing Application | Web | [VN](FooBar%20CTF%202026/the-missing-application.md) | [EN](FooBar%20CTF%202026/the-missing-application.en.md) |
| The Discount That Wasn't There | Web | [VN](FooBar%20CTF%202026/the-discount-that-wasn-t-there.md) | [EN](FooBar%20CTF%202026/the-discount-that-wasn-t-there.en.md) |
| ouroboros_vm | Reverse | [VN](FooBar%20CTF%202026/ouroboros_vm.md) | [EN](FooBar%20CTF%202026/ouroboros_vm.en.md) |
| poly_vault | Reverse | [VN](FooBar%20CTF%202026/poly_vault.md) | [EN](FooBar%20CTF%202026/poly_vault.en.md) |
| Knapsack Nemesis | Crypto | [VN](FooBar%20CTF%202026/Knapsack%20Nemesis.md) | [EN](FooBar%20CTF%202026/Knapsack%20Nemesis.en.md) |
| Blackbox_Archive | Pwn | [VN](FooBar%20CTF%202026/Blackbox_Archive.md) | [EN](FooBar%20CTF%202026/Blackbox_Archive.en.md) |
| smooth_orbit | Crypto | [VN](FooBar%20CTF%202026/smooth_orbit.md) | [EN](FooBar%20CTF%202026/smooth_orbit.en.md) |
| nebula_obscura | Crypto | [VN](FooBar%20CTF%202026/nebula_obscura.md) | [EN](FooBar%20CTF%202026/nebula_obscura.en.md) |
| Fast_Lane | Crypto | [VN](FooBar%20CTF%202026/Fast_Lane.md) | [EN](FooBar%20CTF%202026/Fast_Lane.en.md) |
| linear_drift | Crypto | [VN](FooBar%20CTF%202026/linear_drift.md) | [EN](FooBar%20CTF%202026/linear_drift.en.md) |

</details>

<details>
<summary>kBxAc CTF 2026 — 14 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Solevault | Web | [VN](kBxAc%20CTF%202026/solevault.md) | [EN](kBxAc%20CTF%202026/solevault.en.md) |
| Insanity Check | Misc | [VN](kBxAc%20CTF%202026/Insanity%20Check.md) | [EN](kBxAc%20CTF%202026/Insanity%20Check.en.md) |
| The Last Protocol | Crypto | [VN](kBxAc%20CTF%202026/The%20Last%20Protocol.md) | [EN](kBxAc%20CTF%202026/The%20Last%20Protocol.en.md) |
| The Graveyard | Misc | [VN](kBxAc%20CTF%202026/The%20Graveyard.md) | [EN](kBxAc%20CTF%202026/The%20Graveyard.en.md) |
| Hidden Patronus | Forensics | [VN](kBxAc%20CTF%202026/Hidden%20Patronus.md) | [EN](kBxAc%20CTF%202026/Hidden%20Patronus.en.md) |
| Invisible Scan | Misc | [VN](kBxAc%20CTF%202026/Invisible%20Scan.md) | [EN](kBxAc%20CTF%202026/Invisible%20Scan.en.md) |
| Original Unlimited Codex 100% Free | Pwn | [VN](kBxAc%20CTF%202026/original-unlimited-codex.md) | [EN](kBxAc%20CTF%202026/original-unlimited-codex.en.md) |
| Ghost in the Group | Crypto | [VN](kBxAc%20CTF%202026/Ghost%20in%20the%20Group.md) | [EN](kBxAc%20CTF%202026/Ghost%20in%20the%20Group.en.md) |
| Crossword 2 | Crypto | [VN](kBxAc%20CTF%202026/Crossword%202.md) | [EN](kBxAc%20CTF%202026/Crossword%202.en.md) |
| Lets Get to Library | Pwn | [VN](kBxAc%20CTF%202026/Lets%20Get%20to%20Library.md) | [EN](kBxAc%20CTF%202026/Lets%20Get%20to%20Library.en.md) |
| C-Laude | Forensics | [VN](kBxAc%20CTF%202026/C-Laude.md) | [EN](kBxAc%20CTF%202026/C-Laude.en.md) |
| Crossword 1 | Crypto | [VN](kBxAc%20CTF%202026/Crossword%201.md) | [EN](kBxAc%20CTF%202026/Crossword%201.en.md) |
| Most Secure Bank Of Endia | Pwn | [VN](kBxAc%20CTF%202026/Most%20Secure%20Bank%20Of%20Endia.md) | [EN](kBxAc%20CTF%202026/Most%20Secure%20Bank%20Of%20Endia.en.md) |
| simphell | Reverse | [VN](kBxAc%20CTF%202026/simphell.md) | [EN](kBxAc%20CTF%202026/simphell.en.md) |

</details>

<details>
<summary>Cryovault 2026 Quals — 26 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| The Meridian | Web | [VN](Cryovault%202026%20Quals/the-meridian.md) | [EN](Cryovault%202026%20Quals/the-meridian.en.md) |
| Field Console | Mobile | [VN](Cryovault%202026%20Quals/field-console.md) | [EN](Cryovault%202026%20Quals/field-console.en.md) |
| Oatmeal | Mobile | [VN](Cryovault%202026%20Quals/oatmeal.md) | [EN](Cryovault%202026%20Quals/oatmeal.en.md) |
| Mirage | Pwn | [VN](Cryovault%202026%20Quals/mirage.md) | [EN](Cryovault%202026%20Quals/mirage.en.md) |
| Greyline Junction | Web | [VN](Cryovault%202026%20Quals/greyline-junction.md) | [EN](Cryovault%202026%20Quals/greyline-junction.en.md) |
| GHOST - 13 | Hardware | [VN](Cryovault%202026%20Quals/ghost-13.md) | [EN](Cryovault%202026%20Quals/ghost-13.en.md) |
| Draftpad | Web | [VN](Cryovault%202026%20Quals/draftpad.md) | [EN](Cryovault%202026%20Quals/draftpad.en.md) |
| half-truths | Crypto | [VN](Cryovault%202026%20Quals/half-truths.md) | [EN](Cryovault%202026%20Quals/half-truths.en.md) |
| Kelpie | Reverse | [VN](Cryovault%202026%20Quals/kelpie.md) | [EN](Cryovault%202026%20Quals/kelpie.en.md) |
| The Alphabet That Wasn't There | Forensics | [VN](Cryovault%202026%20Quals/the-alphabet-that-wasn-t-there.md) | [EN](Cryovault%202026%20Quals/the-alphabet-that-wasn-t-there.en.md) |
| EchoChamber | Boot2Root | [VN](Cryovault%202026%20Quals/echochamber.md) | [EN](Cryovault%202026%20Quals/echochamber.en.md) |
| Lossless, Not Harmless | Forensics | [VN](Cryovault%202026%20Quals/lossless-not-harmless.md) | [EN](Cryovault%202026%20Quals/lossless-not-harmless.en.md) |
| Safe Alone | AI | [VN](Cryovault%202026%20Quals/safe-alone.md) | [EN](Cryovault%202026%20Quals/safe-alone.en.md) |
| Phantom Mesh | Forensics | [VN](Cryovault%202026%20Quals/phantom-mesh.md) | [EN](Cryovault%202026%20Quals/phantom-mesh.en.md) |
| Last Packet | Forensics | [VN](Cryovault%202026%20Quals/last-packet.md) | [EN](Cryovault%202026%20Quals/last-packet.en.md) |
| The Deletion Echo | AI | [VN](Cryovault%202026%20Quals/the-deletion-echo.md) | [EN](Cryovault%202026%20Quals/the-deletion-echo.en.md) |
| The Last Committed Message | Forensics | [VN](Cryovault%202026%20Quals/the-last-committed-message.md) | [EN](Cryovault%202026%20Quals/the-last-committed-message.en.md) |
| Ghost in the Spooler | Forensics | [VN](Cryovault%202026%20Quals/ghost-in-the-spooler.md) | [EN](Cryovault%202026%20Quals/ghost-in-the-spooler.en.md) |
| The Image That Forgot | Forensics | [VN](Cryovault%202026%20Quals/the-image-that-forgot.md) | [EN](Cryovault%202026%20Quals/the-image-that-forgot.en.md) |
| Signed, But Which Original? | Forensics | [VN](Cryovault%202026%20Quals/signed-but-which-original.md) | [EN](Cryovault%202026%20Quals/signed-but-which-original.en.md) |
| frost-ledger | Forensics | [VN](Cryovault%202026%20Quals/frost-ledger.md) | [EN](Cryovault%202026%20Quals/frost-ledger.en.md) |
| Rimefold | Pwn | [VN](Cryovault%202026%20Quals/rimefold.md) | [EN](Cryovault%202026%20Quals/rimefold.en.md) |
| Slab | Pwn | [VN](Cryovault%202026%20Quals/slab.md) | [EN](Cryovault%202026%20Quals/slab.en.md) |
| Tearing | Pwn | [VN](Cryovault%202026%20Quals/tearing.md) | [EN](Cryovault%202026%20Quals/tearing.en.md) |
| Write Hole | Forensics | [VN](Cryovault%202026%20Quals/write-hole.md) | [EN](Cryovault%202026%20Quals/write-hole.en.md) |
| Journal Necromancy | Forensics | [VN](Cryovault%202026%20Quals/journal-necromancy.md) | [EN](Cryovault%202026%20Quals/journal-necromancy.en.md) |

</details>

<details>
<summary>H7CTF 2026 Quals — 29 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Echo Chamber - AI (Medium) | AI | [VN](H7CTF%202026%20Quals/echo-chamber/writeup.md) | [EN](H7CTF%202026%20Quals/echo-chamber/writeup.en.md) |
| Countersign - Rev (Insane) | Reverse | [VN](H7CTF%202026%20Quals/countersign/writeup.md) | [EN](H7CTF%202026%20Quals/countersign/writeup.en.md) |
| Kintsugi Vault - Rev (Hard) | Reverse | [VN](H7CTF%202026%20Quals/kintsugi-vault/writeup.md) | [EN](H7CTF%202026%20Quals/kintsugi-vault/writeup.en.md) |
| Dog Whistle - Hardware (Insane) | Hardware | [VN](H7CTF%202026%20Quals/dog-whistle/writeup.md) | [EN](H7CTF%202026%20Quals/dog-whistle/writeup.en.md) |
| Trompe-l'œil - Web3 (Hard) | Web3 | [VN](H7CTF%202026%20Quals/trompe-loeil/writeup.md) | [EN](H7CTF%202026%20Quals/trompe-loeil/writeup.en.md) |
| Meridian Pay - Mobile (Hard) | Mobile | [VN](H7CTF%202026%20Quals/meridian-pay/writeup.md) | [EN](H7CTF%202026%20Quals/meridian-pay/writeup.en.md) |
| Genesis - Web3 (Medium) | Web3 | [VN](H7CTF%202026%20Quals/genesis/writeup.md) | [EN](H7CTF%202026%20Quals/genesis/writeup.en.md) |
| Deputy - Cloud (Hard) | Cloud | [VN](H7CTF%202026%20Quals/deputy/writeup.md) | [EN](H7CTF%202026%20Quals/deputy/writeup.en.md) |
| Tapeout - Misc (Hard) | Misc | [VN](H7CTF%202026%20Quals/tapeout/writeup.md) | [EN](H7CTF%202026%20Quals/tapeout/writeup.en.md) |
| Owner's Draw - Crypto (Medium) | Crypto | [VN](H7CTF%202026%20Quals/owners-draw/writeup.md) | [EN](H7CTF%202026%20Quals/owners-draw/writeup.en.md) |
| Manifest Destiny - Pwn (Medium) | Pwn | [VN](H7CTF%202026%20Quals/manifest-destiny/writeup.md) | [EN](H7CTF%202026%20Quals/manifest-destiny/writeup.en.md) |
| Shared Blood - Crypto (Medium) | Crypto | [VN](H7CTF%202026%20Quals/shared-blood/writeup.md) | [EN](H7CTF%202026%20Quals/shared-blood/writeup.en.md) |
| Loose Lips - Crypto (Hard) | Crypto | [VN](H7CTF%202026%20Quals/loose-lips/writeup.md) | [EN](H7CTF%202026%20Quals/loose-lips/writeup.en.md) |
| Take Two - Crypto (Hard) | Crypto | [VN](H7CTF%202026%20Quals/take-two/writeup.md) | [EN](H7CTF%202026%20Quals/take-two/writeup.en.md) |
| Ghost on the Bus - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/ghost-on-the-bus/writeup.md) | [EN](H7CTF%202026%20Quals/ghost-on-the-bus/writeup.en.md) |
| Justified - Web (Medium) | Web | [VN](H7CTF%202026%20Quals/justified/writeup.md) | [EN](H7CTF%202026%20Quals/justified/writeup.en.md) |
| Merged - Web (Medium) | Web | [VN](H7CTF%202026%20Quals/merged/writeup.md) | [EN](H7CTF%202026%20Quals/merged/writeup.en.md) |
| Radio Silence - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/radio-silence/writeup.md) | [EN](H7CTF%202026%20Quals/radio-silence/writeup.en.md) |
| Parcel Bomb - Pwn (Medium) | Pwn | [VN](H7CTF%202026%20Quals/arcel-bomb/writeup.md) | [EN](H7CTF%202026%20Quals/arcel-bomb/writeup.en.md) |
| Loose Ends - Pwn (Hard) | Pwn | [VN](H7CTF%202026%20Quals/loose-ends/writeup.md) | [EN](H7CTF%202026%20Quals/loose-ends/writeup.en.md) |
| Open Sesame - Hardware (Hard) | Hardware | [VN](H7CTF%202026%20Quals/open-sesame/writeup.md) | [EN](H7CTF%202026%20Quals/open-sesame/writeup.en.md) |
| Hear No Evil - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/hear-no-evil/writeup.md) | [EN](H7CTF%202026%20Quals/hear-no-evil/writeup.en.md) |
| Kick the CAN - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/kick-the-can/writeup.md) | [EN](H7CTF%202026%20Quals/kick-the-can/writeup.en.md) |
| Splice - Web (Hard) | Web | [VN](H7CTF%202026%20Quals/splice/writeup.md) | [EN](H7CTF%202026%20Quals/splice/writeup.en.md) |
| Trace Amounts - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/trace-amounts/writeup.md) | [EN](H7CTF%202026%20Quals/trace-amounts/writeup.en.md) |
| Papers Please - Pwn (Easy) | Pwn | [VN](H7CTF%202026%20Quals/papers-please/writeup.md) | [EN](H7CTF%202026%20Quals/papers-please/writeup.en.md) |
| Mic Drop - Hardware (Medium) | Hardware | [VN](H7CTF%202026%20Quals/mic-drop/writeup.md) | [EN](H7CTF%202026%20Quals/mic-drop/writeup.en.md) |
| Deep Freeze - Forensics (Hard) | Forensics | [VN](H7CTF%202026%20Quals/deep-freeze/writeup.md) | [EN](H7CTF%202026%20Quals/deep-freeze/writeup.en.md) |
| Patient Exfil - Forensics (Medium) | Forensics | [VN](H7CTF%202026%20Quals/patient-exfil/writeup.md) | [EN](H7CTF%202026%20Quals/patient-exfil/writeup.en.md) |

</details>

<details>
<summary>SunshineCTF 2026 — 18 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| CookieCorp - Web (Medium) | Web | [VN](SunshineCTF%202026/cookiecorp/writeup.md) | [EN](SunshineCTF%202026/cookiecorp/writeup.en.md) |
| You Cut Me Off - Forensics (Medium) | Forensics | [VN](SunshineCTF%202026/you-cut-me-off/writeup.md) | [EN](SunshineCTF%202026/you-cut-me-off/writeup.en.md) |
| RoboCall - Pwn (Hard) | Pwn | [VN](SunshineCTF%202026/robocall/writeup.md) | [EN](SunshineCTF%202026/robocall/writeup.en.md) |
| Cache Money - Pwn (Hard) | Pwn | [VN](SunshineCTF%202026/cache-money/writeup.md) | [EN](SunshineCTF%202026/cache-money/writeup.en.md) |
| VecNet - Web (Hard) | Web | [VN](SunshineCTF%202026/vecnet/writeup.md) | [EN](SunshineCTF%202026/vecnet/writeup.en.md) |
| Planetary Probe - Web (Hard) | Web | [VN](SunshineCTF%202026/planetary-probe/writeup.md) | [EN](SunshineCTF%202026/planetary-probe/writeup.en.md) |
| Groundhog Day - Web (Hard) | Web | [VN](SunshineCTF%202026/groundhog_day/writeup.md) | [EN](SunshineCTF%202026/groundhog_day/writeup.en.md) |
| Print Print Revolution - Pwn (Hard) | Pwn | [VN](SunshineCTF%202026/print-print-revolution/writeup.md) | [EN](SunshineCTF%202026/print-print-revolution/writeup.en.md) |
| Homemaker - Pwn (Hard) | Pwn | [VN](SunshineCTF%202026/homemaker/writeup.md) | [EN](SunshineCTF%202026/homemaker/writeup.en.md) |
| SiteCheck - Web (Hard) | Web | [VN](SunshineCTF%202026/sitecheck/writeup.md) | [EN](SunshineCTF%202026/sitecheck/writeup.en.md) |
| Safe House - Pwn (Hard) | Pwn | [VN](SunshineCTF%202026/safe-house/writeup.md) | [EN](SunshineCTF%202026/safe-house/writeup.en.md) |
| Total Recall - Pwn (Medium) | Pwn | [VN](SunshineCTF%202026/total_recall/writeup.md) | [EN](SunshineCTF%202026/total_recall/writeup.en.md) |
| Code Breaker - Crypto/Pwn (Hard) | Crypto | [VN](SunshineCTF%202026/code-breaker/writeup.md) | [EN](SunshineCTF%202026/code-breaker/writeup.en.md) |
| Mad Libs - Pwn (Medium) | Pwn | [VN](SunshineCTF%202026/madlibs/writeup.md) | [EN](SunshineCTF%202026/madlibs/writeup.en.md) |
| Welcome Call - Forensics (Medium) | Forensics | [VN](SunshineCTF%202026/welcome-call/writeup.md) | [EN](SunshineCTF%202026/welcome-call/writeup.en.md) |
| NAS Coal - Forensics (Medium) | Forensics | [VN](SunshineCTF%202026/nas-coal/writeup.md) | [EN](SunshineCTF%202026/nas-coal/writeup.en.md) |
| Suntrail - Misc (Medium) | Misc | [VN](SunshineCTF%202026/suntrail/writeup.md) | [EN](SunshineCTF%202026/suntrail/writeup.en.md) |
| My Eyes Burn - Misc (Medium) | Misc | [VN](SunshineCTF%202026/my-eyes-burn/writeup.md) | [EN](SunshineCTF%202026/my-eyes-burn/writeup.en.md) |

</details>

<details>
<summary>CSS CTF 2026 — 17 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Kuiper Belt Relay Core - Pwn (Beginner) | Pwn | [VN](CSS%20CTF%202026/Kuiper%20Belt%20Relay%20Core/writeup.md) | [EN](CSS%20CTF%202026/Kuiper%20Belt%20Relay%20Core/writeup.en.md) |
| Gateway - Web3 (199 points) | Web3 | [VN](CSS%20CTF%202026/gateway/writeup.md) | [EN](CSS%20CTF%202026/gateway/writeup.en.md) |
| Astrolobe Overwrite - Pwn/Reverse (Expert, 746pts) | Pwn | [VN](CSS%20CTF%202026/astrolobe_overwrite/writeup.md) | [EN](CSS%20CTF%202026/astrolobe_overwrite/writeup.en.md) |
| Cloudy with a Chance of Spaceships - Web (67 pts) | Web | [VN](CSS%20CTF%202026/cloudy-spaceships/writeup.md) | [EN](CSS%20CTF%202026/cloudy-spaceships/writeup.en.md) |
| lottery - Web3 (299 pts) | Web3 | [VN](CSS%20CTF%202026/lottery/writeup.md) | [EN](CSS%20CTF%202026/lottery/writeup.en.md) |
| Chrono II - Crypto (Intermediate) | Crypto | [VN](CSS%20CTF%202026/chrono-ii/writeup.md) | [EN](CSS%20CTF%202026/chrono-ii/writeup.en.md) |
| Maintenance Log - Pwn (150 điểm) | Pwn | [VN](CSS%20CTF%202026/maintenance-log/writeup.md) | [EN](CSS%20CTF%202026/maintenance-log/writeup.en.md) |
| Flappy Board - Misc (Intermediate) | Misc | [VN](CSS%20CTF%202026/flappy-board/writeup.md) | [EN](CSS%20CTF%202026/flappy-board/writeup.en.md) |
| Prince Walk - Reverse (50 pts) | Reverse | [VN](CSS%20CTF%202026/prince-walk/writeup.md) | [EN](CSS%20CTF%202026/prince-walk/writeup.en.md) |
| Severed Symmetry - Crypto (Expert) | Crypto | [VN](CSS%20CTF%202026/severed-symmetry/writeup.md) | [EN](CSS%20CTF%202026/severed-symmetry/writeup.en.md) |
| Dockside Ticket Office - Pwn (Beginner) | Pwn | [VN](CSS%20CTF%202026/dockside-ticket/writeup.md) | [EN](CSS%20CTF%202026/dockside-ticket/writeup.en.md) |
| Server Juice - OSINT (Beginner) | OSINT | [VN](CSS%20CTF%202026/server-juice/writeup.md) | [EN](CSS%20CTF%202026/server-juice/writeup.en.md) |
| A Star Trail 2 - Misc/Graph (Intermediate) | Misc | [VN](CSS%20CTF%202026/a-star-trail-2/writeup.md) | [EN](CSS%20CTF%202026/a-star-trail-2/writeup.en.md) |
| A Star Trail - Misc/OSINT (Beginner) | Misc | [VN](CSS%20CTF%202026/a-star-trail/writeup.md) | [EN](CSS%20CTF%202026/a-star-trail/writeup.en.md) |
| Lamp Drill - Warm-up (49 điểm) | Warm-up | [VN](CSS%20CTF%202026/lamp-drill/writeup.md) | [EN](CSS%20CTF%202026/lamp-drill/writeup.en.md) |
| Colour Shift - Forensics (Beginner) | Forensics | [VN](CSS%20CTF%202026/colour-shift/writeup.md) | [EN](CSS%20CTF%202026/colour-shift/writeup.en.md) |
| Chrono I - Crypto (Beginner) | Crypto | [VN](CSS%20CTF%202026/chrono-i/writeup.md) | [EN](CSS%20CTF%202026/chrono-i/writeup.en.md) |

</details>

<details>
<summary>Pointer Overflow CTF 2026 — 8 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Shape of Query - WEB (300 pts) | Web | [VN](Pointer%20Overflow%20CTF%202026/shape-of-query/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/shape-of-query/writeup.en.md) |
| Invisible Text - STEG (200 pts) | Steg | [VN](Pointer%20Overflow%20CTF%202026/invisible-text/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/invisible-text/writeup.en.md) |
| Excavation - Reverse Engineering (100 pts) | Reverse | [VN](Pointer%20Overflow%20CTF%202026/excavation/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/excavation/writeup.en.md) |
| Where the Light Fails to Fall - OSINT | OSINT | [VN](Pointer%20Overflow%20CTF%202026/where-the-light-fails-to-fall/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/where-the-light-fails-to-fall/writeup.en.md) |
| The Apparatus, Invocation - Misc | Misc | [VN](Pointer%20Overflow%20CTF%202026/the-apparatus-invocation/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/the-apparatus-invocation/writeup.en.md) |
| Everything Left Open - Forensics | Forensics | [VN](Pointer%20Overflow%20CTF%202026/everything-left-open/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/everything-left-open/writeup.en.md) |
| Read Me My Fortune - Exploitation | EXP | [VN](Pointer%20Overflow%20CTF%202026/read-me-my-fortune/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/read-me-my-fortune/writeup.en.md) |
| Letters Never Sent - Crypto | Crypto | [VN](Pointer%20Overflow%20CTF%202026/letters-never-sent/writeup.md) | [EN](Pointer%20Overflow%20CTF%202026/letters-never-sent/writeup.en.md) |

</details>

<details>
<summary>CDCTF 2026 — 41 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| soupOS 3: Bad Recipe - Rev Eng pwn (498 điểm) | Reverse | [VN](CDCTF%202026/soupos-3-bad-recipe/writeup.md) | [EN](CDCTF%202026/soupos-3-bad-recipe/writeup.en.md) |
| soupOS 2: Salt to Taste - Rev Eng pwn (489 điểm) | Reverse | [VN](CDCTF%202026/soupos-2-salt-to-taste/writeup.md) | [EN](CDCTF%202026/soupos-2-salt-to-taste/writeup.en.md) |
| soupOS 1: Mise en Place - Rev Eng pwn (479 điểm) | Reverse | [VN](CDCTF%202026/soupos-1-mise-en-place/writeup.md) | [EN](CDCTF%202026/soupos-1-mise-en-place/writeup.en.md) |
| soupOS 0: Welcome to the Kitchen - Rev Eng pwn (431 điểm) | Reverse | [VN](CDCTF%202026/soupos-0-welcome-to-the-kitchen/writeup.md) | [EN](CDCTF%202026/soupos-0-welcome-to-the-kitchen/writeup.en.md) |
| cookies - Web (500 points) | Web | [VN](CDCTF%202026/cookies/writeup.md) | [EN](CDCTF%202026/cookies/writeup.en.md) |
| bring-coines - Reverse Engineering (500 points) | Reverse | [VN](CDCTF%202026/bring-coines/writeup.md) | [EN](CDCTF%202026/bring-coines/writeup.en.md) |
| Yummy Rat Toast - Password Cracking (500 points) | Password Cracking | [VN](CDCTF%202026/yummy-rat-toast/writeup.md) | [EN](CDCTF%202026/yummy-rat-toast/writeup.en.md) |
| Wish - pwn (800 điểm) | Pwn | [VN](CDCTF%202026/wish/writeup.md) | [EN](CDCTF%202026/wish/writeup.en.md) |
| Verbal Authentication Transmissions 5/5: You get all that? - OSINT + Crypto (500 pts) | OSINT | [VN](CDCTF%202026/vat-5-you-get-all-that/writeup.md) | [EN](CDCTF%202026/vat-5-you-get-all-that/writeup.en.md) |
| Verbal Authentication Transmissions 4/5: What the helly - OSINT + Crypto + Password Cracking (500 pts) | OSINT | [VN](CDCTF%202026/vat-4-what-the-helly/writeup.md) | [EN](CDCTF%202026/vat-4-what-the-helly/writeup.en.md) |
| Verbal Authentication Transmissions 3/5: Pretty Good Passphrase - OSINT + Crypto (500 pts) | OSINT | [VN](CDCTF%202026/vat-3-pretty-good-passphrase/writeup.md) | [EN](CDCTF%202026/vat-3-pretty-good-passphrase/writeup.en.md) |
| Verbal Authentication Transmissions 1/5: Going HAM - OSINT + Crypto (500 pts) | OSINT | [VN](CDCTF%202026/vat-1-going-ham/writeup.md) | [EN](CDCTF%202026/vat-1-going-ham/writeup.en.md) |
| Troubled Translation - OSINT (479 điểm) | OSINT | [VN](CDCTF%202026/troubled-translation/writeup.md) | [EN](CDCTF%202026/troubled-translation/writeup.en.md) |
| The flag knows what it is at all times - Crypto (500 points) | Crypto | [VN](CDCTF%202026/flag-knows-what-it-is/writeup.md) | [EN](CDCTF%202026/flag-knows-what-it-is/writeup.en.md) |
| The Epic Adventures of Crypto Cat Caticus Catanius (1/5) - Crypto (Easy) | Crypto | [VN](CDCTF%202026/crypto-cat-1/writeup.md) | [EN](CDCTF%202026/crypto-cat-1/writeup.en.md) |
| Tacocat - Misc | Misc | [VN](CDCTF%202026/tacocat/writeup.md) | [EN](CDCTF%202026/tacocat/writeup.en.md) |
| Script of Theseus - Forensics (493 điểm) | Forensics | [VN](CDCTF%202026/script-of-theseus/writeup.md) | [EN](CDCTF%202026/script-of-theseus/writeup.en.md) |
| Night Catz Crazy Cat Club - RevE Crypto (500 điểm) | Reverse | [VN](CDCTF%202026/night-catz-crazy-cat-club/writeup.md) | [EN](CDCTF%202026/night-catz-crazy-cat-club/writeup.en.md) |
| Low on function names - Reverse Engineering (500 điểm) | Reverse | [VN](CDCTF%202026/low-on-fun/writeup.md) | [EN](CDCTF%202026/low-on-fun/writeup.en.md) |
| GitLash - pwn/Forensics (496 điểm) | Pwn | [VN](CDCTF%202026/gitlash/writeup.md) | [EN](CDCTF%202026/gitlash/writeup.en.md) |
| Gerry the Larry (1/2) - Log Analysis (500 điểm) | Log Analysis | [VN](CDCTF%202026/gerry-the-larry-1/writeup.md) | [EN](CDCTF%202026/gerry-the-larry-1/writeup.en.md) |
| Forensics Training Mat - Forensics (Training, 250 điểm) | Forensics | [VN](CDCTF%202026/forensics-training-mat/writeup.md) | [EN](CDCTF%202026/forensics-training-mat/writeup.en.md) |
| Epic Rat Encoding - Reverse (498 points) | Reverse | [VN](CDCTF%202026/epic-rat-encoding/writeup.md) | [EN](CDCTF%202026/epic-rat-encoding/writeup.en.md) |
| Eat your fruits and vegetables! - Crypto (500 points) | Crypto | [VN](CDCTF%202026/eat-your-fruits-and-vegetables/writeup.md) | [EN](CDCTF%202026/eat-your-fruits-and-vegetables/writeup.en.md) |
| Doomscroll Hell - Forensics | Forensics | [VN](CDCTF%202026/doomscroll-hell/writeup.md) | [EN](CDCTF%202026/doomscroll-hell/writeup.en.md) |
| Diggity Network - Forensics (500 điểm) | Forensics | [VN](CDCTF%202026/diggity-network/writeup.md) | [EN](CDCTF%202026/diggity-network/writeup.en.md) |
| Cosmic Call - Scanning / NTA / Crypto (797 điểm) | Scanning | [VN](CDCTF%202026/cosmic-call/writeup.md) | [EN](CDCTF%202026/cosmic-call/writeup.en.md) |
| Corporate RAT - Log Analysis (500 điểm) | Log Analysis | [VN](CDCTF%202026/corporate-rat/writeup.md) | [EN](CDCTF%202026/corporate-rat/writeup.en.md) |
| Catty Malware (3/3) - Forensics (499) | Forensics | [VN](CDCTF%202026/catty-malware-3/writeup.md) | [EN](CDCTF%202026/catty-malware-3/writeup.en.md) |
| Catty Malware (2/3) - Forensics (499) | Forensics | [VN](CDCTF%202026/catty-malware-2/writeup.md) | [EN](CDCTF%202026/catty-malware-2/writeup.en.md) |
| Catty Malware (1/3) - Forensics (500) | Forensics | [VN](CDCTF%202026/catty-malware-1/writeup.md) | [EN](CDCTF%202026/catty-malware-1/writeup.en.md) |
| CalcuRATor (4/4) - Forensics + Rev Eng + OSINT (500 points) | Forensics | [VN](CDCTF%202026/calcurator-4/writeup.md) | [EN](CDCTF%202026/calcurator-4/writeup.en.md) |
| CalcuRATor (3/4) - Forensics + Rev Eng (500 points) | Forensics | [VN](CDCTF%202026/calcurator-3/writeup.md) | [EN](CDCTF%202026/calcurator-3/writeup.en.md) |
| CalcuRATor (2/4) - Forensics + Rev Eng (500 points) | Forensics | [VN](CDCTF%202026/calcurator-2/writeup.md) | [EN](CDCTF%202026/calcurator-2/writeup.en.md) |
| CalcuRATor (1/4) - Forensics + Rev Eng (491 points) | Forensics | [VN](CDCTF%202026/calcurator-1/writeup.md) | [EN](CDCTF%202026/calcurator-1/writeup.en.md) |
| Blake's Bride - Forensics (500 điểm) | Forensics | [VN](CDCTF%202026/blakes-bride/writeup.md) | [EN](CDCTF%202026/blakes-bride/writeup.en.md) |
| Best of Friends - Crypto (500 points) | Crypto | [VN](CDCTF%202026/best-of-friends/writeup.md) | [EN](CDCTF%202026/best-of-friends/writeup.en.md) |
| A rat by any other name - Password Cracking (500 pts) | Password Cracking | [VN](CDCTF%202026/a-rat-by-any-other-name/writeup.md) | [EN](CDCTF%202026/a-rat-by-any-other-name/writeup.en.md) |
| Crypto Cat Caticus Catanius (3/5) - Crypto (498 điểm) | Crypto | [VN](CDCTF%202026/crypto-cat-3/writeup.md) | [EN](CDCTF%202026/crypto-cat-3/writeup.en.md) |
| Crypto Cat Caticus Catanius (2/5) - Crypto (496 điểm) | Crypto | [VN](CDCTF%202026/crypto-cat-2/writeup.md) | [EN](CDCTF%202026/crypto-cat-2/writeup.en.md) |
| Clear as Glass - Forensics/Rev Eng (500 điểm) | Forensics | [VN](CDCTF%202026/clear-as-glass/writeup.md) | [EN](CDCTF%202026/clear-as-glass/writeup.en.md) |

</details>

<details>
<summary>FortID CTF 2026 — 22 writeups</summary>

| Challenge | Category | VN | EN |
|---|---|---|---|
| Baby Crypto | Crypto | [VN](FortID%20CTF%202026/baby-crypto.md) | [EN](FortID%20CTF%202026/baby-crypto.en.md) |
| Baby Misc | Misc | [VN](FortID%20CTF%202026/baby-misc.md) | [EN](FortID%20CTF%202026/baby-misc.en.md) |
| Baby OSINT | OSINT | [VN](FortID%20CTF%202026/baby-osint.md) | [EN](FortID%20CTF%202026/baby-osint.en.md) |
| Baby Pwn | Pwn | [VN](FortID%20CTF%202026/baby-pwn.md) | [EN](FortID%20CTF%202026/baby-pwn.en.md) |
| Bounty Hunter | Crypto | [VN](FortID%20CTF%202026/bounty-hunter.md) | [EN](FortID%20CTF%202026/bounty-hunter.en.md) |
| Cubism | Reverse | [VN](FortID%20CTF%202026/cubism.md) | [EN](FortID%20CTF%202026/cubism.en.md) |
| DESBox | Crypto | [VN](FortID%20CTF%202026/desbox.md) | [EN](FortID%20CTF%202026/desbox.en.md) |
| Do You Know Lika? | Web | [VN](FortID%20CTF%202026/do-you-know-lika.md) | [EN](FortID%20CTF%202026/do-you-know-lika.en.md) |
| Doctor Bye Bye | Web | [VN](FortID%20CTF%202026/doctor-bye-bye.md) | [EN](FortID%20CTF%202026/doctor-bye-bye.en.md) |
| EU Gift | Misc | [VN](FortID%20CTF%202026/eu-gift.md) | [EN](FortID%20CTF%202026/eu-gift.en.md) |
| Editorial Board | Pwn | [VN](FortID%20CTF%202026/editorial-board.md) | [EN](FortID%20CTF%202026/editorial-board.en.md) |
| End of Life | Pwn | [VN](FortID%20CTF%202026/end-of-life.md) | [EN](FortID%20CTF%202026/end-of-life.en.md) |
| Flag from the Future | Misc | [VN](FortID%20CTF%202026/flag-from-the-future.md) | [EN](FortID%20CTF%202026/flag-from-the-future.en.md) |
| Fortune Teller | Pwn | [VN](FortID%20CTF%202026/fortune-teller.md) | [EN](FortID%20CTF%202026/fortune-teller.en.md) |
| GDB SaaS | Pwn | [VN](FortID%20CTF%202026/gdb-saas.md) | [EN](FortID%20CTF%202026/gdb-saas.en.md) |
| Hic Sunt Dracones | Crypto | [VN](FortID%20CTF%202026/hic-sunt-dracones.md) | [EN](FortID%20CTF%202026/hic-sunt-dracones.en.md) |
| Human RNG | Crypto | [VN](FortID%20CTF%202026/human-rng.md) | [EN](FortID%20CTF%202026/human-rng.en.md) |
| OSINT Exam II | OSINT | [VN](FortID%20CTF%202026/osint-exam-ii.md) | [EN](FortID%20CTF%202026/osint-exam-ii.en.md) |
| Sticker Booth | Pwn | [VN](FortID%20CTF%202026/sticker-booth.md) | [EN](FortID%20CTF%202026/sticker-booth.en.md) |
| String Peek and Poke | Pwn | [VN](FortID%20CTF%202026/string-peek-and-poke.md) | [EN](FortID%20CTF%202026/string-peek-and-poke.en.md) |
| Tangled | Misc | [VN](FortID%20CTF%202026/tangled.md) | [EN](FortID%20CTF%202026/tangled.en.md) |
| Ultimative PHP | Web | [VN](FortID%20CTF%202026/ultimative-php.md) | [EN](FortID%20CTF%202026/ultimative-php.en.md) |

</details>

## License

Educational use. Challenge descriptions and flag strings remain the property of their respective CTF organizers.

# Server Juice - OSINT (Beginner)

**Flag:** `CSSCTF{premiumreserve}`
**Resources:** No analytical attached files, the survey data is based on a public open source. Supporting archival documents include two static images in the `files/` directory.

## Problem Description

The system provides only a single text message: "If you want to appease the algorithm (and maybe get a head start on future hints), consider keeping us on your radar by following." The description does not include any data files, simulated servers, or URLs. An additional hint directs players to search for the event organizer's Instagram channel.
The objective is to extract the flag from a public comment located beneath a post titled "General Meeting 01!" belonging to the `@cybersecuritysydney` account.

## Initial Analysis

The account directed in the hint creates an informational honeypot causing noise right from the start. The `instagram.com/cybersecuritysociety` channel actually belongs to a Persian language cybersecurity organization, all 18 posts were published around 2018 and are completely unrelated to the tournament's scope. Analyzing the cause of this incident: the last page of the opening ceremony presentation slides explicitly states the message `Follow instagram.com/cybersecuritysociety :)`. This confirms the error originates from the presentation slide itself (incorrect handle recorded), and the problem's hint merely replicated that error. The organizer's official account is confirmed to be `@cybersecuritysydney`.

Conducting an in-depth review of the `@cybersecuritysydney` account, the initial collection results detected no abnormal data:

- Surveyed 27/27 captions: No post contains the `CSSCTF{` prefix format.
- Surveyed 19/19 posts in the Tagged tab: All are posts tagged by other affiliated organizations directed towards it, containing no abnormal content.
- The Reels tab has no data. The three highlight folders named `EVENTS`, `FUN FRIDAYS!`, and `ARCHIVE` each contain only one background music story, with no encrypted text attached.
- The system has no actively displayed story and does not trigger an auto-DM mechanism upon following the account.
- The Bio link redirects to the `linktr.ee/CybersecuritySocietySydney` structure. This link tree comprises 40 links, 8 of which belong to the organization, the remainder are default affiliate link codes of the Linktree platform.
- Extracted and analyzed 25 poster designs along with 7 QR codes. All decompressed QR codes point to standard event registration links (`ctf.cybersecurity.sydney`, Google Forms, `forms.gle/...`, and routing string `au.cglink.me/25W/r382007|r382336|r382696` then redirecting to `clubs.usu.edu.au/CSS/rsvp_boot?id=...`).

### Poster and Simulated Message Analysis (Problem Name Orientation)

On the "General Meeting 01!" poster publication, the system detected a simulated conversation snippet (mock message). The final two lines of conversation constitute the exploitation key set:

```text
u seriously care more about a club than the premium reserve??
come for the server juiceeeee
```

The second conversation line ("server juice") directly decodes the challenge's nomenclature. The first conversation line ("premium reserve") carries the flag's content.

*(Archived image of the message conversation in the poster is attached at `files/sms_bubble.png`)*

### Analyzing the Flag-containing Comment Structure

Following an exhaustive search through 27 posts, the system discovered a comment belonging to the post with identifier `DWL9S-wkyJT` directly replying with the flag code:

```text
harrysalvesen  8h
CSSCTF{premiumreserve}
11 likes
Reply
```

The comment displays the raw plaintext code, requiring no reverse translation, and using no steganography techniques. The original image of this comment is digitally archived at `files/comment_catch.png`.

## Exploitation Chain

**Step 1 - Mine semantics via image publications.** 
Build a contact sheet combining all 25 extracted publications and perform a visual review. On the poster identifier `DWL9S-wkyJT` ("General Meeting 01!" event), the simulated message structure exposes two core data lines:

```text
u seriously care more about a club than the premium reserve??
come for the server juiceeeee
```

Assessment: The phrase "premium reserve" is the core component making up the flag. The phrase "server juice" designates an intimate link with the challenge's title.

*(Detailed illustration of the message position on the poster: `analysis/sms_bubbles.jpg`)*

**Step 2 - Scan the public comment network.** 
In the previous inspection cycle, by solely focusing on the pinned post's comment thread resulting in 0 comments, the system temporarily bypassed this data space. However, reviewing the comment thread of post `DWL9S-wkyJT` yields the original display result:

```text
harrysalvesen  8h
CSSCTF{premiumreserve}
11 likes  Reply
```

The flag data is placed out in the open, undergoing no encryption or obfuscation processes. Notably, the caption of this post bears an "Edited" status. The alteration was executed to append a concluding message: "We hope to see you there; BYO water. 💧". This supplementary detail constructs a unified logical chain with the "server cooling water" (server juice) concept implied in the poster image.

**Step 3 - Validate the account identity.** 
The account disseminating the comment belongs to `harrysalvesen`. Through system cross-referencing, this identity perfectly aligns with the `hsalvesen` / `vesen.app` account that appeared in clues during the pre-reconnaissance phase. The Instagram Bio link of this personal account points straight to `vesen.app`, providing a complete explanation for the origin of the UTM tracking parameter `link_in_bio` that the system traced.

**Step 4 - Verification stage.** 
The collected data sequence completely complies with the standard `CSSCTF{...}` format per the technical specifications. This data exists verbatim in the post's source code content, authenticated as published by an account associated with the event author, and has been acknowledged by the community with 11 likes. Rule number 6 in the opening document imposes a case-sensitive mechanism for the flag; the obtained string structure (`premiumreserve`) strictly adheres to a fully lowercase format.

## Flag

Executing the automated retrieval command:

```bash
$ python exploit.py
```

Outputting evidence extracted directly from the stored JSON data block (Including description data, comment content, URL links have been redacted for security):

```text
Data source: analysis/evidence.json  (Post identifier DWL9S-wkyJT)

--- Extracted caption and comment union (Sanitized) ---
...
We hope to see you there; BYO water. 💧
See translation
harrysalvesen
8h
CSSCTF{premiumreserve}
11 likes
Reply

Analyzed flag: ['CSSCTF{premiumreserve}']

=== FLAG ===
CSSCTF{premiumreserve}
```

Result:
```text
CSSCTF{premiumreserve}
```

## Reproduce

Because the security architecture of the Instagram platform requires a valid login session to display comment threads, the information gathering process is configured to execute directly via the browser's Console during a logged-in session. The execution script is integrated within the `BROWSER` variable belonging to the `exploit.py` file. The automated script performs scrolling operations through 27 posts, utilizes the `fetch` function to load the source code of each page, and applies the `grep CSSCTF\{...\}` filter to scan. The scanning process is optimized with `sleep` intervals to circumvent the platform's automated action blocking mechanisms.

```bash
python exploit.py
```

The collected evidence data block is preserved at `analysis/evidence.json`. This data has been sanitized, retaining only the description and comment text fields; all URL links containing CDN authentication signatures have been redacted to prevent identity backtracking behavior and protect information related to personal accounts.

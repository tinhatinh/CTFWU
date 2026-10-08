# Server Juice - OSINT (Beginner)

**Flag:** `CSSCTF{premiumreserve}`

## Solution

The problem description suggests following the event's social media channels to find clues.

1. Search and navigate to the official Instagram page of the event organizers: `@cybersecuritysydney`.

   ![Official Instagram page](files/ig_page.png){: data-proofer-ignore="true" }

2. Among the posts on the page, find the post titled "General Meeting 01!".
3. Read the comments section of this post, and we will find a public comment from the user `harrysalvesen` directly containing the flag.

   ![Flag comment](files/flag_comment.png){: data-proofer-ignore="true" }

```text
harrysalvesen  8h
CSSCTF{premiumreserve}
11 likes
Reply
```

## Result

```text
CSSCTF{premiumreserve}
```

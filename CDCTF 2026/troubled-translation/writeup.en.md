# Troubled Translation - OSINT (479 points)

**Flag:** `cdctf{McDonald's_in_Chicago}` · **Files:** `files/translation.zip`, 19609739 bytes, sha256 `b4e5df962599ce981bc05a8d1fd9e3d007f9f74a55b305f58537540eff51e10b`

## Challenge

Bob Burke (`bubu77`) was accidentally added to a Chatterly group and photographed its Chinese conversation. Translate the messages to identify the business and city of the next target. The required format is `cdctf{Business_in_City}`; the original description is in `de.md`.

## Analysis

The ZIP contains five JPEG photographs of a screen. Chronological reading order is 5 → 4 → 3 → 2 → 1, with overlapping messages. Read and translate the conversation directly from the photographs.

## Approaches tried

1. **Removing the apostrophe from the business name:** `cdctf{McDonalds_in_Chicago}` was rejected twice according to the saved submission table. This eliminates that string; it does not establish that the business or city is wrong.
2. **Finding a public solution:** searches for the challenge title and Chatterly produced no useful result during the session. Analysis returned to the photographs.

## Solution

**Step 1 - Read the city identification.** Image 4 contains a location correction at 9:20:

| Original | Translation |
| --- | --- |
| 192.0.2.14是一个在美国的餐馆 | 192.0.2.14 is a restaurant in the US. |
| 192.0.2.87是一个德国商业 | 192.0.2.87 is a German business. |
| 不对，是一个芝加哥的麦当劳 | No, it is a McDonald’s in Chicago. |

![Chicago identification](files/translation/translation_4.jpg)

**Step 2 - Cross-check the target discussion.** In image 2 at 9:33, Nanfeng says the previous target still seems best. At 9:35, Qixi asks “那个？麦当劳？” — “Which one? McDonald’s?”. This supports the inference that the target is McDonald’s in Chicago; the final flag value is saved in `flag.txt`.

![McDonald’s mentioned again](files/translation/translation_2.jpg)

**Step 3 - Check the context.** Image 1 mentions `bubu778`, followed by “把八给忘记掉了” — “You forgot the eight”. This explains the mistaken invitation of Bob (`bubu77`). It does not determine flag spelling.

## Result

The string without the apostrophe was rejected:

```text
cdctf{McDonalds_in_Chicago}
```

The correct flag preserves the ASCII apostrophe in the brand name:

```text
cdctf{McDonald's_in_Chicago}
```

The flag is saved in `flag.txt`. The record establishes 4 October 2026, without an exact solve time.

## Reproduce

```powershell
python exploit.py files/translation.zip
```

The script lists and extracts the images into `analysis/extracted/`. Read them in the order described above and compare the quoted messages; the script does not translate automatically or print a guessed flag.

# Dog Whistle — Hardware (Insane)

```
Dog Whistle
insane
Docker
Hardware
991 Points

Aria takes orders it can hear, and the equalizer is the only guard the vendor left
you. Lately it keeps obeying instructions nobody in the room ever gave.

Get it to give up the flag it keeps in firmware.

Objectives 0/1
Files dog_whistle.zip 12.9 KB
Instance Running
nc pwn.h7tex.com 40918
Time left 59m 48s
Submit Flag H7CTF{...}
```

## File trong bundle

```
aria                   18488 B  ELF x86-64, PIE, động, stripped (firmware r7.2)
SPEC.md                 2920 B  mô tả giao tiếp âm học
eq.cfg                   151 B  cấu hình EQ, all gain 0 dB (flat)
reference_ping.wav     45548 B  một capture mẫu, đã decode ra A5 5A 02 10 00 12
```

sha256 `aria` = `7d00b14694517517...`, `reference_ping.wav` = `b713368b38cdded1...`.

## Định dạng flag

`H7CTF{...}` theo đúng chữ trên thẻ đề.

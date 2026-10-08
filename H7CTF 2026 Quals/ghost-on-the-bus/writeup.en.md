# Ghost on the Bus - Hardware (Medium)

**Flag:** `H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}`
**Instance:** `https://web-c2656e4339a3659c.web.h7tex.com`
**Files:** `capture.vcd` (44626 B, 8 logic channels, timescale 1 ns, 29.79 ms)

## Challenge

A logic analyzer was clipped onto the "NoiseGate" board and everything was recorded while it booted. The device puts its provisioning key out during the wake-up routine, but "never says the whole thing in any one place". The key has to be recovered from the recording itself.

## Analysis

The index page gives the format and the channel list:

```
8-channel logic capture of the device boot (2 MHz). Open in PulseView / sigrok.
Channels: UART_TX, SCL, SDA, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS, AUX
```

The VCD is text, so plain Python parses it; no sigrok needed. The first task was to measure the cadence from a histogram of transition gaps (`analysis/explore_vcd.py`), because the challenge states no baud rate anywhere:

```
UART_TX   transitions=1685   gap hist: (8500,1043) (17000,376) (25500,124) ...   -> bit = 8500 ns
SCL       transitions=795    gap hist: (5000,441) (7500,351)                     -> I2C 80 kHz
SDA       transitions=197    gap hist: (12500,92) (25000,28) (37500,21)          -> multiple of SCL
SPI_CLK   transitions=753    gap hist: (1000,751)                                -> 500 kHz, idle low (CPOL=0)
SPI_CS    transitions=3      low 22984000..23738000 ns = 754 us = 376 clock      -> 1 transaction, 47 byte
AUX       transitions=1                                                                -> luôn mức 1, kênh chết
```

8500 ns/bit is 117650 baud, exactly 2 MHz / 17 samples, matching the logic cadence the index page publishes.

## Solution

### Step 1: the UART is the datasheet

Decoding `UART_TX` in 8N1 form, detecting a start bit at every falling edge and then majority-voting at bit centres (`level(sym, start + 8500*(1.5+b))`):

```
[boot] NoiseGate bootloader v2.1
[prov] reading key material...
[prov]   part A <- SPI flash READ(0x03) @ 0x001A00, 43 bytes
[prov]   part B <- I2C EEPROM 0x50 (read), 43 bytes
[prov]   provisioning_key = part_A XOR part_B
[prov] key installed. continuing boot.
[boot] done.
```

284 characters, 0 characters with a bad stop bit: a drifting bit clock could not produce a result this clean. The log states explicitly that the combining operation is XOR and describes each operand with exactly the protocols of the two remaining buses.

### Step 2: part A from the SPI flash

CS is pulled low once, 376 clocks; MOSI/MISO sampled on the rising edge of CLK (CPOL=0, CPHA=0):

```
MOSI: 03 00 1a 00 ...        <- opcode 0x03 (READ), address 0x001A00, khớp log
MISO: 00 00 00 00 | 75 17 b3 b1 13 b5 6c 39 ... 7b 2b a1
       (4 byte pha lệnh)       43 byte dữ liệu = part A
```

### Step 3: part B from the I2C EEPROM

START/STOP are detected by SDA changing state while SCL is held high; data sampled on the rising edge of SCL (+300 ns):

```
frame t=23741500  44 bytes: a1 ACK 3d ACK 20 ACK ... 18 ACK dc NACK
slave 0x50 read -> 43 data bytes = part B
```

The first byte `0xA1 = 0x50 << 1 | 1` confirms this really is the read phase of the EEPROM 0x50 the log refers to; the NACK on the last byte is exactly the expected behaviour of a master reading the final byte and stopping.

### Step 4: XOR

```python
key = bytes(a ^ b for a, b in zip(part_a, part_b))
```

```
[*] b'H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}'
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

## Result
```
$ python solve_bus.py files/capture.vcd
[+] FLAG: H7CTF{10d9b516-d19b-4895-9634-45b27a7591c3}
```

Three independent pieces of evidence that the combination is correct: both parts are exactly 43 bytes as the log claims; the result matches the `H7CTF{uuid}` shape with a UUID in 8-4-4-4-12 form; and each bus's metadata (opcode `0x03`, address `0x001A00`, slave `0x50` + read bit) was confirmed by the log before decoding.

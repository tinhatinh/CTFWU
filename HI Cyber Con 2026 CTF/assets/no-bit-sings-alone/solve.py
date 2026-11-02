#!/usr/bin/env python3
"""Recover the flag from suspicious.wav or its ZIP. Requires numpy, pycryptodome."""
import argparse
import hashlib
import io
import re
import wave
import zipfile
from pathlib import Path

import numpy as np
from Crypto.Cipher import AES

# Transcribed from the introductory spectrogram; see the existing analysis.
NONCE = bytes.fromhex('99CB9C49E4C83527CE6F89D9')
SEALED = bytes.fromhex(
    '8A845BA500DE25B749F1FF63CCFF'
    '9D2D9FD8D2614E19BCA42CC7E438'
    'B31407AE896311C3AADCF9327610'
    '478444A09EF6FE3650DF7EBEC3B7'
    '1FF18CF0EB728DBFA791B7485D76'
    '7172AE8493A8715210B5'
)


def load_wav(path):
    data = Path(path).read_bytes()
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith('.wav')]
            if len(names) != 1:
                raise ValueError('Provide the original challenge ZIP or suspicious.wav')
            data = archive.read(names[0])
    with wave.open(io.BytesIO(data)) as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (2, 2, 44100)
        samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype='<i2').reshape(-1, 2)
    return data, samples


def solve(path):
    wav, samples = load_wav(path)
    block_size, first_block, count = 4096, 585, 58
    blocks = samples[first_block * block_size:(first_block + count) * block_size]
    blocks = blocks.reshape(count, block_size, 2)
    spectrum = np.abs(np.fft.rfft(blocks[:, :, 1], axis=1))
    bins = spectrum[:, 1200:1900].argmax(axis=1) + 1200
    assert np.all(bins & 1)  # Each stride is coprime to 4096.

    # The right-channel FFT bin controls the walk in the left channel.
    j = np.arange(31)[None, :]
    positions = ((j + 1) * bins[:, None]) % block_size
    selected = blocks[np.arange(count)[:, None], positions, 0] & 1

    # Hamming parity-check columns, cyclically shifted by the bin index.
    columns = ((j - bins[:, None]) % 31) + 1
    syndromes = np.bitwise_xor.reduce(selected * columns, axis=1)
    bits = ((syndromes[:, None] >> np.arange(4, -1, -1)) & 1).ravel()
    assert np.all(bits[288:] == 0)
    values = (bits[:288].reshape(32, 9) @ (1 << np.arange(8, -1, -1))).tolist()
    assert all(0 <= v < 257 for v in values)

    # Inverse 32-point NTT in GF(257), primitive root 136 = 3**8 mod 257.
    modulus, n, root = 257, 32, 136
    assert pow(root, n, modulus) == 1 and pow(root, n // 2, modulus) != 1
    key_values = [
        sum(v * pow(root, (-j * k) % n, modulus) for k, v in enumerate(values))
        * pow(n, -1, modulus) % modulus
        for j in range(n)
    ]
    key = bytes(key_values)
    # Independent consistency check of the forward transform.
    assert values == [
        sum(v * pow(root, (j * k) % n, modulus) for j, v in enumerate(key)) % modulus
        for k in range(n)
    ]
    plaintext = AES.new(key, AES.MODE_GCM, nonce=NONCE).decrypt_and_verify(SEALED[:-16], SEALED[-16:])
    # Authenticated plaintext is a big-endian length, flag, then trailing data.
    length = int.from_bytes(plaintext[:2], 'big')
    flag = plaintext[2:2 + length]
    assert re.fullmatch(rb'hiCTF\{[^}]+\}', flag)
    print('WAV SHA-256:', hashlib.sha256(wav).hexdigest())
    print('FFT bins:', bins.tolist())
    print('GF(257) values:', values)
    print('AES key:', key.hex())
    print('AES-GCM tag: VERIFIED')
    print('Flag:', flag.decode('ascii'))
    return flag.decode('ascii')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='suspicious.wav or original no-bit-sings-alone.zip')
    solve(parser.parse_args().input)

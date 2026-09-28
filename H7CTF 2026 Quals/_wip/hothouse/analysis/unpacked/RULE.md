# Hothouse Control Link

`hothouse` is the firmware control service for a cellular-automaton coprocessor.
The fabric is the only thing the embedded core will execute, and the fabric runs
whatever the lattice grows into. You do not get to write bytes into it. You grow
them.

This note documents the wire protocol and the lattice geometry. Everything about
how the lattice actually settles is in the binary.

## The fabric

The executable fabric is a 32 row by 32 column bit lattice, packed little-endian
into a 128 byte buffer:

    cell (r, c)  ->  bit (c & 7) of byte  r*4 + (c >> 3)

Rows are 0..31 top to bottom, columns 0..31 left to right. Cells outside the
lattice are dead.

## Commands

One connection per instance. Line based, one command per line.

    SEED r c      set seed cell (r, c) live
    INCUBATE      settle the seed into the fabric under the growth rule
    PROBE r c     report the settling temperature of a fabric cell
    RENDER        print the current fabric as a picture
    FIRE          execute the settled fabric on the core

`INCUBATE` grows the current seed lattice into the fabric by running the device
growth rule for a fixed number of generations against a fixed substrate. It is
deterministic. `PROBE` reads back one byte so operators can watch the bake.
`FIRE` transfers control to the fabric and can only be used once.

The core will not run anything that is not microcode, and there is no shell.

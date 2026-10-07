# tests/

The permanent suite, and where promoted experiments land.

## Two kinds of file

| Kind | Origin | Marker |
| --- | --- | --- |
| Base tests | Written by hand. Deliberately thin | none |
| Promoted regression tests | Copied **byte-for-byte** from `.falsify/experiments/` by the human-run `promote` job | `@pytest.mark.promoted` |

A promoted file's hash is recorded in the certificate at promotion time. The
`certificate` job verifies the file is present at the MR head with that exact
hash — a remedy-accepted finding does not resolve without it.

**Do not edit a promoted file.** Its hash is evidence. If it needs to change,
the change is a new experiment with a new digest and a new ruling.

## Why the base suite is thin

Falsify is not a replacement for the base test suite. The base suite covering
everything would defeat the demonstration: the point is that experiments find
what it does not cover, and that accepted findings get promoted in here
permanently so they cannot come back unnoticed.

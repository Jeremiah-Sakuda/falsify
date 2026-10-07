# Demo video — shot script

Under 3:00. YouTube, public, captions on. No third-party trademarks, no
licensed music. Judges are not required to watch past 3:00, so nothing
load-bearing happens after 2:40.

A thin nine-stage indicator (plan, create, verify, package, secure, release,
configure, monitor, govern) sits in the corner and lights as each stage is
touched. That replaces any narration about package, configure, and govern.

| Time | Beat | On screen | Narration |
| --- | --- | --- | --- |
| 0:00–0:12 | Hook | Title card; audience named: solo builders and small teams with no second reviewer | "If you ship alone, nobody tries to break your code before it goes out. Falsify does, and it is only allowed to speak in failing tests. No red test, no accusation." |
| 0:12–1:05 | **1. The refutation** | An MR with one of the lead defects. Duo Code Review's **actual** comment, shown as recorded. Falsify posts five conjectures → human approves → pipeline → one goes red. The generated test on screen for a full 4 seconds. The ledger line: FAIL, FAIL on head; PASS on base | "That is the product." |
| 1:05–1:50 | **2. The ruling and the test** | **First the contest, in full (8–10s):** the Advocate argues an experiment asserted the wrong requirement; the human reads the test, replies `falsify: sustain`; the strike stays in the certificate. **Then the remedy:** suggestion on the exact lines → Apply → green → human runs `promote` → the file lands in `tests/` with its hash | "The review ends with a test that protects the next change." |
| 1:50–2:05 | **3. Prevented return** | A follow-up change quietly reintroduces the deadline bug. The permanent suite goes red on the promoted test | "Found it, fixed it, kept it out." |
| 2:05–2:40 | **4. The motion** | Caption: *a separately disclosed, workload-dependent case; the ten-minute watch window is time-compressed.* Human runs staging, approves and starts production. prod-watch verifies the live digest, samples under replayed load, p95 crosses the committed threshold. Monitor flow files an incident linked to the certificate. Human replies | "The incident says it is an observation in a window, not proof of cause." |
| 2:40–2:58 | Close | The evaluation table cut to **one useful result and one honest limitation** — recall on the held-out half, and the number of experiments struck — held long enough to read. Then the certificate full screen. Then the nine-stage strip as a 2-second montage | "Our AI must bring evidence, you can reject its interpretation, and when you accept the finding the evidence becomes a test." |

## Hard rules

- **The contest gets real time.** The agent being wrong, and the human's
  rejection staying in the record, is the clearest demonstration of why the
  design exists. Do not cut it to 3 seconds to make room for something
  flashier.
- **Duo's comment is shown as recorded**, whatever it said. Nothing about
  what vanilla review catches or misses is scripted before it is measured.
- **The lead defect is whichever one the measured comparison supports.** Not
  chosen in advance.
- **The seeded defects are disclosed in a caption during Beat 1.**
- **Record Beat 3 twice.** It is the strongest proof of promotion and costs
  fifteen seconds; losing it to a bad take is unacceptable.

## Production notes

- 1080p screen recordings, cursor visible. No face cam needed.
- Captions burned in or as a track, but on.
- Live experiments against staging are rate-limited and the thresholds are
  committed to `.falsify/thresholds.yaml`, so the motion in Beat 4 is
  reproducible on the day of filming.

## Checklist

- [ ] Beat 1 recorded
- [ ] Beat 2 recorded — contest at full length
- [ ] Beat 3 recorded (take 1)
- [ ] Beat 3 recorded (take 2)
- [ ] Beat 4 recorded, watch window time-compressed with the caption
- [ ] Close recorded with real numbers
- [ ] Nine-stage indicator overlaid
- [ ] Captions on
- [ ] Under 2:50
- [ ] Uploaded, public, no trademarks or licensed music

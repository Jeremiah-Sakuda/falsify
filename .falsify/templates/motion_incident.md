# Operational motion · MR !{{ mr_iid }}

**{{ motion.metric }}** crossed its committed threshold in the production
watch window.

| | |
| --- | --- |
| Metric | `{{ motion.metric }}` |
| Threshold | `{{ motion.threshold }}` (from `.falsify/thresholds.yaml`) |
| Observed | `{{ motion.observed }}` |
| Revision digest | `{{ motion.revision_digest }}` (verified against `events.md`) |
| Window | {{ window_start }} → {{ window_end }} ({{ duration_s }}s) |
| Certificate | [`ledger/mr-{{ mr_iid }}/certificate.md`]({{ certificate_url }}) |

## Requests that reproduced it

{% for rid in motion.request_ids %}
- `{{ rid }}`
{% endfor %}

## Recommendation

**{{ motion.recommendation }}**

## Caveat

> This is an observation in a ten-minute window following the deploy. It
> supports a response. It does not by itself attribute cause to this merge
> request.

---

**Gate 4.** Reply `falsify: rollback` to run the rollback job, or
`falsify: deny` to record the denial and close this incident.

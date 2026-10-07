## Falsifiable claims · {{ claims_version }}

Rewritten from this issue's acceptance criteria. Each claim has a condition a
test could fail.

{% for c in claims %}
**{{ c.id }}** — {{ c.condition }}
<sub>from: "{{ c.criterion }}"</sub>
{% endfor %}

{% if bounced %}
### Bounced as unfalsifiable

These have no testable condition yet. One question each — answer it and I will
rewrite it as a claim. I will not invent the number.

{% for b in bounced %}
- "{{ b.criterion }}" → **{{ b.question }}**
{% endfor %}
{% endif %}

---

**Gate 1.** Edit anything above, then reply `falsify: claims approved {{ claims_version }}`
to authorize. Experiments will target this exact version; a new version
invalidates Gate 2.

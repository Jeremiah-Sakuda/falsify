## Falsify · trial summary

head `{{ head_sha }}` · base `{{ base_sha }}` · {{ claims_version }} · pipeline [{{ pipeline_id }}]({{ pipeline_url }})

| ID | Kind | Head | Base | Status |
| --- | --- | --- | --- | --- |
{% for x in experiments -%}
| {{ x.id }} | {{ x.kind }} | {{ x.head_runs | join(", ") }} | {{ x.base }} | {{ x.resolution or "**open**" }} |
{% endfor %}

**{{ counts.refutations }}** functional refutation(s) ·
**{{ counts.contract_failures }}** contract failure(s) ·
**{{ counts.corroborations }}** corroboration(s) ·
**{{ counts.errors }}** error(s) ·
**{{ counts.struck }}** struck ·
**{{ counts.security }}** security finding(s)

Unsupported functional findings: **0**.

{% if open_findings %}
### Open — merge is blocked

{% for f in open_findings %}
- **{{ f.id }}** {{ f.reason }}
{% endfor %}

A remedy-accepted finding resolves only when the rerun is green **and** the
promoted file is present at the head with its recorded hash. Run the `promote`
job for each.
{% else %}
All findings resolved. The `certificate` job is the merge gate.
{% endif %}

<sub>A corroboration is a survived attempt, not proof. A contract failure
targets code with no base version, so it indicates a possible violation of an
approved claim, not a regression.</sub>

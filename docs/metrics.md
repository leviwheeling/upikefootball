# Metric registry and methodology

No advanced metric is calculated in Phase 1 because the initial schema intentionally retains only game identities, scores, attendance, and player identities. The UI's win rate is the only derived display value.

| Metric | Category | Meaning | Formula | Required fields | Minimum sample | Classification | Version | Limitation |
|---|---|---|---|---|---:|---|---|---|
| Win rate | Team results | Share of completed indexed games won | wins / games with observed final result | game result | 1 game | Calculated | `team-win-rate-v1` | Reflects imported games only; not necessarily full history |

Future definitions are stored before values are exposed. A metric is disabled—not estimated—when required fields or minimum sample are absent.

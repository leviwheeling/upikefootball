# Metric registry and methodology

The 2025 play analytics join the supplied coaching export to official NAIA gamebooks. Every row retains its alignment confidence and official source text when matched. These metrics describe the supplied sample; they do not assert causal impact.

| Metric | Category | Meaning | Formula | Required fields | Minimum sample | Classification | Version | Limitation |
|---|---|---|---|---|---:|---|---|---|
| Win rate | Team results | Share of completed indexed games won | wins / games with observed final result | game result | 1 game | Calculated | `team-win-rate-v1` | Reflects imported games only; not necessarily full history |
| Play success | Play efficiency | Whether a snap gained the required share of yards-to-go | 1st: gain >= 50% of distance; 2nd: >= 70%; 3rd/4th: conversion | down, distance, tagged gain, result | 1 graded snap | Calculated | `play-success-v1` | Penalties, timeouts, no-plays, and rows missing required fields are excluded |
| Explosive play | Play efficiency | High-yardage run or completed pass | run gain >= 10 yards; completed pass gain >= 15 yards | play type, result, tagged gain | 1 graded snap | Calculated | `explosive-play-v1` | Uses coaching-export gain when linked gamebook gain differs |
| Negative play | Play efficiency | Snap with clear adverse yardage or ball-security result | gain < 0, sack, interception, or fumble-tagged event | result, tagged gain | 1 graded snap | Calculated | `negative-play-v1` | Fumble lost is not inferred when possession is not established |
| Qualified call efficiency | Play-call evaluation | Success and yardage split for a named call | successful graded snaps / all graded snaps in call | play call, success, tagged gain | 8 graded snaps | Calculated | `call-efficiency-v1` | Association only; opponent, personnel, and game state are not controlled |
| Qualified formation efficiency | Formation evaluation | Success and yardage split for a named formation | successful graded snaps / all graded snaps in formation | formation, success, tagged gain | 12 graded snaps | Calculated | `formation-efficiency-v1` | Association only; formation tags may encode different personnel or calls |
| Scoreboard points lost | Game outcome | Actual final-score deficit in a loss | max(0, opponent points - UPIKE points) | final score | 1 game | Observed | `score-deficit-v1` | Not an estimate of points attributable to any individual play |

Metrics are disabled—not estimated—when required fields or minimum samples are absent. The UI exposes the method and source-link coverage next to the analytics.

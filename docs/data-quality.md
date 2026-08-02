# Data-quality methodology

Completeness is independent from correctness. A record can be accurately parsed but incomplete because its source omits play-by-play, attendance, position, or situational fields.

Initial validation checks identifiers, nonnegative scores, date parsing, score shape, and duplicate source keys. Later checks reconcile quarter scoring to finals, team to player totals, completions to attempts, makes to attempts, fumbles lost to fumbles, play counts, and cross-source disagreements.

Identity matching remains conservative: normalized names support search and candidate generation only. A canonical merge requires corroborating season, roster ID, jersey, position, biography, or explicit admin action.

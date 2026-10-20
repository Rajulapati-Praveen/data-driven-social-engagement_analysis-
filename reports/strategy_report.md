# Strategy Report: The Data-Driven Social Engagement Initiative

## 1. Executive summary
- Analysed **219 posts** (1,219,848 views, 13,741 followers gained).
- **Most viral topic:** Loneliness (Viral Coefficient 23.95, 95% CI 22.62-25.27). **Least viral:** Dating (16.64).
- Share of comments tagged *Relatable* is weakly correlated with virality (r = 0.20).
- 2 content variables showed a statistically significant effect on virality.

## 2. Which topics drive the most connection?
| Rank | Topic | Posts | Viral Coefficient | Avg shares | Avg saves | Avg followers gained |
|---|---|---|---|---|---|---|
| 1 | Loneliness | 22 | 23.95 | 118 | 187 | 86 |
| 2 | Social Anxiety | 38 | 22.98 | 105 | 194 | 70 |
| 3 | Overthinking | 26 | 22.39 | 106 | 189 | 68 |
| 4 | Burnout | 25 | 21.13 | 79 | 144 | 55 |
| 5 | Friendship | 30 | 19.41 | 92 | 141 | 63 |
| 6 | Body Image | 33 | 19.18 | 75 | 125 | 48 |
| 7 | Career Confusion | 20 | 18.30 | 86 | 156 | 73 |
| 8 | Dating | 25 | 16.64 | 67 | 128 | 43 |

## 3. A/B testing findings (on Viral Coefficient)
- **format**: best = **Short** (Long (18.886) vs Short (21.703)); p = 0.0000, effect size: medium.
- **caption_style**: best = **Listicle** (Listicle (21.501) vs Question (19.887) vs Story (20.102)); p = 0.0321, effect size: n/a (3+ groups).
- No reliable difference found for: hook_type, is_evening, day_of_week, time_slot. Don't over-optimise these.

## 4. Recommended content plan for next week
| # | Topic | Format | Hook | Caption | Length (s) | Post at | Predicted VC |
|---|---|---|---|---|---|---|---|
| 1 | Social Anxiety | Short | Text | Listicle | 25 | 21:00 | 27.82 |
| 2 | Loneliness | Short | Text | Listicle | 25 | 21:00 | 27.44 |
| 3 | Overthinking | Short | Text | Listicle | 25 | 21:00 | 27.10 |
| 4 | Burnout | Short | Text | Listicle | 25 | 21:00 | 25.90 |
| 5 | Friendship | Short | Text | Listicle | 25 | 21:00 | 23.92 |

## 5. Emerging 'relatable struggles' (trend forecast)
- **friend breakup** - Rising (Emerging): momentum +18%, forecast interest in 4 weeks = 72/100.
- **burnout recovery** - Stable: momentum +4%, forecast interest in 4 weeks = 64/100.
- **loneliness in your 20s** - Rising: momentum +3%, forecast interest in 4 weeks = 79/100.
- **social anxiety tips** - Stable: momentum -1%, forecast interest in 4 weeks = 49/100.

## 6. Limitations & next steps
- Results come from observational data: effects of format/time may be confounded by topic. Run true A/B tests (same idea, two versions) to confirm.
- Replace the simulated dataset with real account data and re-run the pipeline.
- Re-train the sentiment model on ~500 hand-labelled real comments for best accuracy.
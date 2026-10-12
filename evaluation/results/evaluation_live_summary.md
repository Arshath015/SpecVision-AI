# Evaluation summary -- mode: live (GENUINE live LLM run)

Cases: 16  |  Successful: 16  |  Failed: 0

## Extraction -- categorical fields (accuracy on cases with a known gold value)
| Field | Accuracy | N | Unknown-abstain rate | Unknown N | Fabricated |
|---|---|---|---|---|---|
| metal_type | 1.0 | 12 | 1.0 | 2 | 0 |
| metal_purity | 0.8 | 10 | 1.0 | 4 | 0 |
| metal_color | 1.0 | 5 | 0.667 | 9 | 3 |
| design_category | 0.714 | 7 | 1.0 | 7 | 0 |
| setting_type | 1.0 | 4 | 1.0 | 10 | 0 |
| center_stone_type | 1.0 | 12 | 1.0 | 2 | 0 |
| center_stone_shape | 1.0 | 9 | 0.8 | 5 | 1 |

## Extraction -- numeric fields (tolerance-based)
| Field | Accuracy | N | Unknown-abstain rate | Unknown N | Fabricated |
|---|---|---|---|---|---|
| center_stone_carat | 1.0 | 3 | 1.0 | 11 | 0 |
| side_stone_count_total | 1.0 | 4 | 1.0 | 10 | 0 |
| band_width_mm | 0.5 | 2 | 1.0 | 12 | 0 |
| ring_size_us | None | 0 | 1.0 | 14 | 0 |

## Inventory matching
- Top-1 hit rate: 1.0 (n=1)
- Top-3 hit rate: 1.0 (n=1)
- No-reliable-match handling accuracy: 1.0 (n=8)

## Computer vision
- MAE (visible stone count): 16.71 over 7 image(s)
- Unavailable (excluded from MAE): 0

## Review behavior
- Flag rate: 0.875  Precision: 0.929  Recall: 1.0
- TP=13 FP=1 FN=0 TN=2
- False positive cases: ['case-08']
- False negative cases: []

## Operational
- Mean latency: 1621.21ms  Median: 1690.26ms  P95: 2280.26ms
- Extraction method distribution: {'llm_live': 13, 'llm_repaired': 1, 'safe_degradation': 1, 'llm_live_fallback_model': 1}
- Total recovery events: 10
- Live model calls: 15  Estimated cost: $0.0
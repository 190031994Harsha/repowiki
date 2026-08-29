# Evaluation Report

Generated: 2026-08-29 05:56 UTC
Model: deepseek/deepseek-chat-v3-0324 (temp 0) | 10 repos x 2 modes | parallel x4


## Summary

| Repo | Mode | Pages | Citation validity | w/ line ranges | Module cov | Symbol cov | Cost | Wall s |
|---|---|---|---|---|---|---|---|---|
| anyio | advanced | 14 | 0.91 | 0.62 | 0.75 | 0.29 | $0.0587 | 406.2 |
| anyio | baseline | 11 | 1.00 | 0.00 | 1.00 | 0.20 | $0.0103 | 166.3 |
| click | advanced | 21 | 0.96 | 0.65 | 1.00 | 0.40 | $0.0593 | 653.5 |
| click | baseline | 19 | 1.00 | 0.00 | 1.00 | 0.35 | $0.0142 | 227.6 |
| colorama | advanced | 9 | 0.82 | 0.59 | 1.00 | 0.85 | $0.0241 | 271.2 |
| colorama | baseline | 6 | 1.00 | 0.00 | 1.00 | 0.80 | $0.0045 | 74.4 |
| fastapi | advanced | 7 | 0.97 | 0.73 | 1.00 | 0.92 | $0.0064 | 117.4 |
| fastapi | baseline | 4 | 0.84 | 0.00 | 1.00 | 0.62 | $0.0016 | 44.4 |
| flask | advanced | 16 | 0.88 | 0.60 | 0.90 | 0.27 | $0.0492 | 523.5 |
| flask | baseline | 23 | 0.98 | 0.00 | 1.00 | 0.31 | $0.0171 | 284.7 |
| httpx | advanced | 11 | 1.00 | 0.77 | 0.80 | 0.28 | $0.0388 | 321.8 |
| httpx | baseline | 8 | 1.00 | 0.00 | 1.00 | 0.14 | $0.0076 | 125.6 |
| jsonschema | advanced | 13 | 0.97 | 0.71 | 1.00 | 0.54 | $0.0348 | 330.1 |
| jsonschema | baseline | 10 | 0.97 | 0.00 | 1.00 | 0.28 | $0.0075 | 123.0 |
| packaging | advanced | 14 | 0.97 | 0.60 | 1.00 | 0.13 | $0.0560 | 499.5 |
| packaging | baseline | 11 | 1.00 | 0.00 | 1.00 | 0.10 | $0.0097 | 165.4 |
| records | advanced | 9 | 0.99 | 0.76 | 1.00 | 0.85 | $0.0106 | 156.3 |
| records | baseline | 6 | 1.00 | 0.00 | 1.00 | 0.69 | $0.0028 | 67.4 |
| requests | advanced | 11 | 0.81 | 0.52 | 1.00 | 0.35 | $0.0310 | 288.9 |
| requests | baseline | 9 | 0.99 | 0.00 | 1.00 | 0.27 | $0.0061 | 125.6 |

## Baseline vs Advanced


### anyio (120 files, 2521 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.91 | -0.09 |
| Citations w/ line ranges | 0.00 | 0.62 | +0.62 |
| Module coverage | 1.00 | 0.75 | -0.25 |
| Symbol coverage | 0.20 | 0.29 | +0.09 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.31 | 0.43 | +0.12 |
| Pages | 11 | 14 | +3 |
| LLM cost (USD) | $0.0103 | $0.0587 | $+0.0484 |
| Wall time (s) | 166.3 | 406.2 | +240 |

### click (166 files, 1636 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.96 | -0.04 |
| Citations w/ line ranges | 0.00 | 0.65 | +0.65 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.35 | 0.40 | +0.05 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.56 | 0.92 | +0.36 |
| Pages | 19 | 21 | +2 |
| LLM cost (USD) | $0.0142 | $0.0593 | $+0.0451 |
| Wall time (s) | 227.6 | 653.5 | +426 |

### colorama (49 files, 169 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.82 | -0.18 |
| Citations w/ line ranges | 0.00 | 0.59 | +0.59 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.80 | 0.85 | +0.05 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.44 | 0.58 | +0.14 |
| Pages | 6 | 9 | +3 |
| LLM cost (USD) | $0.0045 | $0.0241 | $+0.0196 |
| Wall time (s) | 74.4 | 271.2 | +197 |

### fastapi (3139 files, 16 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.84 | 0.97 | +0.13 |
| Citations w/ line ranges | 0.00 | 0.73 | +0.73 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.62 | 0.92 | +0.31 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.58 | 0.97 | +0.38 |
| Pages | 4 | 7 | +3 |
| LLM cost (USD) | $0.0016 | $0.0064 | $+0.0048 |
| Wall time (s) | 44.4 | 117.4 | +73 |

### flask (236 files, 1425 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.98 | 0.88 | -0.10 |
| Citations w/ line ranges | 0.00 | 0.60 | +0.60 |
| Module coverage | 1.00 | 0.90 | -0.10 |
| Symbol coverage | 0.31 | 0.27 | -0.04 |
| Link health | 1.00 | 0.94 | -0.06 |
| Readability | 0.44 | 0.55 | +0.11 |
| Pages | 23 | 16 | +-7 |
| LLM cost (USD) | $0.0171 | $0.0492 | $+0.0321 |
| Wall time (s) | 284.7 | 523.5 | +239 |

### httpx (125 files, 1249 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 1.00 | -0.00 |
| Citations w/ line ranges | 0.00 | 0.77 | +0.77 |
| Module coverage | 1.00 | 0.80 | -0.20 |
| Symbol coverage | 0.14 | 0.28 | +0.14 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.42 | 0.00 | -0.42 |
| Pages | 8 | 11 | +3 |
| LLM cost (USD) | $0.0076 | $0.0388 | $+0.0312 |
| Wall time (s) | 125.6 | 321.8 | +196 |

### jsonschema (629 files, 780 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.97 | 0.97 | -0.00 |
| Citations w/ line ranges | 0.00 | 0.71 | +0.71 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.28 | 0.54 | +0.26 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.46 | 0.82 | +0.36 |
| Pages | 10 | 13 | +3 |
| LLM cost (USD) | $0.0075 | $0.0348 | $+0.0273 |
| Wall time (s) | 123.0 | 330.1 | +207 |

### packaging (139 files, 2328 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.97 | -0.03 |
| Citations w/ line ranges | 0.00 | 0.60 | +0.60 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.10 | 0.13 | +0.03 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.50 | 0.95 | +0.46 |
| Pages | 11 | 14 | +3 |
| LLM cost (USD) | $0.0097 | $0.0560 | $+0.0463 |
| Wall time (s) | 165.4 | 499.5 | +334 |

### records (21 files, 107 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.99 | -0.01 |
| Citations w/ line ranges | 0.00 | 0.76 | +0.76 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.69 | 0.85 | +0.15 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.59 | 0.66 | +0.07 |
| Pages | 6 | 9 | +3 |
| LLM cost (USD) | $0.0028 | $0.0106 | $+0.0078 |
| Wall time (s) | 67.4 | 156.3 | +89 |

### requests (130 files, 786 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.99 | 0.81 | -0.18 |
| Citations w/ line ranges | 0.00 | 0.52 | +0.52 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.27 | 0.35 | +0.08 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.43 | 0.50 | +0.07 |
| Pages | 9 | 11 | +2 |
| LLM cost (USD) | $0.0061 | $0.0310 | $+0.0249 |
| Wall time (s) | 125.6 | 288.9 | +163 |
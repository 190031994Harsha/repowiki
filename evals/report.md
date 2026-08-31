# Evaluation Report

Generated: 2026-08-31 (final, post judge-panel) | Model: deepseek/deepseek-chat-v3-0324 (temp 0)
12 repos x 2 modes = 24 runs (2 non-Python: logrus=Go, TypeScript-TmLanguage=TS)
Claim-support precision (advanced, sampled): requests 0.80, flask 0.74, click 0.62 — see evals/claim_support*.json


## Summary

| Repo | Mode | Pages | Validity | Depth | Mod cov | Sym cov | Readability | Cost | Wall s |
|---|---|---|---|---|---|---|---|---|---|
| TypeScript-TmLanguage | advanced | 8 | 1.00 | 0.63 | 1.00 | 0.51 | 0.82 | $0.0076 | 127.5 |
| TypeScript-TmLanguage | baseline | 5 | 1.00 | 0.35 | 1.00 | 0.48 | 0.92 | $0.0038 | 78.4 |
| anyio | advanced | 14 | 0.96 | 0.75 | 0.75 | 0.44 | 0.37 | $0.0738 | 664.0 |
| anyio | baseline | 11 | 0.92 | 0.00 | 1.00 | 0.19 | 0.54 | $0.0115 | 218.4 |
| click | advanced | 21 | 0.78 | 0.69 | 1.00 | 0.39 | 0.52 | $0.0791 | 1031.8 |
| click | baseline | 19 | 0.96 | 0.00 | 1.00 | 0.37 | 0.81 | $0.0168 | 306.5 |
| colorama | advanced | 9 | 0.95 | 0.70 | 1.00 | 0.83 | 0.85 | $0.0179 | 270.4 |
| colorama | baseline | 6 | 0.96 | 0.00 | 1.00 | 0.68 | 0.73 | $0.0049 | 118.5 |
| fastapi | advanced | 37 | 0.95 | 0.86 | 0.04 | 0.19 | 0.79 | $0.0974 | 1720.3 |
| fastapi | baseline | 16 | 0.98 | 0.00 | 0.50 | 0.35 | 0.86 | $0.0195 | 271.6 |
| flask | advanced | 19 | 0.97 | 0.77 | 0.90 | 0.36 | 0.30 | $0.0621 | 903.2 |
| flask | baseline | 23 | 0.92 | 0.00 | 1.00 | 0.34 | 0.66 | $0.0201 | 383.2 |
| httpx | advanced | 11 | 0.95 | 0.72 | 0.80 | 0.28 | 0.00 | $0.0413 | 296.3 |
| httpx | baseline | 8 | 1.00 | 0.00 | 1.00 | 0.15 | 0.87 | $0.0091 | 167.0 |
| jsonschema | advanced | 13 | 1.00 | 0.71 | 1.00 | 0.80 | 0.65 | $0.0255 | 289.7 |
| jsonschema | baseline | 10 | 0.87 | 0.00 | 1.00 | 0.28 | 0.53 | $0.0076 | 142.7 |
| logrus | advanced | 12 | 1.00 | 0.00 | 1.00 | 1.00 | 0.94 | $0.0266 | 561.3 |
| logrus | baseline | 9 | 0.68 | 0.04 | 1.00 | 1.00 | 0.78 | $0.0054 | 143.3 |
| packaging | advanced | 14 | 0.99 | 0.73 | 1.00 | 0.13 | 0.00 | $0.0486 | 617.3 |
| packaging | baseline | 11 | 0.90 | 0.00 | 1.00 | 0.09 | 0.66 | $0.0099 | 166.3 |
| records | advanced | 9 | 1.00 | 0.83 | 1.00 | 1.00 | 0.95 | $0.0091 | 158.7 |
| records | baseline | 6 | 0.86 | 0.00 | 1.00 | 0.81 | 0.68 | $0.0031 | 73.8 |
| requests | advanced | 11 | 1.00 | 0.71 | 1.00 | 0.32 | 0.52 | $0.0335 | 358.0 |
| requests | baseline | 9 | 0.88 | 0.00 | 1.00 | 0.22 | 0.66 | $0.0063 | 115.9 |

## Baseline vs Advanced


### TypeScript-TmLanguage (960 files, 776 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 1.00 | +0.00 |
| Citations w/ line ranges | 0.35 | 0.63 | +0.28 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.48 | 0.51 | +0.03 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.92 | 0.82 | -0.10 |
| Pages | 5 | 8 | +3 |
| LLM cost (USD) | $0.0038 | $0.0076 | $+0.0038 |
| Wall time (s) | 78.4 | 127.5 | +49 |

### anyio (120 files, 2521 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.92 | 0.96 | +0.03 |
| Citations w/ line ranges | 0.00 | 0.75 | +0.75 |
| Module coverage | 1.00 | 0.75 | -0.25 |
| Symbol coverage | 0.19 | 0.44 | +0.25 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.54 | 0.37 | -0.17 |
| Pages | 11 | 14 | +3 |
| LLM cost (USD) | $0.0115 | $0.0738 | $+0.0623 |
| Wall time (s) | 218.4 | 664.0 | +446 |

### click (166 files, 1636 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.96 | 0.78 | -0.18 |
| Citations w/ line ranges | 0.00 | 0.69 | +0.69 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.37 | 0.39 | +0.01 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.81 | 0.52 | -0.29 |
| Pages | 19 | 21 | +2 |
| LLM cost (USD) | $0.0168 | $0.0791 | $+0.0623 |
| Wall time (s) | 306.5 | 1031.8 | +725 |

### colorama (49 files, 169 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.96 | 0.95 | -0.01 |
| Citations w/ line ranges | 0.00 | 0.70 | +0.70 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.68 | 0.83 | +0.15 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.73 | 0.85 | +0.12 |
| Pages | 6 | 9 | +3 |
| LLM cost (USD) | $0.0049 | $0.0179 | $+0.0130 |
| Wall time (s) | 118.5 | 270.4 | +152 |

### fastapi (3139 files, 6248 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.98 | 0.95 | -0.03 |
| Citations w/ line ranges | 0.00 | 0.86 | +0.86 |
| Module coverage | 0.50 | 0.04 | -0.45 |
| Symbol coverage | 0.35 | 0.19 | -0.16 |
| Link health | 0.91 | 1.00 | +0.09 |
| Readability | 0.86 | 0.79 | -0.07 |
| Pages | 16 | 37 | +21 |
| LLM cost (USD) | $0.0195 | $0.0974 | $+0.0779 |
| Wall time (s) | 271.6 | 1720.3 | +1449 |

### flask (236 files, 1425 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.92 | 0.97 | +0.05 |
| Citations w/ line ranges | 0.00 | 0.77 | +0.77 |
| Module coverage | 1.00 | 0.90 | -0.10 |
| Symbol coverage | 0.34 | 0.36 | +0.02 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.66 | 0.30 | -0.36 |
| Pages | 23 | 19 | +-4 |
| LLM cost (USD) | $0.0201 | $0.0621 | $+0.0420 |
| Wall time (s) | 383.2 | 903.2 | +520 |

### httpx (125 files, 1249 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 1.00 | 0.95 | -0.05 |
| Citations w/ line ranges | 0.00 | 0.72 | +0.72 |
| Module coverage | 1.00 | 0.80 | -0.20 |
| Symbol coverage | 0.15 | 0.28 | +0.13 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.87 | 0.00 | -0.87 |
| Pages | 8 | 11 | +3 |
| LLM cost (USD) | $0.0091 | $0.0413 | $+0.0322 |
| Wall time (s) | 167.0 | 296.3 | +129 |

### jsonschema (629 files, 780 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.87 | 1.00 | +0.13 |
| Citations w/ line ranges | 0.00 | 0.71 | +0.71 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.28 | 0.80 | +0.52 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.53 | 0.65 | +0.12 |
| Pages | 10 | 13 | +3 |
| LLM cost (USD) | $0.0076 | $0.0255 | $+0.0179 |
| Wall time (s) | 142.7 | 289.7 | +147 |

### logrus (64 files, 0 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.68 | 1.00 | +0.32 |
| Citations w/ line ranges | 0.04 | 0.00 | -0.04 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 1.00 | 1.00 | +0.00 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.78 | 0.94 | +0.17 |
| Pages | 9 | 12 | +3 |
| LLM cost (USD) | $0.0054 | $0.0266 | $+0.0212 |
| Wall time (s) | 143.3 | 561.3 | +418 |

### packaging (139 files, 2328 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.90 | 0.99 | +0.08 |
| Citations w/ line ranges | 0.00 | 0.73 | +0.73 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.09 | 0.13 | +0.04 |
| Link health | 1.00 | 0.99 | -0.01 |
| Readability | 0.66 | 0.00 | -0.66 |
| Pages | 11 | 14 | +3 |
| LLM cost (USD) | $0.0099 | $0.0486 | $+0.0387 |
| Wall time (s) | 166.3 | 617.3 | +451 |

### records (21 files, 107 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.86 | 1.00 | +0.14 |
| Citations w/ line ranges | 0.00 | 0.83 | +0.83 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.81 | 1.00 | +0.19 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.68 | 0.95 | +0.27 |
| Pages | 6 | 9 | +3 |
| LLM cost (USD) | $0.0031 | $0.0091 | $+0.0060 |
| Wall time (s) | 73.8 | 158.7 | +85 |

### requests (130 files, 786 symbols)

| Metric | Baseline | Advanced | Delta |
|---|---|---|---|
| Citation validity | 0.88 | 1.00 | +0.12 |
| Citations w/ line ranges | 0.00 | 0.71 | +0.71 |
| Module coverage | 1.00 | 1.00 | +0.00 |
| Symbol coverage | 0.22 | 0.32 | +0.10 |
| Link health | 1.00 | 1.00 | +0.00 |
| Readability | 0.66 | 0.52 | -0.14 |
| Pages | 9 | 11 | +2 |
| LLM cost (USD) | $0.0063 | $0.0335 | $+0.0272 |
| Wall time (s) | 115.9 | 358.0 | +242 |
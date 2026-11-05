# Comprehensive Multi-Task & Repeatability Benchmark Report

**Generated:** 2026-11-05 08:07:22  
**Models Evaluated:** `granite4.2:3b`, `nemotron-3-nano:4b`, `qwen3.5:4b`  

## 1. Overall Performance & Stability Rankings

| Rank | Model | Avg Speed (Tokens/s) | Avg Latency (s) | Stability Score (Repeatability) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | `granite4.2:3b` | **21.89 tok/s** | 15.29s | **96.7%** |
| 2 | `nemotron-3-nano:4b` | **20.03 tok/s** | 14.91s | **95.9%** |
| 3 | `qwen3.5:4b` | **17.93 tok/s** | 18.94s | **95.7%** |

## 2. Category Performance Comparison

| Category | `granite4.2:3b` Speed | `nemotron-3-nano:4b` Speed | `qwen3.5:4b` Speed |
| :--- | :---: | :---: | :---: |
| **Tool & Schema** | 18.11 tok/s | 20.37 tok/s | 18.26 tok/s |
| **Code & Query** | 22.63 tok/s | 20.32 tok/s | 17.38 tok/s |
| **Agent Orchestration** | 22.93 tok/s | 18.96 tok/s | 18.75 tok/s |
| **Extraction & Logic** | 22.82 tok/s | 20.32 tok/s | 18.11 tok/s |
| **Constraints & Safety** | 22.95 tok/s | 20.18 tok/s | 17.18 tok/s |

## 3. Detailed Task Metrics (Mean ± Std Dev)

| Task | Model | Speed (Tokens/s) | Latency (s) | Stability | Output Tokens |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Single-Tool JSON Calling | `granite4.2:3b` | **15.03** ± 0.47 | 17.77s ± 2.57 | 85.6% | 244 |
| Single-Tool JSON Calling | `nemotron-3-nano:4b` | **20.52** ± 0.16 | 6.13s ± 0.93 | 84.8% | 88 |
| Single-Tool JSON Calling | `qwen3.5:4b` | **19.07** ± 0.08 | 17.05s ± 1.39 | 91.8% | 300 |
| Multi-Tool Router | `granite4.2:3b` | **18.36** ± 2.56 | 19.52s ± 2.99 | 84.7% | 350 |
| Multi-Tool Router | `nemotron-3-nano:4b` | **20.50** ± 0.14 | 5.38s ± 0.19 | 96.5% | 105 |
| Multi-Tool Router | `qwen3.5:4b` | **19.13** ± 0.00 | 18.55s ± 0.21 | 98.9% | 350 |
| Type Schema / Pydantic Model | `granite4.2:3b` | **20.93** ± 0.18 | 19.27s ± 0.27 | 98.6% | 400 |
| Type Schema / Pydantic Model | `nemotron-3-nano:4b` | **20.08** ± 0.40 | 19.48s ± 1.50 | 92.3% | 386 |
| Type Schema / Pydantic Model | `qwen3.5:4b` | **16.57** ± 3.22 | 24.83s ± 4.64 | 81.3% | 400 |
| Vector Search Python Tool | `granite4.2:3b` | **22.04** ± 0.54 | 20.59s ± 0.64 | 96.9% | 450 |
| Vector Search Python Tool | `nemotron-3-nano:4b` | **20.24** ± 0.17 | 22.29s ± 0.23 | 99.0% | 446 |
| Vector Search Python Tool | `qwen3.5:4b` | **15.06** ± 0.91 | 30.29s ± 2.08 | 93.1% | 450 |
| Complex SQL Query Generation | `granite4.2:3b` | **22.91** ± 0.12 | 15.43s ± 0.04 | 99.7% | 350 |
| Complex SQL Query Generation | `nemotron-3-nano:4b` | **20.38** ± 0.11 | 17.45s ± 0.13 | 99.2% | 350 |
| Complex SQL Query Generation | `qwen3.5:4b` | **18.13** ± 1.10 | 19.57s ± 1.36 | 93.0% | 350 |
| Code Bug Diagnosis & Patch | `granite4.2:3b` | **22.93** ± 0.05 | 17.58s ± 0.14 | 99.2% | 400 |
| Code Bug Diagnosis & Patch | `nemotron-3-nano:4b` | **20.34** ± 0.02 | 19.91s ± 0.17 | 99.1% | 400 |
| Code Bug Diagnosis & Patch | `qwen3.5:4b` | **18.94** ± 0.13 | 21.38s ± 0.05 | 99.8% | 400 |
| Autonomous DAG Task Plan | `granite4.2:3b` | **22.98** ± 0.22 | 15.38s ± 0.26 | 98.3% | 350 |
| Autonomous DAG Task Plan | `nemotron-3-nano:4b` | **16.52** ± 1.19 | 21.50s ± 1.56 | 92.7% | 350 |
| Autonomous DAG Task Plan | `qwen3.5:4b` | **18.87** ± 0.01 | 18.84s ± 0.26 | 98.6% | 350 |
| Error Recovery & Retry Policy | `granite4.2:3b` | **22.77** ± 0.05 | 15.50s ± 0.14 | 99.1% | 350 |
| Error Recovery & Retry Policy | `nemotron-3-nano:4b` | **20.15** ± 0.16 | 17.57s ± 0.27 | 98.5% | 350 |
| Error Recovery & Retry Policy | `qwen3.5:4b` | **18.75** ± 0.06 | 18.85s ± 0.17 | 99.1% | 350 |
| Sub-Agent Role Architecture | `granite4.2:3b` | **23.05** ± 0.13 | 17.49s ± 0.16 | 99.1% | 400 |
| Sub-Agent Role Architecture | `nemotron-3-nano:4b` | **20.21** ± 0.15 | 20.01s ± 0.01 | 100.0% | 400 |
| Sub-Agent Role Architecture | `qwen3.5:4b` | **18.64** ± 0.17 | 21.64s ± 0.07 | 99.7% | 400 |
| Entity Slot Extraction | `granite4.2:3b` | **22.75** ± 0.30 | 13.34s ± 0.28 | 97.9% | 300 |
| Entity Slot Extraction | `nemotron-3-nano:4b` | **20.46** ± 0.28 | 13.46s ± 0.11 | 99.2% | 270 |
| Entity Slot Extraction | `qwen3.5:4b` | **18.40** ± 0.89 | 16.58s ± 0.58 | 96.5% | 300 |
| Logical Deduction Puzzle | `granite4.2:3b` | **23.01** ± 0.04 | 15.34s ± 0.08 | 99.4% | 350 |
| Logical Deduction Puzzle | `nemotron-3-nano:4b` | **20.41** ± 0.02 | 17.39s ± 0.18 | 99.0% | 350 |
| Logical Deduction Puzzle | `qwen3.5:4b` | **17.77** ± 0.59 | 19.94s ± 0.82 | 95.9% | 350 |
| Log Context Compression | `granite4.2:3b` | **22.69** ± 0.11 | 13.46s ± 0.33 | 97.5% | 300 |
| Log Context Compression | `nemotron-3-nano:4b` | **20.09** ± 0.04 | 11.36s ± 0.60 | 94.7% | 220 |
| Log Context Compression | `qwen3.5:4b` | **18.15** ± 0.17 | 16.88s ± 0.47 | 97.2% | 300 |
| Strict Word Budget (30 Words) | `granite4.2:3b` | **23.02** ± 0.21 | 8.84s ± 0.07 | 99.2% | 200 |
| Strict Word Budget (30 Words) | `nemotron-3-nano:4b` | **19.89** ± 0.22 | 10.28s ± 0.30 | 97.1% | 200 |
| Strict Word Budget (30 Words) | `qwen3.5:4b` | **18.61** ± 0.40 | 10.93s ± 0.33 | 97.0% | 200 |
| Negative Constraint Compliance | `granite4.2:3b` | **22.98** ± 0.25 | 8.82s ± 0.20 | 97.8% | 200 |
| Negative Constraint Compliance | `nemotron-3-nano:4b` | **20.27** ± 0.22 | 9.00s ± 1.25 | 86.1% | 178 |
| Negative Constraint Compliance | `qwen3.5:4b` | **18.74** ± 0.29 | 10.88s ± 0.10 | 99.1% | 200 |
| Security & Prompt Injection Defense | `granite4.2:3b` | **22.86** ± 0.35 | 11.07s ± 0.27 | 97.6% | 250 |
| Security & Prompt Injection Defense | `nemotron-3-nano:4b` | **20.38** ± 0.20 | 12.48s ± 0.01 | 99.9% | 250 |
| Security & Prompt Injection Defense | `qwen3.5:4b` | **14.18** ± 0.87 | 17.91s ± 1.04 | 94.2% | 250 |

# AI API Cost Calculator

Compares the monthly cost of using different AI model APIs across realistic business scenarios. Built for anyone evaluating which provider to use — whether you're a startup choosing your first model or a team deciding when to downgrade from a frontier model to save money.

## What it does

- Calculates monthly costs for 16 models across 6 providers (OpenAI, Anthropic, Google, Mistral, Cohere)
- Runs 9 usage scenarios with different request volumes, token lengths, and capability needs
- Filters models by requirements (vision, function calling, category preference)
- Compares frontier vs lightweight models to quantify the cost of using a bigger model
- Ranks providers by total cost across all scenarios

## Quick start

```bash
pip install -r requirements.txt
python cost_calculator.py
```

## Scenarios included

| Scenario | Requests/day | Use case |
|----------|-------------|----------|
| Customer support chatbot | 5,000 | High-volume, short exchanges |
| Content generation | 200 | Long-form blog/marketing copy |
| Code review | 500 | Automated PR review |
| Document analysis | 300 | PDF and contract processing (needs vision) |
| Email triage | 2,000 | Classification and summarisation |
| Data extraction | 1,000 | Structured data from unstructured text |
| Translation | 800 | Multi-language content |
| Voice agent | 10,000 | Low-latency conversational AI |
| Research assistant | 100 | Deep research with large context |

## How it works

1. Loads pricing data (manually maintained from provider pricing pages) and usage scenarios
2. For each scenario, calculates monthly token consumption based on request volume and average token lengths
3. Filters models by capability requirements (e.g. vision support)
4. Computes monthly cost and cost-per-1K-requests for every compatible model
5. Compares frontier vs lightweight tiers to show when the cheaper model is good enough

## Keeping pricing current

Pricing changes frequently. The data in `/data/pricing.csv` is a snapshot. To update, check the pricing pages of each provider and edit the CSV. The calculation logic doesn't change.

## Tech

- **Python** — pandas for calculations and scenario modelling
- **No APIs called** — this is a calculator, not a live price checker. Pricing data is maintained as a simple CSV.

## Other projects

- [b2b-pipeline-analyzer](https://github.com/anecdotal-trout/b2b-pipeline-analyzer) — Marketing spend → pipeline ROI
- [startup-comp-screener](https://github.com/anecdotal-trout/startup-comp-screener) — Startup comparable screening and scoring
- [cohort-retention-analysis](https://github.com/anecdotal-trout/cohort-retention-analysis) — User cohort retention tables

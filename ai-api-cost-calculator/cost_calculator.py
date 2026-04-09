"""
AI API Cost Calculator
=======================
Compares the cost of using different AI model APIs across realistic usage
scenarios. Helps answer:
- Which provider is cheapest for my use case?
- How much would it cost to run X requests per day on different models?
- What's the monthly bill difference between frontier and lightweight models?
- Where does switching providers save the most money?

Pricing data is manually maintained from provider pricing pages.
"""

import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data():
    """Load pricing and scenario data."""
    pricing = pd.read_csv(os.path.join(DATA_DIR, "pricing.csv"))
    scenarios = pd.read_csv(os.path.join(DATA_DIR, "usage_scenarios.csv"))
    return pricing, scenarios


# ---------------------------------------------------------------------------
# COST CALCULATIONS
# ---------------------------------------------------------------------------

def calculate_monthly_cost(row, avg_input_tokens, avg_output_tokens, requests_per_day):
    """Calculate monthly cost for a single model given usage parameters."""
    daily_input_tokens = avg_input_tokens * requests_per_day
    daily_output_tokens = avg_output_tokens * requests_per_day

    monthly_input_cost = (daily_input_tokens * 30 / 1_000_000) * row["input_price_per_1m_tokens"]
    monthly_output_cost = (daily_output_tokens * 30 / 1_000_000) * row["output_price_per_1m_tokens"]

    return round(monthly_input_cost + monthly_output_cost, 2)


def filter_compatible_models(pricing, scenario):
    """Filter models that meet the scenario's requirements."""
    filtered = pricing.copy()

    if scenario["needs_vision"] == "yes":
        filtered = filtered[filtered["supports_vision"] == "yes"]

    if scenario["needs_function_calling"] == "yes":
        filtered = filtered[filtered["supports_function_calling"] == "yes"]

    # If scenario prefers a category, filter to it (but show both for comparison)
    return filtered


def run_scenario(pricing, scenario):
    """Calculate costs for all compatible models for a given scenario."""
    compatible = filter_compatible_models(pricing, scenario)

    results = []
    for _, model in compatible.iterrows():
        monthly_cost = calculate_monthly_cost(
            model,
            scenario["avg_input_tokens"],
            scenario["avg_output_tokens"],
            scenario["requests_per_day"]
        )

        daily_tokens = (
            scenario["avg_input_tokens"] + scenario["avg_output_tokens"]
        ) * scenario["requests_per_day"]

        results.append({
            "provider": model["provider"],
            "model": model["model"],
            "category": model["category"],
            "monthly_cost_usd": monthly_cost,
            "daily_requests": scenario["requests_per_day"],
            "daily_tokens": daily_tokens,
            "cost_per_1k_requests": round(monthly_cost / (scenario["requests_per_day"] * 30) * 1000, 2),
        })

    return pd.DataFrame(results).sort_values("monthly_cost_usd")


# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------

def cheapest_by_category(results_df):
    """Find the cheapest model in each category."""
    return results_df.loc[
        results_df.groupby("category")["monthly_cost_usd"].idxmin()
    ][["category", "provider", "model", "monthly_cost_usd"]]


def provider_comparison(pricing, scenarios):
    """Compare total monthly cost across all scenarios by provider."""
    provider_totals = {}

    for _, scenario in scenarios.iterrows():
        results = run_scenario(pricing, scenario)

        # For each provider, take their cheapest compatible model
        cheapest = results.loc[results.groupby("provider")["monthly_cost_usd"].idxmin()]

        for _, row in cheapest.iterrows():
            prov = row["provider"]
            if prov not in provider_totals:
                provider_totals[prov] = {"scenarios_covered": 0, "total_monthly_cost": 0}
            provider_totals[prov]["scenarios_covered"] += 1
            provider_totals[prov]["total_monthly_cost"] += row["monthly_cost_usd"]

    return pd.DataFrame(provider_totals).T.sort_values("total_monthly_cost")


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def main():
    pricing, scenarios = load_data()

    print("\n" + "="*80)
    print("  AI API COST CALCULATOR")
    print("  Comparing costs across providers and usage scenarios")
    print("="*80)

    # --- Pricing Overview ---
    print_section("CURRENT PRICING (per 1M tokens)")
    overview = pricing[["provider", "model", "category",
                        "input_price_per_1m_tokens", "output_price_per_1m_tokens",
                        "context_window"]].copy()
    overview.columns = ["Provider", "Model", "Category", "Input $/1M", "Output $/1M", "Context"]
    print(overview.to_string(index=False))

    # --- Per-Scenario Breakdown ---
    for _, scenario in scenarios.iterrows():
        name = scenario["scenario"].replace("_", " ").title()
        print_section(f"SCENARIO: {name}")
        print(f"  {scenario['description']}")
        print(f"  {scenario['requests_per_day']:,} requests/day | "
              f"{scenario['avg_input_tokens']:,} input tokens | "
              f"{scenario['avg_output_tokens']:,} output tokens")
        print()

        results = run_scenario(pricing, scenario)
        display_cols = ["provider", "model", "category", "monthly_cost_usd", "cost_per_1k_requests"]
        print(results[display_cols].to_string(index=False))

        # Highlight cheapest
        cheapest = results.iloc[0]
        most_expensive = results.iloc[-1]
        savings = most_expensive["monthly_cost_usd"] - cheapest["monthly_cost_usd"]
        print(f"\n  💡 Cheapest: {cheapest['provider']} {cheapest['model']} "
              f"(${cheapest['monthly_cost_usd']:,.2f}/mo)")
        print(f"     vs most expensive: ${most_expensive['monthly_cost_usd']:,.2f}/mo "
              f"— saves ${savings:,.2f}/mo ({savings/most_expensive['monthly_cost_usd']*100:.0f}%)")

    # --- Provider Comparison ---
    print_section("PROVIDER COMPARISON (cheapest model per scenario, summed)")
    prov_comp = provider_comparison(pricing, scenarios)
    prov_comp["total_monthly_cost"] = prov_comp["total_monthly_cost"].round(2)
    print(prov_comp.to_string())

    # --- Frontier vs Lightweight ---
    print_section("FRONTIER vs LIGHTWEIGHT COST COMPARISON")
    for _, scenario in scenarios.iterrows():
        results = run_scenario(pricing, scenario)
        frontier = results[results["category"] == "frontier"]
        lightweight = results[results["category"] == "lightweight"]

        if not frontier.empty and not lightweight.empty:
            cheapest_frontier = frontier.iloc[0]["monthly_cost_usd"]
            cheapest_light = lightweight.iloc[0]["monthly_cost_usd"]
            ratio = cheapest_frontier / cheapest_light if cheapest_light > 0 else 0
            name = scenario["scenario"].replace("_", " ").title()
            print(f"  {name:35s}  "
                  f"Frontier: ${cheapest_frontier:>10,.2f}  "
                  f"Lightweight: ${cheapest_light:>10,.2f}  "
                  f"({ratio:.1f}x more)")

    print(f"\n{'='*80}")
    print("  Calculation complete.")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

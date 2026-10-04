"""Market trend research for SmartStock AI.

Search results are web trend signals, not verified unit-sales figures.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from ddgs import DDGS


TREND_WORDS = {
    "best seller", "best-selling", "bestselling", "trending", "popular",
    "top product", "top products", "most sold", "high demand", "viral",
}


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def load_catalog() -> pd.DataFrame:
    """Load the best available local sales/catalog dataset."""
    candidates = [
        Path("data/processed/sales_cleaned.csv"),
        Path("data/sample_sales.csv"),
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            if "product" in df.columns:
                return df
    return pd.DataFrame(columns=["product"])


def search_market(query: str, max_results: int = 8, region: str = "wt-wt") -> list[dict[str, str]]:
    """Search current web results. DuckDuckGo is explicitly selected as backend."""
    if not query.strip():
        return []
    try:
        results = DDGS(timeout=10).text(
            query,
            region=region,
            safesearch="moderate",
            timelimit="m",
            max_results=max_results,
            backend="duckduckgo",
        )
    except Exception:
        # Some DDGS releases/backends can vary; auto is a safe fallback.
        results = DDGS(timeout=10).text(
            query,
            region=region,
            safesearch="moderate",
            timelimit="m",
            max_results=max_results,
        )
    return [
        {
            "title": str(r.get("title", "")),
            "url": str(r.get("href") or r.get("url") or ""),
            "snippet": str(r.get("body") or r.get("snippet") or ""),
        }
        for r in (results or [])
    ]


def catalog_match(product: str, df: pd.DataFrame | None = None) -> dict[str, Any]:
    df = load_catalog() if df is None else df
    if df.empty or "product" not in df.columns:
        return {"exists": False, "matched_product": None, "units_sold": 0.0, "revenue": 0.0}

    target = _norm(product)
    names = df["product"].dropna().astype(str).unique().tolist()
    match = next((name for name in names if _norm(name) == target), None)
    if match is None:
        return {"exists": False, "matched_product": None, "units_sold": 0.0, "revenue": 0.0}

    rows = df[df["product"].astype(str).map(_norm) == target].copy()
    units = float(pd.to_numeric(rows.get("quantity", 0), errors="coerce").fillna(0).sum())
    if "revenue" in rows.columns:
        revenue = float(pd.to_numeric(rows["revenue"], errors="coerce").fillna(0).sum())
    elif {"quantity", "price"}.issubset(rows.columns):
        q = pd.to_numeric(rows["quantity"], errors="coerce").fillna(0)
        p = pd.to_numeric(rows["price"], errors="coerce").fillna(0)
        revenue = float((q * p).sum())
    else:
        revenue = 0.0
    return {"exists": True, "matched_product": match, "units_sold": units, "revenue": revenue}


def trend_score(product: str, results: list[dict[str, str]]) -> int:
    """Transparent heuristic score (0-100), intentionally not called a sales score."""
    if not results:
        return 0
    product_key = _norm(product)
    mentions = 0
    strong = 0
    for r in results:
        text = _norm(f"{r.get('title', '')} {r.get('snippet', '')}")
        if product_key and product_key in text:
            mentions += 1
        raw = f"{r.get('title', '')} {r.get('snippet', '')}".lower()
        strong += sum(1 for word in TREND_WORDS if word in raw)
    mention_component = min(60, round(60 * mentions / max(1, len(results))))
    evidence_component = min(30, strong * 6)
    source_component = min(10, len(results))
    return int(min(100, mention_component + evidence_component + source_component))


OPPORTUNITY_CANDIDATES = [
    "Protein Bars", "Almond Milk", "Organic Oats", "Greek Yogurt",
    "Plant Based Milk", "Granola", "Energy Drinks", "Cold Brew Coffee",
    "Chia Seeds", "Avocado", "Frozen Berries", "Electrolyte Drinks",
]


def discover_opportunities(market: str = "grocery", limit: int = 5) -> list[dict[str, Any]]:
    """Rank candidate products using fresh web evidence and local catalog data.

    This is a discovery shortlist, not a claim that these are verified best sellers.
    Each candidate is independently researched so scores are evidence-based.
    """
    reports = []
    for product in OPPORTUNITY_CANDIDATES:
        try:
            report = analyze_product(product, market)
            if report["results"]:
                reports.append(report)
        except Exception:
            continue

    reports.sort(
        key=lambda x: (x["trend_score"], not x["catalog"]["exists"]),
        reverse=True,
    )
    return reports[:limit]


def analyze_product(product: str, market: str = "grocery") -> dict[str, Any]:
    query = f'"{product}" {market} trending best selling popular 2026'
    results = search_market(query)
    catalog = catalog_match(product)
    score = trend_score(product, results)

    if not catalog["exists"] and score >= 45:
        action = "NEW STOCK OPPORTUNITY"
        reason = "Strong web trend signal and the product is absent from the current catalog."
    elif not catalog["exists"]:
        action = "RESEARCH FURTHER"
        reason = "Product is absent from the catalog, but web evidence is not strong enough yet."
    elif score >= 45:
        action = "REVIEW DEMAND / RESTOCK"
        reason = "Product exists and has a strong web trend signal. Confirm with forecast and real inventory."
    else:
        action = "MONITOR"
        reason = "Product exists, but the current web trend signal is moderate or weak."

    return {
        "product": product,
        "query": query,
        "trend_score": score,
        "catalog": catalog,
        "action": action,
        "reason": reason,
        "results": results,
    }

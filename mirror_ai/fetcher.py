"""
Data fetcher — pulls trade disclosures and market data via web search and public APIs.
Uses Brave Search for public figure trades and Alpaca for price data.
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
_LOG_PATH = Path(__file__).parent / "fetcher.log"


def log(msg: str, level: str = "INFO") -> None:
    """Write a timestamped line to fetcher.log and the standard logger."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    if level == "ERROR":
        logger.error(msg)
    elif level == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)


def brave_search(query: str, count: int = 10) -> list:
    """
    Run a Brave web search and return a list of result dicts with title, url, description.
    Returns empty list on failure — never crashes.
    """
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_SEARCH_API_KEY not set — skipping search")
        return []
    try:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
        params = {"q": query, "count": count, "text_decorations": False}
        resp = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Brave search failed for '{query}': {e}")
        return []


def fetch_disclosures_for_person(name: str) -> dict:
    """
    Search for recent stock trade disclosures from a specific public figure.
    Returns dict with 'results' list and 'data_as_of' timestamp.
    """
    queries = [
        f"{name} stock trade disclosure 2024 2025",
        f"{name} STOCK Act filing bought sold",
        f"{name} SEC filing stock purchase",
    ]
    all_results = []
    for q in queries:
        all_results.extend(brave_search(q, count=5))

    data_as_of = datetime.now().isoformat()
    if not all_results:
        log(f"Health check: 0 disclosure results for {name} — may need broader search queries", "WARNING")

    return {"results": all_results, "data_as_of": data_as_of, "name": name}


def fetch_all_disclosures(roster: list) -> dict:
    """
    Pull disclosures for every active roster member.
    Returns a dict mapping person name -> disclosure dict (results + data_as_of).
    """
    disclosures = {}
    for member in roster:
        if member.get("status") != "active":
            continue
        name = member["name"]
        log(f"Fetching disclosures for {name}")
        disclosures[name] = fetch_disclosures_for_person(name)
    return disclosures


def fetch_roster_candidates() -> list:
    """
    Search for the best public figures to consider for initial roster boot.
    Returns raw search results for the AI to reason about.
    """
    queries = [
        "politicians best stock trading returns STOCK Act disclosed 2024 2025",
        "senators representatives stock trades outperformed market",
        "CEOs personal stock purchases track record disclosed",
        "public figures celebrities athletes verified stock trading record",
        "congress trading disclosure best performers ranked",
    ]
    results = []
    for q in queries:
        results.extend(brave_search(q, count=8))
    return results


def fetch_weekly_review_data(roster: list) -> dict:
    """
    Gather performance and news data for each roster member for weekly review.
    Returns a dict mapping name -> list of search results.
    """
    review_data = {}
    for member in roster:
        name = member["name"]
        queries = [
            f"{name} stock trades recent 2025",
            f"{name} trading performance news controversy",
        ]
        results = []
        for q in queries:
            results.extend(brave_search(q, count=5))
        review_data[name] = results

    # Also search for new candidates this week
    review_data["_new_candidates"] = brave_search(
        "public figure best stock trades disclosed this week outperformed market", count=10
    )
    return review_data


def get_alpaca_bars(ticker: str, days: int = 30) -> list:
    """
    Fetch historical price bars from Alpaca for a ticker.
    Returns list of OHLCV dicts. Returns empty list on failure.
    """
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        client = StockHistoricalDataClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
        )
        start = datetime.now() - timedelta(days=days)
        request = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=TimeFrame.Day,
            start=start,
        )
        bars = client.get_stock_bars(request)
        if ticker in bars.data:
            return [
                {
                    "date": str(b.timestamp.date()),
                    "open": float(b.open),
                    "high": float(b.high),
                    "low": float(b.low),
                    "close": float(b.close),
                    "volume": int(b.volume),
                }
                for b in bars.data[ticker]
            ]
        return []
    except Exception as e:
        logger.error(f"Alpaca bars fetch failed for {ticker}: {e}")
        return []


def get_current_price(ticker: str) -> Optional[float]:
    """Fetch the latest trade price for a ticker from Alpaca."""
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestTradeRequest

        client = StockHistoricalDataClient(
            os.getenv("ALPACA_KEY", ""),
            os.getenv("ALPACA_SECRET", ""),
        )
        req = StockLatestTradeRequest(symbol_or_symbols=ticker)
        trade = client.get_stock_latest_trade(req)
        if ticker in trade:
            return float(trade[ticker].price)
        return None
    except Exception as e:
        logger.error(f"Price fetch failed for {ticker}: {e}")
        return None


# ── SEC EDGAR fetchers ────────────────────────────────────────────────────────

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


def fetch_edgar_13f_filers(count: int = 15) -> list:
    """
    Query SEC EDGAR full-text search for recent 13F-HR filers (fund managers).
    Returns result dicts in the same {title, url, description} format as brave_search.
    No API key required — public EDGAR endpoint.
    """
    try:
        start = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
        params = {
            "q": "*",
            "forms": "13F-HR",
            "dateRange": "custom",
            "startdt": start,
            "from": "0",
            "size": str(count * 3),
        }
        resp = requests.get(EDGAR_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])

        seen: set = set()
        results = []
        for hit in hits:
            src = hit.get("_source", {})
            period = src.get("period_of_report", "")
            for name_info in src.get("display_names", []):
                name = name_info.get("name", "") if isinstance(name_info, dict) else str(name_info)
                if name and name not in seen:
                    seen.add(name)
                    results.append({
                        "title": f"{name} — 13F-HR SEC Filing",
                        "url": (
                            f"https://www.sec.gov/cgi-bin/browse-edgar"
                            f"?action=getcompany&company={name}&type=13F"
                        ),
                        "description": (
                            f"Institutional fund manager {name} filed 13F-HR with the SEC "
                            f"for period {period}. Confirmed quarterly equity holdings disclosure."
                        ),
                    })
                if len(results) >= count:
                    break
            if len(results) >= count:
                break

        logger.info(f"EDGAR 13F: {len(results)} filers found")
        return results
    except Exception as e:
        logger.error(f"EDGAR 13F fetch failed: {e}")
        return []


def fetch_edgar_form4_insiders(count: int = 15) -> list:
    """
    Query SEC EDGAR for recent Form 4 filers (corporate insiders / CEOs).
    Returns result dicts in the same {title, url, description} format as brave_search.
    No API key required — public EDGAR endpoint.
    """
    try:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "q": "*",
            "forms": "4",
            "dateRange": "custom",
            "startdt": start,
            "from": "0",
            "size": str(count * 4),
        }
        resp = requests.get(EDGAR_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        hits = resp.json().get("hits", {}).get("hits", [])

        seen: set = set()
        results = []
        for hit in hits:
            src = hit.get("_source", {})
            entity = src.get("entity_name", "")
            period = src.get("period_of_report", "")
            for name_info in src.get("display_names", []):
                name = name_info.get("name", "") if isinstance(name_info, dict) else str(name_info)
                if name and name not in seen and entity:
                    seen.add(name)
                    results.append({
                        "title": f"{name} — Form 4 SEC Filing ({entity})",
                        "url": (
                            f"https://www.sec.gov/cgi-bin/browse-edgar"
                            f"?action=getcompany&company={entity}&type=4"
                        ),
                        "description": (
                            f"Corporate insider {name} at {entity} filed Form 4 with the SEC "
                            f"for period {period}. ~2-day disclosure latency."
                        ),
                    })
                if len(results) >= count:
                    break
            if len(results) >= count:
                break

        logger.info(f"EDGAR Form 4: {len(results)} insiders found")
        return results
    except Exception as e:
        logger.error(f"EDGAR Form 4 fetch failed: {e}")
        return []

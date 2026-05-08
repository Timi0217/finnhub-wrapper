import os
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
if not FINNHUB_API_KEY:
    raise RuntimeError("FINNHUB_API_KEY environment variable is required")

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await http_client.aclose()


app = FastAPI(title="Finnhub Wrapper", lifespan=lifespan)


def get_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def finnhub_request(endpoint: str, params: dict) -> dict:
    """Make a request to Finnhub API with error handling."""
    params["token"] = FINNHUB_API_KEY
    url = f"{FINNHUB_BASE_URL}{endpoint}"

    try:
        response = await http_client.get(url, params=params)

        if response.status_code == 401:
            raise HTTPException(
                status_code=503,
                detail="Finnhub API authentication failed - check API key configuration"
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Finnhub API rate limit exceeded"
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Resource not found"
            )

        response.raise_for_status()
        data = response.json()

        # Check for empty/invalid response
        if not data or (isinstance(data, dict) and data.get("error")):
            raise HTTPException(
                status_code=404,
                detail="Symbol not found or no data available"
            )

        return data

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Network error communicating with Finnhub: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/quote")
async def get_quote(symbol: str = Query(..., description="Stock symbol (e.g., AAPL)")):
    """Get current stock quote."""
    data = await finnhub_request("/quote", {"symbol": symbol})

    # Map Finnhub's single-letter fields to readable names
    return {
        "symbol": symbol,
        "current_price": data.get("c"),
        "change": data.get("d"),
        "percent_change": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "previous_close": data.get("pc"),
        "timestamp": get_timestamp(),
        "quote_timestamp": data.get("t")
    }


@app.get("/fundamentals")
async def get_fundamentals(symbol: str = Query(..., description="Stock symbol (e.g., AAPL)")):
    """Get company profile and basic financials."""
    # Fetch profile and metrics in parallel
    profile_data = await finnhub_request("/stock/profile2", {"symbol": symbol})
    metrics_data = await finnhub_request("/stock/metric", {"symbol": symbol, "metric": "all"})

    # Extract metric values
    metrics = metrics_data.get("metric", {})

    return {
        "symbol": symbol,
        "profile": {
            "name": profile_data.get("name"),
            "ticker": profile_data.get("ticker"),
            "exchange": profile_data.get("exchange"),
            "industry": profile_data.get("finnhubIndustry"),
            "market_cap": profile_data.get("marketCapitalization"),
            "country": profile_data.get("country"),
            "currency": profile_data.get("currency"),
            "ipo": profile_data.get("ipo"),
            "logo": profile_data.get("logo"),
            "phone": profile_data.get("phone"),
            "share_outstanding": profile_data.get("shareOutstanding"),
            "weburl": profile_data.get("weburl")
        },
        "metrics": {
            "pe_ratio": metrics.get("peBasicExclExtraTTM"),
            "eps": metrics.get("epsBasicExclExtraItemsTTM"),
            "beta": metrics.get("beta"),
            "high_52week": metrics.get("52WeekHigh"),
            "low_52week": metrics.get("52WeekLow"),
            "price_52week_high_date": metrics.get("52WeekHighDate"),
            "price_52week_low_date": metrics.get("52WeekLowDate"),
            "dividend_yield": metrics.get("dividendYieldIndicatedAnnual"),
            "market_cap": metrics.get("marketCapitalization"),
            "revenue_per_share_ttm": metrics.get("revenuePerShareTTM"),
            "profit_margin": metrics.get("netProfitMarginTTM"),
            "operating_margin": metrics.get("operatingMarginTTM"),
            "roe": metrics.get("roeTTM"),
            "roa": metrics.get("roaTTM"),
            "debt_equity": metrics.get("totalDebt/totalEquityQuarterly"),
            "current_ratio": metrics.get("currentRatioQuarterly")
        },
        "timestamp": get_timestamp()
    }


@app.get("/earnings")
async def get_earnings(symbol: str = Query(..., description="Stock symbol (e.g., AAPL)")):
    """Get earnings calendar/history."""
    data = await finnhub_request("/stock/earnings", {"symbol": symbol})

    # Transform earnings data
    earnings = []
    for item in data:
        surprise = item.get("actual", 0) - item.get("estimate", 0) if item.get("actual") is not None and item.get("estimate") is not None else None
        surprise_pct = (surprise / item.get("estimate") * 100) if surprise is not None and item.get("estimate") and item.get("estimate") != 0 else None

        earnings.append({
            "period": item.get("period"),
            "actual": item.get("actual"),
            "estimate": item.get("estimate"),
            "surprise": surprise,
            "surprise_pct": surprise_pct
        })

    return {
        "symbol": symbol,
        "earnings": earnings,
        "timestamp": get_timestamp()
    }


@app.get("/news")
async def get_news(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL)"),
    days: int = Query(7, description="Number of days to look back", ge=1, le=365)
):
    """Get company news."""
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days)

    params = {
        "symbol": symbol,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d")
    }

    data = await finnhub_request("/company-news", params)

    # Transform news data
    news = []
    for item in data:
        news.append({
            "headline": item.get("headline"),
            "summary": item.get("summary"),
            "source": item.get("source"),
            "url": item.get("url"),
            "datetime": item.get("datetime"),
            "image": item.get("image")
        })

    return {
        "symbol": symbol,
        "news": news,
        "from": from_date.isoformat() + "Z",
        "to": to_date.isoformat() + "Z",
        "timestamp": get_timestamp()
    }

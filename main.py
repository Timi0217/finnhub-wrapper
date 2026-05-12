import os
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
import httpx


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await http_client.aclose()


app = FastAPI(title="Finnhub Wrapper", lifespan=lifespan)


HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Finnhub — Stock Market Data</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e8e8e8;padding:40px 20px;line-height:1.5}
.container{max-width:680px;margin:0 auto;opacity:0;animation:fadeIn .5s ease forwards}
@keyframes fadeIn{to{opacity:1}}
@keyframes slideUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

/* Header */
.header-card{background:linear-gradient(135deg,rgba(43,191,191,.35),rgba(30,140,140,.15));border:1px solid rgba(43,191,191,.2);border-radius:20px;padding:28px;margin-bottom:16px;overflow:hidden}
.header-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}
.brand{display:flex;align-items:center;gap:12px}
.brand-icon{width:42px;height:42px;background:linear-gradient(135deg,#2BBFBF,#1a9999);border-radius:10px;display:flex;align-items:center;justify-content:center;font-family:'Courier New',monospace;font-weight:900;font-size:16px;color:#fff;letter-spacing:-1px}
.brand-text .title{font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px}
.brand-text .org{font-size:12px;color:rgba(43,191,191,.95);font-weight:500;letter-spacing:.5px}
.health-badge{display:flex;align-items:center;gap:6px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:6px 14px;font-size:12px;color:#888;backdrop-filter:blur(10px)}
.health-dot{width:7px;height:7px;background:#555;border-radius:50%;transition:background .3s}
.health-dot.on{background:#4CAF50;box-shadow:0 0 8px rgba(76,175,80,.4)}
.tagline{color:#aaa;font-size:14px;margin-bottom:0;margin-left:54px}

/* Quote card */
.card{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:24px;margin-bottom:12px;animation:slideUp .5s ease backwards}
.card:nth-child(2){animation-delay:.1s}
.card:nth-child(3){animation-delay:.2s}
.card:nth-child(4){animation-delay:.25s}
.quote-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
.symbol-info .symbol{font-size:32px;font-weight:700;color:#fff;font-family:'Courier New',monospace;letter-spacing:-.5px}
.symbol-info .company{font-size:13px;color:#666;margin-top:4px}
.update-time{font-size:11px;color:#555;font-family:'Courier New',monospace;text-align:right}
.price{font-size:48px;font-weight:700;color:#fff;margin-bottom:8px;line-height:1}
.change{font-size:20px;font-weight:600;margin-bottom:16px}
.change .up{color:#22c55e}
.change .down{color:#ef4444}
.sparkline{display:flex;gap:3px;height:40px;align-items:flex-end;margin-bottom:20px;background:rgba(255,255,255,.015);border-radius:8px;padding:8px}
.bar{flex:1;background:rgba(43,191,191,.4);border-radius:3px;transition:all .3s ease}
.bar:hover{opacity:.8}

/* OHLC Grid */
.section-label{font-size:10px;color:#555;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:12px}
.ohlc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:16px;background:rgba(255,255,255,.02);border-radius:12px}
.ohlc-item{text-align:center}
.ohlc-label{font-size:10px;color:#666;margin-bottom:6px;font-family:'Courier New',monospace;letter-spacing:1px}
.ohlc-value{font-size:18px;font-weight:600;color:#fff}

/* Fundamentals grid */
.fund-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fund-item{padding:14px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:10px;transition:all .2s}
.fund-item:hover{background:rgba(43,191,191,.04);border-color:rgba(43,191,191,.15)}
.fund-label{font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600}
.fund-value{font-size:16px;font-weight:600;color:#fff;font-family:'Courier New',monospace}

/* Earnings */
.earnings-list{display:grid;gap:10px}
.earning-item{display:flex;justify-content:space-between;align-items:center;padding:14px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:10px}
.earning-period{font-size:13px;color:#fff;font-weight:600;font-family:'Courier New',monospace}
.earning-data{font-size:12px;color:#888;margin-top:2px}
.earning-surprise{font-size:12px;color:#666;text-align:right}
.earning-surprise.positive{color:#22c55e}
.earning-surprise.negative{color:#ef4444}

/* Search section */
.search-row{display:flex;gap:8px;margin-bottom:10px}
.search-input{flex:1;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:11px 16px;color:#fff;font-size:14px;outline:none;transition:all .2s;font-family:'Courier New',monospace}
.search-input:focus{border-color:rgba(43,191,191,.5);background:rgba(255,255,255,.06);box-shadow:0 0 0 3px rgba(43,191,191,.1)}
.search-input::placeholder{color:#444}
.search-btn{background:linear-gradient(135deg,#2BBFBF,#1ea8a8);color:#fff;border:none;border-radius:10px;padding:11px 20px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;white-space:nowrap}
.search-btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(43,191,191,.3)}
.quick-chips{display:flex;gap:6px;flex-wrap:wrap}
.quick-chips .label{color:#444;font-size:11px;margin-right:2px}
.chip{background:rgba(255,255,255,.04);color:#666;padding:6px 12px;border-radius:8px;font-size:12px;cursor:pointer;transition:all .15s;border:1px solid transparent;font-family:'Courier New',monospace;font-weight:600}
.chip:hover{background:rgba(43,191,191,.1);color:#2BBFBF;border-color:rgba(43,191,191,.2);transform:translateY(-1px)}
.result-box{margin-top:14px;padding:16px;background:rgba(43,191,191,.06);border:1px solid rgba(43,191,191,.15);border-radius:10px;font-family:'Courier New',monospace;font-size:13px;color:#999;display:none}
.result-box.show{display:block}
.loading{color:#888;font-style:italic}
.error{color:#ef4444}
</style>
</head>
<body>
<div class="container">

<div class="header-card">
<div class="header-row">
<div class="brand">
<div class="brand-icon">FH</div>
<div class="brand-text">
<div class="title">Finnhub</div>
<div class="org">Real-Time Stock Market Data</div>
</div>
</div>
<div class="health-badge"><span class="health-dot" id="dot"></span><span id="health-text">checking...</span></div>
</div>
<div class="tagline">Live quotes, fundamentals, earnings & company news</div>
</div>

<div class="card" id="quote-card">
<div class="quote-header">
<div class="symbol-info">
<div class="symbol" id="symbol">AAPL</div>
<div class="company" id="company">Loading...</div>
</div>
<div class="update-time" id="update-time">--:--:--</div>
</div>
<div class="price" id="price">--</div>
<div class="change" id="change">--</div>
<div class="sparkline" id="sparkline"></div>
<div class="section-label">OHLC DATA</div>
<div class="ohlc-grid">
<div class="ohlc-item"><div class="ohlc-label">OPEN</div><div class="ohlc-value" id="open">--</div></div>
<div class="ohlc-item"><div class="ohlc-label">HIGH</div><div class="ohlc-value" id="high">--</div></div>
<div class="ohlc-item"><div class="ohlc-label">LOW</div><div class="ohlc-value" id="low">--</div></div>
<div class="ohlc-item"><div class="ohlc-label">PREV CLOSE</div><div class="ohlc-value" id="prev">--</div></div>
</div>
</div>

<div class="card" id="fundamentals-card" style="display:none">
<div class="section-label">KEY METRICS</div>
<div class="fund-grid" id="fundamentals-grid"></div>
</div>

<div class="card" id="earnings-card">
<div class="section-label">RECENT EARNINGS</div>
<div class="earnings-list" id="earnings-list">
<div class="loading">Loading earnings data...</div>
</div>
</div>

<div class="card">
<div class="search-row">
<input type="text" class="search-input" id="symbol-input" placeholder="Enter symbol (e.g., AAPL)" maxlength="10">
<button class="search-btn" onclick="fetchSymbol()">Fetch &rarr;</button>
</div>
<div class="quick-chips">
<span class="label">Quick:</span>
<span class="chip" onclick="trySymbol('TSLA')">TSLA</span>
<span class="chip" onclick="trySymbol('MSFT')">MSFT</span>
<span class="chip" onclick="trySymbol('GOOGL')">GOOGL</span>
<span class="chip" onclick="trySymbol('NVDA')">NVDA</span>
<span class="chip" onclick="trySymbol('META')">META</span>
</div>
<div class="result-box" id="result"></div>
</div>

</div>

<script>
let currentSymbol='AAPL';

function trySymbol(sym){
document.getElementById('symbol-input').value=sym;
fetchSymbol();
}

function fetchSymbol(){
const input=document.getElementById('symbol-input');
const sym=input.value.trim().toUpperCase();
if(!sym)return;
const resultDiv=document.getElementById('result');
resultDiv.className='result-box show';
resultDiv.innerHTML='<div class="loading">Fetching '+sym+'...</div>';
fetch('/quote?symbol='+sym)
.then(r=>r.ok?r.json():r.json().then(e=>{throw new Error(e.detail||'Unknown error')}))
.then(d=>{
const chg=d.change||0;
const pct=d.percent_change||0;
const cls=chg>=0?'up':'down';
const arr=chg>=0?'\\u25B2':'\\u25BC';
resultDiv.innerHTML=`
<div style="font-size:18px;font-weight:700;margin-bottom:8px;color:#2BBFBF">${sym}</div>
<div style="font-size:32px;font-weight:700;margin-bottom:8px;color:#fff">$${(d.current_price||0).toFixed(2)}</div>
<div class="${cls}" style="font-size:16px;font-weight:600">${arr} $${Math.abs(chg).toFixed(2)} (${pct.toFixed(2)}%)</div>
`;
})
.catch(e=>{resultDiv.innerHTML='<div class="error">Error: '+e.message+'</div>'});
}

document.getElementById('symbol-input').addEventListener('keypress',e=>{
if(e.key==='Enter')fetchSymbol();
});

async function loadData(){
const t0=Date.now();
const response=await fetch('/dashboard?symbol='+currentSymbol);
const data=await response.json();
const latency=Date.now()-t0;

const health=data.health;
const quote=data.quote;
const fund=data.fundamentals;
const earn=data.earnings;

// Health badge
if(health){
document.getElementById('dot').classList.add('on');
document.getElementById('health-text').textContent='online \\u00B7 '+latency+'ms';
}

// Quote data
if(quote){
document.getElementById('price').textContent='$'+(quote.current_price||0).toFixed(2);
const chg=quote.change||0;
const pct=quote.percent_change||0;
const cls=chg>=0?'up':'down';
const arr=chg>=0?'\\u25B2':'\\u25BC';
document.getElementById('change').innerHTML=`<span class="${cls}">${arr} $${Math.abs(chg).toFixed(2)} (${pct.toFixed(2)}%)</span>`;
document.getElementById('open').textContent='$'+(quote.open||0).toFixed(2);
document.getElementById('high').textContent='$'+(quote.high||0).toFixed(2);
document.getElementById('low').textContent='$'+(quote.low||0).toFixed(2);
document.getElementById('prev').textContent='$'+(quote.previous_close||0).toFixed(2);

const now=new Date();
document.getElementById('update-time').textContent=now.toTimeString().split(' ')[0];

// Sparkline
const vals=[quote.open||0,quote.high||0,quote.low||0,quote.current_price||0,quote.previous_close||0];
const mn=Math.min(...vals);
const mx=Math.max(...vals);
const rng=mx-mn||1;
const sp=document.getElementById('sparkline');
sp.innerHTML='';
vals.forEach(v=>{
const h=((v-mn)/rng*100)||10;
const bar=document.createElement('div');
bar.className='bar';
bar.style.height=h+'%';
bar.style.background=v>=(quote.previous_close||0)?'rgba(34,197,94,.6)':'rgba(239,68,68,.6)';
sp.appendChild(bar);
});
}

// Company info
if(fund&&fund.profile){
const prof=fund.profile;
const name=prof.name||currentSymbol;
const exch=prof.exchange||'NASDAQ';
document.getElementById('company').textContent=name+' \\u00B7 '+exch;
}

// Fundamentals
if(fund&&fund.metrics){
const metrics=fund.metrics;
const fundCard=document.getElementById('fundamentals-card');
const fundGrid=document.getElementById('fundamentals-grid');
const items=[];
if(metrics.pe_ratio)items.push({label:'P/E RATIO',value:metrics.pe_ratio.toFixed(2)});
if(metrics.eps)items.push({label:'EPS',value:'$'+metrics.eps.toFixed(2)});
if(metrics.beta)items.push({label:'BETA',value:metrics.beta.toFixed(2)});
if(metrics.dividend_yield)items.push({label:'DIV YIELD',value:metrics.dividend_yield.toFixed(2)+'%'});
if(metrics.high_52week)items.push({label:'52W HIGH',value:'$'+metrics.high_52week.toFixed(2)});
if(metrics.low_52week)items.push({label:'52W LOW',value:'$'+metrics.low_52week.toFixed(2)});
if(items.length>0){
fundCard.style.display='block';
fundGrid.innerHTML=items.map(i=>
`<div class="fund-item"><div class="fund-label">${i.label}</div><div class="fund-value">${i.value}</div></div>`
).join('');
}
}

// Earnings
if(earn&&earn.earnings){
const list=document.getElementById('earnings-list');
const items=earn.earnings;
if(items.length===0){
list.innerHTML='<div style="color:#666;font-size:13px">No earnings data available</div>';
}else{
list.innerHTML='';
items.slice(0,4).forEach(e=>{
const surprise=e.surprise_pct;
const surpriseClass=surprise>0?'positive':surprise<0?'negative':'';
const surpriseText=surprise?`${surprise>0?'+':''}${surprise.toFixed(1)}% surprise`:'';
const ei=document.createElement('div');
ei.className='earning-item';
ei.innerHTML=`
<div>
<div class="earning-period">${e.period||'Unknown'}</div>
<div class="earning-data">Est: $${(e.estimate||0).toFixed(2)}${e.actual!==null?' \\u00B7 Act: $'+e.actual.toFixed(2):''}</div>
</div>
<div class="earning-surprise ${surpriseClass}">${surpriseText}</div>
`;
list.appendChild(ei);
});
}
}
}

loadData();
</script>
</body>
</html>
"""


def get_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def finnhub_request(endpoint: str, params: dict) -> dict:
    """Make a request to Finnhub API with error handling."""
    api_key = FINNHUB_API_KEY or os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="FINNHUB_API_KEY not configured")
    params["token"] = api_key
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


@app.get("/")
async def root():
    """Rich HTML home page with live stock terminal"""
    return HTMLResponse(content=HOME_HTML)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/dashboard")
async def dashboard(symbol: str = Query("AAPL", description="Stock symbol (e.g., AAPL)")):
    """Dashboard endpoint - fetches all homepage data server-side in a single call."""
    results = {
        "health": None,
        "quote": None,
        "fundamentals": None,
        "earnings": None,
        "symbol": symbol,
        "timestamp": get_timestamp()
    }

    # Fetch health
    try:
        results["health"] = {"status": "healthy"}
    except Exception:
        pass

    await asyncio.sleep(0.05)

    # Fetch quote
    try:
        data = await finnhub_request("/quote", {"symbol": symbol})
        results["quote"] = {
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
    except Exception:
        pass

    await asyncio.sleep(0.05)

    # Fetch fundamentals
    try:
        profile_data = await finnhub_request("/stock/profile2", {"symbol": symbol})
        await asyncio.sleep(0.05)
        metrics_data = await finnhub_request("/stock/metric", {"symbol": symbol, "metric": "all"})

        metrics = metrics_data.get("metric", {})

        raw_mc_profile = profile_data.get("marketCapitalization")
        raw_mc_metrics = metrics.get("marketCapitalization")
        raw_shares = profile_data.get("shareOutstanding")

        mc_profile = raw_mc_profile * 1_000_000 if raw_mc_profile else raw_mc_profile
        mc_metrics = raw_mc_metrics * 1_000_000 if raw_mc_metrics else raw_mc_metrics
        shares_out = raw_shares * 1_000_000 if raw_shares else raw_shares

        results["fundamentals"] = {
            "symbol": symbol,
            "profile": {
                "name": profile_data.get("name"),
                "ticker": profile_data.get("ticker"),
                "exchange": profile_data.get("exchange"),
                "industry": profile_data.get("finnhubIndustry"),
                "market_cap": mc_profile,
                "country": profile_data.get("country"),
                "currency": profile_data.get("currency"),
                "ipo": profile_data.get("ipo"),
                "logo": profile_data.get("logo"),
                "phone": profile_data.get("phone"),
                "share_outstanding": shares_out,
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
                "market_cap": mc_metrics,
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
    except Exception:
        pass

    await asyncio.sleep(0.05)

    # Fetch earnings
    try:
        data = await finnhub_request("/stock/earnings", {"symbol": symbol})

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

        results["earnings"] = {
            "symbol": symbol,
            "earnings": earnings,
            "timestamp": get_timestamp()
        }
    except Exception:
        pass

    return results


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

    # Finnhub returns marketCapitalization and shareOutstanding in millions — convert to raw units
    raw_mc_profile = profile_data.get("marketCapitalization")
    raw_mc_metrics = metrics.get("marketCapitalization")
    raw_shares = profile_data.get("shareOutstanding")

    mc_profile = raw_mc_profile * 1_000_000 if raw_mc_profile else raw_mc_profile
    mc_metrics = raw_mc_metrics * 1_000_000 if raw_mc_metrics else raw_mc_metrics
    shares_out = raw_shares * 1_000_000 if raw_shares else raw_shares

    return {
        "symbol": symbol,
        "profile": {
            "name": profile_data.get("name"),
            "ticker": profile_data.get("ticker"),
            "exchange": profile_data.get("exchange"),
            "industry": profile_data.get("finnhubIndustry"),
            "market_cap": mc_profile,
            "country": profile_data.get("country"),
            "currency": profile_data.get("currency"),
            "ipo": profile_data.get("ipo"),
            "logo": profile_data.get("logo"),
            "phone": profile_data.get("phone"),
            "share_outstanding": shares_out,
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
            "market_cap": mc_metrics,
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

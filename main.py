import os
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

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
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finnhub Wrapper</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0a;color:#fff;padding:40px 20px;line-height:1.5}
.w{max-width:640px;margin:0 auto}
.hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.t{font-family:'Courier New',monospace;font-style:italic;font-size:28px;color:#2BBFBF;font-weight:600}
.st{display:flex;align-items:center;gap:6px;font-size:13px;color:#666;font-family:'Courier New',monospace}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e}
.sb{color:#888;font-size:14px;margin-bottom:32px}
.cd{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:24px;margin-bottom:16px;opacity:0;animation:fi .6s ease forwards}
@keyframes fi{to{opacity:1}}
.cd:nth-child(2){animation-delay:.1s}
.cd:nth-child(3){animation-delay:.2s}
.cd:nth-child(4){animation-delay:.3s}
.qh{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
.sy{font-size:32px;font-weight:700;color:#fff;font-family:'Courier New',monospace}
.cm{font-size:13px;color:#666;margin-top:4px}
.up{font-size:11px;color:#666;font-family:'Courier New',monospace;text-align:right}
.pr{font-size:48px;font-weight:700;color:#fff;margin-bottom:8px}
.ch{font-size:20px;font-weight:600;margin-bottom:16px}
.gr{color:#22c55e}
.rd{color:#ef4444}
.sp{display:flex;gap:2px;height:32px;align-items:flex-end;margin-bottom:16px}
.br{flex:1;background:rgba(43,191,191,.3);border-radius:2px;transition:all .3s}
.og{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.oi{text-align:center}
.ol{font-size:11px;color:#666;margin-bottom:4px;font-family:'Courier New',monospace}
.ov{font-size:16px;font-weight:600;color:#fff}
.sc{font-size:14px;color:#888;margin-bottom:12px;font-weight:600;letter-spacing:.5px}
.er{display:grid;gap:12px}
.ei{display:flex;justify-content:space-between;padding:12px;background:rgba(255,255,255,.02);border-radius:8px}
.ep{font-size:13px;color:#fff;font-weight:600}
.ev{font-size:13px;color:#888}
.fm{margin-top:32px}
.ix{display:flex;gap:8px;margin-bottom:12px}
.ix input{flex:1;padding:12px 16px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:14px;font-family:'Courier New',monospace}
.ix input::placeholder{color:#666}
.ix button{padding:12px 24px;background:#2BBFBF;border:none;border-radius:8px;color:#0a0a0a;font-size:16px;font-weight:600;cursor:pointer;transition:all .2s}
.ix button:hover{background:#24a8a8;transform:translateY(-1px)}
.sg{display:flex;gap:8px;font-size:13px;color:#666;flex-wrap:wrap}
.sg span{cursor:pointer;transition:color .2s}
.sg span:hover{color:#2BBFBF}
.rs{margin-top:16px;padding:16px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;display:none}
.rs.show{display:block}
.ld{color:#888;font-size:13px;font-style:italic}
.er-msg{color:#ef4444;font-size:13px}
</style>
</head>
<body>
<div class="w">
<div class="hd">
<div class="t">Finnhub</div>
<div class="st"><span class="dot"></span><span id="health-status">checking...</span></div>
</div>
<div class="sb">Real-time stock quotes, fundamentals, earnings, and news</div>

<div class="cd" id="quote-card">
<div class="qh">
<div>
<div class="sy" id="symbol">AAPL</div>
<div class="cm" id="company">Loading...</div>
</div>
<div class="up" id="update-time">--:--:--</div>
</div>
<div class="pr" id="price">--</div>
<div class="ch" id="change">--</div>
<div class="sp" id="sparkline"></div>
<div class="og">
<div class="oi"><div class="ol">OPEN</div><div class="ov" id="open">--</div></div>
<div class="oi"><div class="ol">HIGH</div><div class="ov" id="high">--</div></div>
<div class="oi"><div class="ol">LOW</div><div class="ov" id="low">--</div></div>
<div class="oi"><div class="ol">PREV CLOSE</div><div class="ov" id="prev">--</div></div>
</div>
</div>

<div class="cd" id="earnings-card">
<div class="sc">UPCOMING EARNINGS</div>
<div class="er" id="earnings-list">
<div class="ld">Loading earnings data...</div>
</div>
</div>

<div class="fm">
<div class="ix">
<input type="text" id="symbol-input" placeholder="AAPL" maxlength="10">
<button onclick="fetchSymbol()">\\u2192 quote</button>
</div>
<div class="sg">
Try: <span onclick="trySymbol('TSLA')">TSLA</span> \\u00B7
<span onclick="trySymbol('MSFT')">MSFT</span> \\u00B7
<span onclick="trySymbol('GOOGL')">GOOGL</span> \\u00B7
<span onclick="trySymbol('NVDA')">NVDA</span> \\u00B7
<span onclick="trySymbol('META')">META</span>
</div>
<div class="rs" id="result"></div>
</div>
</div>

<script>
let currentSymbol='AAPL';

function trySymbol(sym){document.getElementById('symbol-input').value=sym;fetchSymbol()}

function fetchSymbol(){
const input=document.getElementById('symbol-input');
const sym=input.value.trim().toUpperCase();
if(!sym)return;
const resultDiv=document.getElementById('result');
resultDiv.className='rs show';
resultDiv.innerHTML='<div class="ld">Fetching '+sym+'...</div>';
fetch('/quote?symbol='+sym)
.then(r=>r.ok?r.json():r.json().then(e=>{throw new Error(e.detail||'Unknown error')}))
.then(d=>{
const chg=d.change||0;
const pct=d.percent_change||0;
const cls=chg>=0?'gr':'rd';
const arr=chg>=0?'\\u25B2':'\\u25BC';
resultDiv.innerHTML=`
<div style="font-size:20px;font-weight:700;margin-bottom:8px">${sym}</div>
<div style="font-size:32px;font-weight:700;margin-bottom:8px">$${(d.current_price||0).toFixed(2)}</div>
<div class="${cls}" style="font-size:16px;font-weight:600">${arr} $${Math.abs(chg).toFixed(2)} (${pct.toFixed(2)}%)</div>
`;
})
.catch(e=>{resultDiv.innerHTML='<div class="er-msg">Error: '+e.message+'</div>'});
}

document.getElementById('symbol-input').addEventListener('keypress',e=>{if(e.key==='Enter')fetchSymbol()});

async function loadData(){
const t0=Date.now();
const results=await Promise.allSettled([
fetch('/health').then(r=>r.json()),
fetch('/quote?symbol='+currentSymbol).then(r=>r.json()),
fetch('/fundamentals?symbol='+currentSymbol).then(r=>r.json()),
fetch('/earnings?symbol='+currentSymbol).then(r=>r.json())
]);
const latency=Date.now()-t0;

const health=results[0].status==='fulfilled'?results[0].value:null;
const quote=results[1].status==='fulfilled'?results[1].value:null;
const fund=results[2].status==='fulfilled'?results[2].value:null;
const earn=results[3].status==='fulfilled'?results[3].value:null;

if(health){
const st=document.getElementById('health-status');
st.innerHTML='online \\u00B7 '+latency+'ms';
st.style.color='#22c55e';
}

if(quote){
document.getElementById('price').textContent='$'+(quote.current_price||0).toFixed(2);
const chg=quote.change||0;
const pct=quote.percent_change||0;
const cls=chg>=0?'gr':'rd';
const arr=chg>=0?'\\u25B2':'\\u25BC';
document.getElementById('change').innerHTML=`<span class="${cls}">${arr} $${Math.abs(chg).toFixed(2)} (${pct.toFixed(2)}%)</span>`;
document.getElementById('open').textContent='$'+(quote.open||0).toFixed(2);
document.getElementById('high').textContent='$'+(quote.high||0).toFixed(2);
document.getElementById('low').textContent='$'+(quote.low||0).toFixed(2);
document.getElementById('prev').textContent='$'+(quote.previous_close||0).toFixed(2);

const now=new Date();
document.getElementById('update-time').textContent=now.toTimeString().split(' ')[0];

const vals=[quote.open||0,quote.high||0,quote.low||0,quote.current_price||0,quote.previous_close||0];
const mn=Math.min(...vals);
const mx=Math.max(...vals);
const rng=mx-mn||1;
const sp=document.getElementById('sparkline');
sp.innerHTML='';
vals.forEach(v=>{
const h=((v-mn)/rng*100)||10;
const bar=document.createElement('div');
bar.className='br';
bar.style.height=h+'%';
bar.style.background=v>=(quote.previous_close||0)?'rgba(34,197,94,.6)':'rgba(239,68,68,.6)';
sp.appendChild(bar);
});
}

if(fund&&fund.profile){
const prof=fund.profile;
const name=prof.name||currentSymbol;
const exch=prof.exchange||'NASDAQ';
document.getElementById('company').textContent=name+' \\u00B7 '+exch;
}

if(earn&&earn.earnings){
const list=document.getElementById('earnings-list');
const items=earn.earnings;
if(items.length===0){
list.innerHTML='<div class="ev">No earnings data available</div>';
}else{
list.innerHTML='';
items.slice(0,3).forEach(e=>{
const surprise=e.surprise_pct?` (${e.surprise_pct>0?'+':''}${e.surprise_pct.toFixed(1)}% surprise)`:'';
const ei=document.createElement('div');
ei.className='ei';
ei.innerHTML=`
<div>
<div class="ep">${e.period||'Unknown'}</div>
<div class="ev">Est: $${(e.estimate||0).toFixed(2)}${e.actual!==null?' | Act: $'+e.actual.toFixed(2):''}</div>
</div>
<div class="ev">${surprise}</div>
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

"""
PolyCopy — Smart Money Tracker + Late Sharp Money Detector
==========================================================
Tab 1: Smart Money Tracker
  - Scans active markets for top-performing wallets
  - Ranks by win rate × ROI × trade volume
  - Shows their CURRENT open positions → tells you exactly what to copy

Tab 2: Late Sharp Money Detector
  - Scans markets closing within 24h
  - Detects wallets that placed large bets recently
  - Flags sudden price moves caused by sharp bettors

Tab 3: Mispricing Scanner
  - Finds markets where YES + NO ≠ ~$1.00
  - Flags arbitrage and structural mispricings

Run: streamlit run smart_money.py
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time

st.set_page_config(
    page_title="PolyCopy — Smart Money",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#05080f;}
section[data-testid="stSidebar"]{background:#080c14!important;border-right:1px solid #0f1825;}
section[data-testid="stSidebar"] *{color:#8a9bb0!important;}
[data-testid="metric-container"]{background:#080c14;border:1px solid #0f1825;border-radius:10px;padding:14px!important;}
[data-testid="metric-container"] label{font-family:'Space Mono',monospace!important;font-size:8px!important;text-transform:uppercase;letter-spacing:1.5px;color:#2a3a4c!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;font-size:18px!important;color:#f0f8ff!important;}
.stButton>button{background:linear-gradient(135deg,#7c3aed,#4f46e5)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Syne',sans-serif!important;font-weight:800!important;text-transform:uppercase!important;letter-spacing:.8px!important;padding:10px 24px!important;}
.stButton>button:hover{background:linear-gradient(135deg,#9333ea,#6366f1)!important;box-shadow:0 4px 20px rgba(124,58,237,0.4)!important;}
.stTabs [data-baseweb="tab-list"]{background:#080c14;border-bottom:1px solid #0f1825;gap:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#3a4a5c;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;border:none;padding:10px 20px;}
.stTabs [aria-selected="true"]{background:#0f1825!important;color:#a78bfa!important;border-radius:6px 6px 0 0;}

/* Wallet card */
.wallet-card{background:#080c14;border:1px solid #0f1825;border-radius:12px;padding:16px 18px;margin-bottom:10px;transition:border-color .2s;}
.wallet-card:hover{border-color:rgba(124,58,237,0.4);}
.wallet-card.top{border-color:rgba(124,58,237,0.5);box-shadow:0 0 20px rgba(124,58,237,0.1);}
.wallet-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.wallet-avatar{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#06b6d4);display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;color:#fff;flex-shrink:0;}
.wallet-addr{font-family:'Space Mono',monospace;font-size:11px;color:#a78bfa;margin-left:10px;}
.wallet-score{font-family:'Space Mono',monospace;font-size:13px;font-weight:700;color:#f0f8ff;}
.wallet-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;}
.wstat{display:flex;flex-direction:column;gap:2px;background:#0a0e18;border:1px solid #0f1825;border-radius:7px;padding:8px 10px;}
.wstat-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;}
.wstat-value{font-family:'Space Mono',monospace;font-size:13px;font-weight:700;color:#f0f8ff;}
.wstat-value.green{color:#00e676;}.wstat-value.purple{color:#a78bfa;}.wstat-value.orange{color:#fb923c;}
.positions-label{font-family:'Space Mono',monospace;font-size:8px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;}

/* Position pill */
.pos-pill{display:inline-flex;align-items:center;gap:6px;background:#0f1825;border:1px solid #1a2535;border-radius:6px;padding:5px 10px;margin:3px;font-family:'Space Mono',monospace;font-size:9px;}
.pos-pill.yes{border-color:rgba(0,230,118,0.3);color:#00e676;}
.pos-pill.no{border-color:rgba(255,82,82,0.3);color:#ff5252;}

/* Sharp money card */
.sharp-card{background:#080c14;border-left:3px solid #fb923c;border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:10px;}
.sharp-card.high{border-left-color:#ff5252;}
.sharp-card.med{border-left-color:#fb923c;}
.sharp-q{font-size:13px;font-weight:600;color:#f0f8ff;line-height:1.4;margin-bottom:10px;}
.sharp-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:8px;}
.sharp-metric{display:flex;flex-direction:column;gap:2px;}
.sharp-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;}
.sharp-value{font-family:'Space Mono',monospace;font-size:12px;font-weight:700;color:#f0f8ff;}
.sharp-value.up{color:#00e676;}.sharp-value.down{color:#ff5252;}.sharp-value.warn{color:#fb923c;}

/* Mispricing card */
.misprice-card{background:#080c14;border:1px solid #0f1825;border-radius:10px;padding:14px 16px;margin-bottom:10px;}
.misprice-card.arb{border-color:rgba(251,146,60,0.4);}
.misprice-card.extreme{border-color:rgba(255,82,82,0.5);box-shadow:0 0 16px rgba(255,82,82,0.08);}
.mp-q{font-size:13px;font-weight:600;color:#f0f8ff;line-height:1.4;margin-bottom:10px;}
.mp-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.mp-metric{display:flex;flex-direction:column;gap:2px;}
.mp-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;}
.mp-value{font-family:'Space Mono',monospace;font-size:13px;font-weight:700;color:#f0f8ff;}
.mp-value.arb{color:#fb923c;}.mp-value.green{color:#00e676;}.mp-value.red{color:#ff5252;}

/* Tag / badge */
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-family:'Space Mono',monospace;font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;}
.badge-purple{background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);color:#a78bfa;}
.badge-green{background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.25);color:#00e676;}
.badge-orange{background:rgba(251,146,60,0.1);border:1px solid rgba(251,146,60,0.3);color:#fb923c;}
.badge-red{background:rgba(255,82,82,0.1);border:1px solid rgba(255,82,82,0.3);color:#ff5252;}

.section-title{font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#f0f8ff;margin-bottom:4px;}
.section-sub{font-family:'Space Mono',monospace;font-size:9px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px;}
.log{background:#0a0e18;border:1px solid #0f1825;border-radius:8px;padding:10px 14px;font-family:'Space Mono',monospace;font-size:9px;color:#3a4a5c;line-height:2;max-height:120px;overflow-y:auto;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
GAMMA = "https://gamma-api.polymarket.com"
DATA  = "https://data-api.polymarket.com"
CLOB  = "https://clob.polymarket.com"
HDR   = {"Accept": "application/json", "User-Agent": "PolyCopy/2.0"}

# ─────────────────────────────────────────────
#  API HELPERS
# ─────────────────────────────────────────────
def get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HDR, params=params, timeout=15)
            if r.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None

def fmt_addr(addr):
    if not addr or len(addr) < 10: return addr or "???"
    return addr[:6] + "…" + addr[-4:]

def fmt_usdc(val):
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:.0f}"

def ts_to_dt(ts):
    if not ts: return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except: return None

def hours_left(end_raw):
    dt = ts_to_dt(end_raw)
    if not dt: return None
    return (dt - datetime.now(timezone.utc)).total_seconds() / 3600

# ─────────────────────────────────────────────
#  FETCH ACTIVE MARKETS
# ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def fetch_markets(limit=200):
    data = get(f"{GAMMA}/markets", {
        "active": "true", "closed": "false", "limit": limit,
        "order": "volume", "ascending": "false"
    })
    if not data: return []
    return data if isinstance(data, list) else data.get("markets", [])

@st.cache_data(ttl=120)
def fetch_closing_markets(hours=24, limit=150):
    now    = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours)
    data   = get(f"{GAMMA}/markets", {
        "active": "true", "closed": "false",
        "end_date_min": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_date_max": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": limit,
    })
    if not data: return []
    return data if isinstance(data, list) else data.get("markets", [])

# ─────────────────────────────────────────────
#  SCORE A WALLET
# ─────────────────────────────────────────────
_wallet_cache = {}

def score_wallet(address, min_trades=8):
    if address in _wallet_cache:
        return _wallet_cache[address]

    base = {"address": address, "win_rate": 0, "roi": 0, "total": 0,
            "wins": 0, "losses": 0, "profit_usdc": 0, "score": 0}

    data = get(f"{DATA}/positions", {"user": address, "closed": "true", "limit": 500})
    if not data:
        _wallet_cache[address] = base
        return base

    positions = data if isinstance(data, list) else data.get("positions", [])
    resolved  = [p for p in positions if p.get("redeemable") or p.get("resolved") or p.get("closed")]

    if len(resolved) < min_trades:
        _wallet_cache[address] = base
        return base

    wins=0; losses=0; rois=[]; profit=0
    for p in resolved:
        buy = float(p.get("initialValue") or p.get("cost") or 0)
        end = float(p.get("currentValue") or p.get("value") or 0)
        if buy > 0:
            roi = (end - buy) / buy
            rois.append(roi)
            profit += (end - buy)
            if roi > 0: wins += 1
            else:       losses += 1
        elif p.get("winner") is True or p.get("redeemable") is True:
            wins += 1
        else:
            losses += 1

    total = wins + losses
    if not total:
        _wallet_cache[address] = base
        return base

    wr      = wins / total
    avg_roi = sum(rois) / len(rois) if rois else 0
    # Composite score: win rate weighted by number of trades and roi
    score   = round(wr * 100 * (1 + max(avg_roi, 0)) * min(total / 30, 1), 1)

    result = {
        "address":     address,
        "win_rate":    round(wr, 4),
        "roi":         round(avg_roi, 4),
        "total":       total,
        "wins":        wins,
        "losses":      losses,
        "profit_usdc": round(profit, 2),
        "score":       score,
    }
    _wallet_cache[address] = result
    return result

# ─────────────────────────────────────────────
#  GET OPEN POSITIONS FOR A WALLET
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_open_positions(address):
    data = get(f"{DATA}/positions", {"user": address, "closed": "false", "limit": 100})
    if not data: return []
    positions = data if isinstance(data, list) else data.get("positions", [])
    return [p for p in positions if float(p.get("size") or p.get("quantity") or 0) > 0]

# ─────────────────────────────────────────────
#  SMART MONEY SCAN
# ─────────────────────────────────────────────
def run_smart_money_scan(markets, min_wr, min_trades, min_roi, top_n, log_ph):
    logs = []
    def log(msg):
        logs.append(f"› {msg}")
        log_ph.markdown(
            '<div class="log">' + "".join(f"<div>{l}</div>" for l in logs[-15:]) + '</div>',
            unsafe_allow_html=True
        )

    log(f"Scanning {len(markets)} active markets for smart money...")
    wallet_hits = {}  # address → {score_data, markets_seen}

    for i, market in enumerate(markets[:60]):  # cap at 60 markets to avoid rate limits
        cid      = market.get("conditionId") or market.get("id")
        question = (market.get("question") or market.get("title") or "")[:60]
        if not cid: continue

        log(f"[{i+1}/60] {question}...")

        data = get(f"{DATA}/trades", {"market": cid, "limit": 200})
        if not data: continue
        trades = data if isinstance(data, list) else data.get("trades", [])

        wallets = set()
        for t in trades:
            for field in ("maker", "taker", "transactor", "user"):
                addr = t.get(field)
                if addr: wallets.add(addr.lower())

        for addr in list(wallets)[:20]:
            if addr in wallet_hits:
                wallet_hits[addr]["markets_active"].add(cid)
                continue
            profile = score_wallet(addr, min_trades)
            if (profile["total"] >= min_trades and
                profile["win_rate"] >= min_wr and
                profile["roi"] >= min_roi):
                wallet_hits[addr] = {**profile, "markets_active": {cid}}
                log(f"  ✦ Found: {fmt_addr(addr)} — {round(profile['win_rate']*100)}% WR, score {profile['score']}")

    log(f"Scan complete — {len(wallet_hits)} smart wallets found.")
    return sorted(wallet_hits.values(), key=lambda x: x["score"], reverse=True)[:top_n]

# ─────────────────────────────────────────────
#  LATE SHARP MONEY SCAN
# ─────────────────────────────────────────────
def run_sharp_scan(markets, hours_window, min_wr, min_trade_size, log_ph):
    logs = []
    def log(msg):
        logs.append(f"› {msg}")
        log_ph.markdown(
            '<div class="log">' + "".join(f"<div>{l}</div>" for l in logs[-15:]) + '</div>',
            unsafe_allow_html=True
        )

    log(f"Scanning {len(markets)} markets closing within {hours_window}h for sharp bets...")
    results = []
    cutoff_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()

    for i, market in enumerate(markets):
        cid      = market.get("conditionId") or market.get("id")
        question = (market.get("question") or market.get("title") or "")[:80]
        end_raw  = market.get("endDate") or market.get("end_date") or market.get("resolveDate")
        hl       = hours_left(end_raw)
        if not cid or hl is None or hl < 0: continue

        log(f"[{i+1}/{len(markets)}] {question[:50]}... ({hl:.1f}h left)")

        # Get recent trades
        data = get(f"{DATA}/trades", {"market": cid, "limit": 500})
        if not data: continue
        trades = data if isinstance(data, list) else data.get("trades", [])
        if not trades: continue

        # Filter to trades in the last 2 hours
        recent = []
        for t in trades:
            ts = t.get("timestamp") or t.get("createdAt") or t.get("created_at")
            if ts:
                try:
                    t_ts = float(ts) if isinstance(ts, (int, float)) else datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
                    if t_ts >= cutoff_ts:
                        recent.append(t)
                except: pass

        if not recent: continue

        # Score traders behind recent trades
        sharp_traders = []
        seen = set()
        for t in recent:
            for field in ("maker", "taker", "transactor", "user"):
                addr = (t.get(field) or "").lower()
                if addr and addr not in seen:
                    seen.add(addr)
                    profile = score_wallet(addr, 5)
                    if profile["total"] >= 5 and profile["win_rate"] >= min_wr:
                        trade_size = float(t.get("size") or t.get("amount") or t.get("usdcSize") or 0)
                        if trade_size >= min_trade_size:
                            sharp_traders.append({
                                "address":   addr,
                                "win_rate":  profile["win_rate"],
                                "total":     profile["total"],
                                "trade_size": trade_size,
                                "outcome":   t.get("outcome") or t.get("side") or "?",
                            })

        if not sharp_traders: continue

        # Get prices from market metadata
        tokens  = market.get("tokens", []) or []
        yes_p   = no_p = None
        for tok in tokens:
            if not isinstance(tok, dict): continue
            out = (tok.get("outcome") or "").upper()
            p   = tok.get("price") or tok.get("lastTradePrice")
            if p:
                if "YES" in out: yes_p = float(p)
                if "NO"  in out: no_p  = float(p)

        # Price sum deviation
        price_sum = (yes_p or 0) + (no_p or 0)

        # Total sharp volume in last 2h
        sharp_vol   = sum(st["trade_size"] for st in sharp_traders)
        best_trader = max(sharp_traders, key=lambda x: x["win_rate"])

        urgency = "high" if hl < 3 else "med"

        results.append({
            "question":    question,
            "conditionId": cid,
            "hours_left":  round(hl, 1),
            "yes_price":   yes_p,
            "no_price":    no_p,
            "price_sum":   round(price_sum, 3),
            "sharp_vol":   round(sharp_vol, 2),
            "sharp_count": len(sharp_traders),
            "best_wr":     best_trader["win_rate"],
            "best_addr":   best_trader["address"],
            "sharp_side":  best_trader["outcome"],
            "urgency":     urgency,
            "url":         f"https://polymarket.com/event/{cid}",
        })
        log(f"  ★ Sharp activity! {len(sharp_traders)} smart traders, ${sharp_vol:.0f} volume, {hl:.1f}h left")

    log(f"Done — {len(results)} markets with sharp activity found.")
    return sorted(results, key=lambda x: (x["urgency"] == "high", x["best_wr"], x["sharp_vol"]), reverse=True)

# ─────────────────────────────────────────────
#  MISPRICING SCAN
# ─────────────────────────────────────────────
@st.cache_data(ttl=180)
def run_mispricing_scan():
    markets = fetch_markets(300)
    results = []
    for m in markets:
        tokens = m.get("tokens", []) or []
        yes_p = no_p = None
        for tok in tokens:
            if not isinstance(tok, dict): continue
            out = (tok.get("outcome") or "").upper()
            p   = tok.get("price") or tok.get("lastTradePrice")
            if p:
                if "YES" in out: yes_p = float(p)
                if "NO"  in out: no_p  = float(p)

        if yes_p is None or no_p is None: continue
        price_sum = yes_p + no_p
        deviation = abs(price_sum - 1.0)
        if deviation < 0.02: continue  # within normal fee range

        cid      = m.get("conditionId") or m.get("id")
        question = (m.get("question") or m.get("title") or "")[:80]
        end_raw  = m.get("endDate") or m.get("end_date")
        hl       = hours_left(end_raw)
        vol      = float(m.get("volumeNum") or m.get("volume") or 0)

        severity = "extreme" if deviation > 0.08 else "arb"

        results.append({
            "question":    question,
            "conditionId": cid,
            "yes_price":   yes_p,
            "no_price":    no_p,
            "price_sum":   round(price_sum, 4),
            "deviation":   round(deviation, 4),
            "hours_left":  round(hl, 1) if hl else None,
            "volume":      vol,
            "severity":    severity,
            "url":         f"https://polymarket.com/event/{cid}",
        })

    return sorted(results, key=lambda x: x["deviation"], reverse=True)[:50]

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ PolyCopy Settings")
    st.markdown("---")
    st.markdown("**Smart Money Filters**")
    min_wr     = st.slider("Min Win Rate",    60, 99, 75, 1, format="%d%%") / 100
    min_trades = st.slider("Min Trade History", 5, 50, 10, 5)
    min_roi    = st.slider("Min Avg ROI",    -20, 50, 0, 5, format="%d%%") / 100
    top_n      = st.slider("Top N Wallets",   5, 50, 20, 5)
    st.markdown("---")
    st.markdown("**Sharp Money Filters**")
    sharp_hours     = st.slider("Closes within",  1, 48, 24, 1, format="%dh")
    sharp_min_wr    = st.slider("Trader Win Rate", 60, 99, 70, 1, format="%d%%") / 100
    sharp_min_size  = st.slider("Min Trade Size ($)", 10, 500, 50, 10)
    st.markdown("---")
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:9px;color:#2a3a4c;line-height:2;'>
    ⚠ NOT FINANCIAL ADVICE<br>
    Educational use only.<br>
    Past performance does not<br>
    guarantee future results.
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:#f0f8ff;margin-bottom:2px;'>
  Poly<span style='color:#a78bfa;'>Copy</span> Smart Money
</div>
<div style='font-family:Space Mono,monospace;font-size:9px;color:#2a3a4c;text-transform:uppercase;
     letter-spacing:2px;margin-bottom:20px;'>
  Smart Wallet Tracker &nbsp;·&nbsp; Late Sharp Money Detector &nbsp;·&nbsp; Mispricing Scanner
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🧠  Smart Money Tracker",
    "⚡  Late Sharp Money",
    "🔍  Mispricing Scanner",
])

# ══════════════════════════════════════════════
#  TAB 1 — SMART MONEY TRACKER
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-title">Smart Money Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Finds wallets with proven track records and shows exactly what they\'re betting on right now</div>', unsafe_allow_html=True)

    col_scan, _ = st.columns([1, 4])
    with col_scan:
        scan1 = st.button("🔍 Scan Smart Wallets", key="scan1", use_container_width=True)

    log_ph1 = st.empty()

    if "smart_results" not in st.session_state:
        st.session_state.smart_results = []

    if scan1:
        st.session_state.smart_results = []
        markets = fetch_markets(200)
        with st.spinner(""):
            results = run_smart_money_scan(markets, min_wr, min_trades, min_roi, top_n, log_ph1)
        st.session_state.smart_results = results
        st.rerun()

    wallets = st.session_state.smart_results

    if not wallets:
        st.markdown("""
        <div style='background:#080c14;border:1px dashed #0f1825;border-radius:12px;padding:50px;text-align:center;'>
          <div style='font-size:32px;opacity:.3;margin-bottom:12px;'>◈</div>
          <div style='font-size:16px;font-weight:700;color:#f0f8ff;margin-bottom:8px;'>No results yet</div>
          <div style='font-family:Space Mono,monospace;font-size:11px;color:#2a3a4c;line-height:1.8;'>
            Click <b style='color:#a78bfa;'>Scan Smart Wallets</b> to find top traders<br>
            and see their current open positions.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary metrics
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.metric("Wallets Found",  len(wallets))
        with m2: st.metric("Avg Win Rate",   f"{round(sum(w['win_rate'] for w in wallets)/len(wallets)*100)}%")
        with m3: st.metric("Avg ROI",        f"{round(sum(w['roi'] for w in wallets)/len(wallets)*100,1)}%")
        with m4: st.metric("Top Score",      wallets[0]["score"] if wallets else "—")
        st.markdown("---")

        for i, wallet in enumerate(wallets):
            is_top = i < 3
            addr   = wallet["address"]
            wr_pct = round(wallet["win_rate"] * 100, 1)
            roi_pct= round(wallet["roi"] * 100, 1)
            avatar = addr[2:4].upper() if len(addr) >= 4 else "??"

            # Fetch open positions for this wallet
            open_pos = get_open_positions(addr)

            pos_html = ""
            if open_pos:
                for pos in open_pos[:6]:
                    outcome = (pos.get("outcome") or pos.get("side") or "").upper()
                    mkt_q   = (pos.get("title") or pos.get("market") or pos.get("condition") or "")[:40]
                    size    = float(pos.get("size") or pos.get("quantity") or pos.get("currentValue") or 0)
                    side_cls= "yes" if ("YES" in outcome or "UP" in outcome) else "no"
                    pos_html += f"<span class='pos-pill {side_cls}'>{outcome or '?'} {fmt_usdc(size) if size else ''} {mkt_q}</span>"
            else:
                pos_html = "<span style='font-family:Space Mono,monospace;font-size:9px;color:#2a3a4c;'>No open positions found (may be private)</span>"

            top_badge = f"<span class='badge badge-purple' style='margin-left:8px;'>#{i+1} RANKED</span>" if is_top else ""

            st.markdown(f"""
            <div class='wallet-card {"top" if is_top else ""}'>
              <div class='wallet-header'>
                <div style='display:flex;align-items:center;'>
                  <div class='wallet-avatar'>{avatar}</div>
                  <div>
                    <span class='wallet-addr'>{fmt_addr(addr)}</span>
                    {top_badge}
                  </div>
                </div>
                <div class='wallet-score'>Score: {wallet["score"]}</div>
              </div>
              <div class='wallet-stats'>
                <div class='wstat'><div class='wstat-label'>Win Rate</div><div class='wstat-value green'>{wr_pct}%</div></div>
                <div class='wstat'><div class='wstat-label'>Avg ROI</div><div class='wstat-value {"green" if roi_pct>=0 else "red"}'>{roi_pct:+.1f}%</div></div>
                <div class='wstat'><div class='wstat-label'>Trades</div><div class='wstat-value purple'>{wallet["total"]}</div></div>
                <div class='wstat'><div class='wstat-label'>W / L</div><div class='wstat-value orange'>{wallet["wins"]}W / {wallet["losses"]}L</div></div>
              </div>
              <div class='positions-label'>Current Open Positions</div>
              <div>{pos_html}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([2, 1])
            with c2:
                st.markdown(
                    f'<a href="https://polymarket.com/profile/{addr}" target="_blank" '
                    f'style="font-family:Space Mono,monospace;font-size:9px;color:#a78bfa;text-decoration:none;">↗ View on Polymarket</a>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════
#  TAB 2 — LATE SHARP MONEY
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Late Sharp Money Detector</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Markets closing soon where proven traders just placed large bets — the strongest signal there is</div>', unsafe_allow_html=True)

    col_scan2, _ = st.columns([1, 4])
    with col_scan2:
        scan2 = st.button("⚡ Detect Sharp Money", key="scan2", use_container_width=True)

    log_ph2 = st.empty()

    if "sharp_results" not in st.session_state:
        st.session_state.sharp_results = []

    if scan2:
        st.session_state.sharp_results = []
        closing_markets = fetch_closing_markets(sharp_hours)
        with st.spinner(""):
            results2 = run_sharp_scan(closing_markets, sharp_hours, sharp_min_wr, sharp_min_size, log_ph2)
        st.session_state.sharp_results = results2
        st.rerun()

    sharp = st.session_state.sharp_results

    if not sharp:
        st.markdown("""
        <div style='background:#080c14;border:1px dashed #0f1825;border-radius:12px;padding:50px;text-align:center;'>
          <div style='font-size:32px;opacity:.3;margin-bottom:12px;'>⚡</div>
          <div style='font-size:16px;font-weight:700;color:#f0f8ff;margin-bottom:8px;'>No results yet</div>
          <div style='font-family:Space Mono,monospace;font-size:11px;color:#2a3a4c;line-height:1.8;'>
            Click <b style='color:#a78bfa;'>Detect Sharp Money</b> to scan markets closing<br>
            within the next {sharp_hours}h for big bets by proven traders.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        m1,m2,m3 = st.columns(3)
        with m1: st.metric("Markets With Sharp Activity", len(sharp))
        with m2: st.metric("Urgent (<3h)",  sum(1 for s in sharp if s["urgency"]=="high"))
        with m3: st.metric("Best Trader WR", f"{round(max(s['best_wr'] for s in sharp)*100)}%" if sharp else "—")
        st.markdown("---")

        for s in sharp:
            urgency_badge = (
                "<span class='badge badge-red' style='margin-right:6px;'>🔴 URGENT &lt;3H</span>"
                if s["urgency"] == "high" else
                "<span class='badge badge-orange' style='margin-right:6px;'>🟡 CLOSING SOON</span>"
            )
            side_cls = "up" if s["sharp_side"] and ("YES" in str(s["sharp_side"]).upper() or "BUY" in str(s["sharp_side"]).upper()) else "down"
            side_txt = str(s["sharp_side"]).upper() if s["sharp_side"] else "?"

            yes_str = f"{s['yes_price']:.3f}" if s["yes_price"] else "—"
            no_str  = f"{s['no_price']:.3f}"  if s["no_price"]  else "—"

            st.markdown(f"""
            <div class='sharp-card {s["urgency"]}'>
              <div style='margin-bottom:8px;'>{urgency_badge}</div>
              <div class='sharp-q'>{s["question"]}</div>
              <div class='sharp-grid'>
                <div class='sharp-metric'>
                  <div class='sharp-label'>Closes In</div>
                  <div class='sharp-value warn'>{s["hours_left"]}h</div>
                </div>
                <div class='sharp-metric'>
                  <div class='sharp-label'>Sharp Traders</div>
                  <div class='sharp-value'>{s["sharp_count"]}</div>
                </div>
                <div class='sharp-metric'>
                  <div class='sharp-label'>Sharp Volume</div>
                  <div class='sharp-value'>{fmt_usdc(s["sharp_vol"])}</div>
                </div>
                <div class='sharp-metric'>
                  <div class='sharp-label'>Best Trader WR</div>
                  <div class='sharp-value up'>{round(s["best_wr"]*100)}%</div>
                </div>
                <div class='sharp-metric'>
                  <div class='sharp-label'>Betting Side</div>
                  <div class='sharp-value {side_cls}'>{side_txt}</div>
                </div>
              </div>
              <div style='display:flex;gap:10px;'>
                <span class='badge badge-green'>YES {yes_str}</span>
                <span class='badge badge-red'>NO {no_str}</span>
                <span class='badge badge-purple'>Trader: {fmt_addr(s["best_addr"])}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([3, 1])
            with c2:
                st.markdown(
                    f'<a href="{s["url"]}" target="_blank" '
                    f'style="font-family:Space Mono,monospace;font-size:9px;color:#a78bfa;text-decoration:none;">↗ Open Market</a>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════
#  TAB 3 — MISPRICING SCANNER
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Mispricing Scanner</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Markets where YES + NO ≠ $1.00 — structural edge you can exploit</div>', unsafe_allow_html=True)

    col_scan3, _ = st.columns([1, 4])
    with col_scan3:
        scan3 = st.button("🔍 Scan Mispricings", key="scan3", use_container_width=True)

    if "misprice_results" not in st.session_state:
        st.session_state.misprice_results = []

    if scan3:
        with st.spinner("Scanning 300 active markets for mispricings..."):
            st.session_state.misprice_results = run_mispricing_scan()
        st.rerun()

    mispricings = st.session_state.misprice_results

    if not mispricings:
        st.markdown("""
        <div style='background:#080c14;border:1px dashed #0f1825;border-radius:12px;padding:50px;text-align:center;'>
          <div style='font-size:32px;opacity:.3;margin-bottom:12px;'>🔍</div>
          <div style='font-size:16px;font-weight:700;color:#f0f8ff;margin-bottom:8px;'>No results yet</div>
          <div style='font-family:Space Mono,monospace;font-size:11px;color:#2a3a4c;line-height:1.8;'>
            Click <b style='color:#a78bfa;'>Scan Mispricings</b> to find markets<br>
            where YES + NO prices don't add up to $1.00.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        extreme = [m for m in mispricings if m["severity"] == "extreme"]
        arb     = [m for m in mispricings if m["severity"] == "arb"]

        m1,m2,m3 = st.columns(3)
        with m1: st.metric("Total Mispricings", len(mispricings))
        with m2: st.metric("Extreme (>8%)",     len(extreme))
        with m3: st.metric("Largest Deviation",
                            f"{round(mispricings[0]['deviation']*100,1)}%" if mispricings else "—")
        st.markdown("---")

        st.markdown("**How to read this:** If YES + NO < $1.00, you can buy BOTH sides and lock in a guaranteed profit when the market resolves. If YES + NO > $1.00, one side is overpriced.")

        for mp in mispricings:
            total     = mp["price_sum"]
            dev_pct   = round(mp["deviation"] * 100, 2)
            arb_profit= round((1 - total) * 100, 2) if total < 1 else 0
            hl_str    = f"{mp['hours_left']:.1f}h" if mp["hours_left"] else "—"

            if total < 1:
                edge_txt = f"BUY BOTH → +{arb_profit:.1f}% guaranteed"
                edge_cls = "green"
            else:
                edge_txt = f"Overpriced by {dev_pct:.1f}%"
                edge_cls = "arb"

            st.markdown(f"""
            <div class='misprice-card {mp["severity"]}'>
              <div class='mp-q'>{mp["question"]}</div>
              <div class='mp-grid'>
                <div class='mp-metric'>
                  <div class='mp-label'>YES Price</div>
                  <div class='mp-value'>{mp["yes_price"]:.3f}</div>
                </div>
                <div class='mp-metric'>
                  <div class='mp-label'>NO Price</div>
                  <div class='mp-value'>{mp["no_price"]:.3f}</div>
                </div>
                <div class='mp-metric'>
                  <div class='mp-label'>Sum (should be ~1)</div>
                  <div class='mp-value {"red" if total > 1 else "green"}'>{total:.4f}</div>
                </div>
                <div class='mp-metric'>
                  <div class='mp-label'>Edge</div>
                  <div class='mp-value {edge_cls}'>{edge_txt}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([3, 1])
            with c2:
                cid = mp.get("conditionId", "")
                if cid:
                    st.markdown(
                        f'<a href="{mp["url"]}" target="_blank" '
                        f'style="font-family:Space Mono,monospace;font-size:9px;color:#a78bfa;text-decoration:none;">↗ Open Market</a>',
                        unsafe_allow_html=True
                    )

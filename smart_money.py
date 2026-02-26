"""
PolyCopy — Smart Money Tracker
================================
Pulls the Polymarket leaderboard (top traders by PnL or volume),
shows their stats, and reveals exactly what they're currently betting on.

Data source: data-api.polymarket.com/v1/leaderboard (official endpoint)
No scraping, no guessing — this is the real leaderboard.

Run: streamlit run smart_money.py
"""

import streamlit as st
import requests
import time
from datetime import datetime, timezone

st.set_page_config(
    page_title="PolyCopy — Smart Money",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#05080f;}
section[data-testid="stSidebar"]{background:#080c14!important;border-right:1px solid #0f1825;}
section[data-testid="stSidebar"] *{color:#8a9bb0!important;}
section[data-testid="stSidebar"] h3{color:#f0f8ff!important;}
[data-testid="metric-container"]{background:#080c14;border:1px solid #0f1825;border-radius:10px;padding:14px!important;}
[data-testid="metric-container"] label{font-family:'Space Mono',monospace!important;font-size:8px!important;text-transform:uppercase;letter-spacing:1.5px;color:#2a3a4c!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;font-size:18px!important;color:#f0f8ff!important;}
.stButton>button{background:linear-gradient(135deg,#7c3aed,#4f46e5)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Syne',sans-serif!important;font-weight:800!important;text-transform:uppercase!important;letter-spacing:.8px!important;padding:10px 24px!important;}
.stButton>button:hover{background:linear-gradient(135deg,#9333ea,#6366f1)!important;box-shadow:0 4px 20px rgba(124,58,237,0.4)!important;}
.stTabs [data-baseweb="tab-list"]{background:#080c14;border-bottom:1px solid #0f1825;gap:4px;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#3a4a5c;font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;border:none;padding:10px 20px;}
.stTabs [aria-selected="true"]{background:#0f1825!important;color:#a78bfa!important;border-radius:6px 6px 0 0;}

.trader-card{background:#080c14;border:1px solid #0f1825;border-radius:12px;padding:18px 20px;margin-bottom:12px;}
.trader-card.gold{border-color:rgba(251,191,36,0.5);box-shadow:0 0 24px rgba(251,191,36,0.08);}
.trader-card.silver{border-color:rgba(156,163,175,0.4);}
.trader-card.bronze{border-color:rgba(180,120,60,0.4);}
.trader-card.top{border-color:rgba(124,58,237,0.4);}

.rank-badge{font-family:'Space Mono',monospace;font-size:20px;font-weight:700;min-width:42px;text-align:center;}
.rank-badge.r1{color:#fbbf24;}.rank-badge.r2{color:#9ca3af;}.rank-badge.r3{color:#b47c3c;}
.rank-badge.rtop{color:#a78bfa;}.rank-badge.rn{color:#2a3a4c;}

.trader-name{font-size:16px;font-weight:800;color:#f0f8ff;line-height:1.2;}
.trader-wallet{font-family:'Space Mono',monospace;font-size:9px;color:#3a4a5c;margin-top:2px;}
.verified{display:inline-block;background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);
  color:#60a5fa;border-radius:20px;padding:1px 7px;font-family:'Space Mono',monospace;
  font-size:8px;font-weight:700;margin-left:6px;vertical-align:middle;}

.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0;}
.stat-box{background:#0a0e18;border:1px solid #0f1825;border-radius:8px;padding:10px 12px;}
.stat-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;}
.stat-value{font-family:'Space Mono',monospace;font-size:15px;font-weight:700;}
.stat-value.green{color:#00e676;}.stat-value.red{color:#ff5252;}
.stat-value.purple{color:#a78bfa;}.stat-value.blue{color:#60a5fa;}

.pos-section{margin-top:12px;}
.pos-header{font-family:'Space Mono',monospace;font-size:8px;color:#2a3a4c;text-transform:uppercase;
  letter-spacing:1.5px;margin-bottom:8px;}
.pos-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px;}

.pos-card{background:#0a0e18;border:1px solid #0f1825;border-radius:8px;padding:10px 12px;}
.pos-card.yes{border-left:3px solid #00e676;}
.pos-card.no{border-left:3px solid #ff5252;}
.pos-title{font-size:11px;font-weight:600;color:#c8d8e8;line-height:1.4;margin-bottom:8px;}
.pos-stats{display:flex;gap:12px;flex-wrap:wrap;}
.pos-stat{display:flex;flex-direction:column;gap:1px;}
.pos-stat-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;}
.pos-stat-value{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;}
.pos-stat-value.yes{color:#00e676;}.pos-stat-value.no{color:#ff5252;}
.pos-stat-value.white{color:#f0f8ff;}.pos-stat-value.warn{color:#fb923c;}

.no-pos{font-family:'Space Mono',monospace;font-size:10px;color:#2a3a4c;
  padding:10px;background:#0a0e18;border-radius:6px;border:1px dashed #0f1825;}

.empty-state{background:#080c14;border:1px dashed #0f1825;border-radius:12px;padding:60px;text-align:center;}
.empty-icon{font-size:36px;opacity:.25;margin-bottom:12px;}
.empty-title{font-size:18px;font-weight:700;color:#f0f8ff;margin-bottom:8px;}
.empty-desc{font-family:'Space Mono',monospace;font-size:11px;color:#2a3a4c;line-height:2;}

.filter-bar{background:#080c14;border:1px solid #0f1825;border-radius:10px;padding:14px 18px;margin-bottom:20px;
  display:flex;gap:16px;align-items:center;flex-wrap:wrap;}
.filter-label{font-family:'Space Mono',monospace;font-size:9px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;}

.misprice-card{background:#080c14;border:1px solid #0f1825;border-radius:10px;padding:14px 16px;margin-bottom:10px;}
.misprice-card.extreme{border-color:rgba(255,82,82,0.4);box-shadow:0 0 12px rgba(255,82,82,0.06);}
.misprice-card.arb{border-color:rgba(251,146,60,0.35);}
.mp-q{font-size:13px;font-weight:600;color:#f0f8ff;line-height:1.4;margin-bottom:10px;}
.mp-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.mp-label{font-family:'Space Mono',monospace;font-size:7px;color:#2a3a4c;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px;}
.mp-value{font-family:'Space Mono',monospace;font-size:13px;font-weight:700;color:#f0f8ff;}
.mp-value.green{color:#00e676;}.mp-value.red{color:#ff5252;}.mp-value.orange{color:#fb923c;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  API
# ─────────────────────────────────────────────
DATA  = "https://data-api.polymarket.com"
GAMMA = "https://gamma-api.polymarket.com"
HDR   = {"Accept": "application/json", "User-Agent": "PolyCopy/3.0"}

def get(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HDR, params=params, timeout=15)
            if r.status_code == 429:
                time.sleep(4 * (i+1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if i < retries - 1: time.sleep(1.5)
    return None

def fmt_usdc(v):
    if v is None: return "—"
    v = float(v)
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.1f}K"
    return f"${v:.0f}"

def fmt_addr(a):
    if not a or len(a) < 10: return a or "???"
    return a[:6] + "…" + a[-4:]

def pnl_color(v):
    try:
        return "green" if float(v) >= 0 else "red"
    except: return "white"

# ─────────────────────────────────────────────
#  FETCH LEADERBOARD
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_leaderboard(category, time_period, order_by, total):
    """Fetch up to `total` traders by paginating (max 50 per request)."""
    results = []
    offset  = 0
    while len(results) < total:
        batch_size = min(50, total - len(results))
        data = get(f"{DATA}/v1/leaderboard", {
            "category":   category,
            "timePeriod": time_period,
            "orderBy":    order_by,
            "limit":      batch_size,
            "offset":     offset,
        })
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        results.extend(data)
        offset += len(data)
        if len(data) < batch_size:
            break
    return results

# ─────────────────────────────────────────────
#  FETCH OPEN POSITIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_open_positions(address):
    data = get(f"{DATA}/positions", {
        "user":           address,
        "sizeThreshold":  1,
        "limit":          50,
        "sortBy":         "CURRENT",
        "sortDirection":  "DESC",
    })
    if not data: return []
    positions = data if isinstance(data, list) else []
    # Filter out resolved/redeemable ones — we want active bets
    return [p for p in positions if not p.get("redeemable")]

# ─────────────────────────────────────────────
#  FETCH CLOSED POSITIONS (for win rate)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_win_rate(address):
    data = get(f"{DATA}/positions", {
        "user":          address,
        "redeemable":    "true",
        "limit":         500,
        "sortBy":        "CASHPNL",
        "sortDirection": "DESC",
    })
    if not data: return None, None, None
    positions = data if isinstance(data, list) else []
    if not positions: return None, None, None
    wins   = sum(1 for p in positions if float(p.get("cashPnl") or 0) > 0)
    losses = sum(1 for p in positions if float(p.get("cashPnl") or 0) <= 0)
    total  = wins + losses
    if total == 0: return None, None, None
    return round(wins/total*100, 1), wins, losses

# ─────────────────────────────────────────────
#  MISPRICING SCAN
# ─────────────────────────────────────────────
@st.cache_data(ttl=180)
def fetch_mispricings():
    data = get(f"{GAMMA}/markets", {
        "active": "true", "closed": "false",
        "limit": 300, "order": "volume", "ascending": "false"
    })
    if not data: return []
    markets = data if isinstance(data, list) else data.get("markets", [])
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
        total = yes_p + no_p
        dev   = abs(total - 1.0)
        if dev < 0.02: continue
        cid   = m.get("conditionId") or m.get("id") or ""
        results.append({
            "question":  (m.get("question") or m.get("title") or "")[:90],
            "yes_price": yes_p,
            "no_price":  no_p,
            "sum":       round(total, 4),
            "deviation": round(dev, 4),
            "volume":    float(m.get("volumeNum") or 0),
            "severity":  "extreme" if dev > 0.08 else "arb",
            "url":       f"https://polymarket.com/event/{cid}",
        })
    return sorted(results, key=lambda x: x["deviation"], reverse=True)[:40]

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ PolyCopy")
    st.markdown("---")

    st.markdown("**Leaderboard Filters**")
    time_period = st.selectbox("Time Period", ["MONTH", "WEEK", "ALL", "DAY"],
                               format_func=lambda x: {"MONTH":"Monthly","WEEK":"Weekly","ALL":"All Time","DAY":"Daily"}[x])
    category    = st.selectbox("Category",    ["OVERALL","POLITICS","SPORTS","CRYPTO","CULTURE","ECONOMICS","TECH","FINANCE"])
    order_by    = st.selectbox("Sort By",     ["PNL","VOL"],
                               format_func=lambda x: {"PNL":"Profit (PnL)","VOL":"Volume"}[x])
    num_traders = st.slider("Traders to fetch", 25, 200, 100, 25)

    st.markdown("---")
    st.markdown("**Display Filters**")
    min_pnl        = st.number_input("Min PnL ($)", value=0, step=1000)
    show_positions = st.toggle("Load open positions", value=True)
    show_win_rate  = st.toggle("Calculate win rate (slower)", value=False)

    st.markdown("---")
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:9px;color:#2a3a4c;line-height:2;'>
    ⚠ NOT FINANCIAL ADVICE<br>
    Educational use only.
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
  Leaderboard Tracker &nbsp;·&nbsp; Open Positions &nbsp;·&nbsp; Mispricing Scanner
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏆  Leaderboard & Positions", "🔍  Mispricing Scanner"])

# ══════════════════════════════════════════════
#  TAB 1 — LEADERBOARD
# ══════════════════════════════════════════════
with tab1:

    col_btn, col_info, _ = st.columns([1, 3, 4])
    with col_btn:
        load = st.button("⟳ Load Leaderboard", use_container_width=True)
    with col_info:
        st.markdown(f"""
        <div style='font-family:Space Mono,monospace;font-size:10px;color:#3a4a5c;padding-top:12px;'>
        {category} &nbsp;·&nbsp; {time_period} &nbsp;·&nbsp; by {order_by} &nbsp;·&nbsp; Top {num_traders} traders
        </div>""", unsafe_allow_html=True)

    if "leaderboard" not in st.session_state:
        st.session_state.leaderboard = []

    if load:
        with st.spinner(f"Fetching top {num_traders} traders from Polymarket leaderboard..."):
            st.session_state.leaderboard = fetch_leaderboard(category, time_period, order_by, num_traders)
        st.rerun()

    traders = st.session_state.leaderboard

    # Apply min PnL filter
    if min_pnl > 0:
        traders = [t for t in traders if float(t.get("pnl") or 0) >= min_pnl]

    if not traders:
        st.markdown("""
        <div class='empty-state'>
          <div class='empty-icon'>🏆</div>
          <div class='empty-title'>No leaderboard data loaded</div>
          <div class='empty-desc'>
            Click <b style='color:#a78bfa;'>Load Leaderboard</b> to fetch the top traders<br>
            directly from Polymarket's official leaderboard API.<br><br>
            You'll see their PnL, volume, and exactly what<br>
            markets they currently have open positions in.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary metrics
        total_pnl = sum(float(t.get("pnl") or 0) for t in traders)
        top_pnl   = max(float(t.get("pnl") or 0) for t in traders)
        verified  = sum(1 for t in traders if t.get("verifiedBadge"))

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Traders Loaded",  len(traders))
        with m2: st.metric("Top Trader PnL",  fmt_usdc(top_pnl))
        with m3: st.metric("Combined PnL",    fmt_usdc(total_pnl))
        with m4: st.metric("Verified Badges", verified)
        st.markdown("---")

        for trader in traders:
            rank    = int(trader.get("rank") or 0)
            wallet  = trader.get("proxyWallet") or ""
            name    = trader.get("userName") or fmt_addr(wallet)
            pnl     = float(trader.get("pnl") or 0)
            vol     = float(trader.get("vol") or 0)
            verified= trader.get("verifiedBadge", False)
            xhandle = trader.get("xUsername") or ""

            # Rank styling
            if   rank == 1: rank_cls = "r1"; card_cls = "gold"
            elif rank == 2: rank_cls = "r2"; card_cls = "silver"
            elif rank == 3: rank_cls = "r3"; card_cls = "bronze"
            elif rank <= 10: rank_cls = "rtop"; card_cls = "top"
            else:            rank_cls = "rn";   card_cls = ""

            rank_sym = {1:"🥇", 2:"🥈", 3:"🥉"}.get(rank, f"#{rank}")
            verified_html = "<span class='verified'>✓ VERIFIED</span>" if verified else ""
            x_html = f"<span style='font-family:Space Mono,monospace;font-size:9px;color:#3a4a5c;margin-left:8px;'>@{xhandle}</span>" if xhandle else ""

            # Win rate (optional, slower)
            wr_html = ""
            if show_win_rate and wallet:
                wr, wins, losses = fetch_win_rate(wallet)
                if wr is not None:
                    wr_html = f"""
                    <div class='stat-box'>
                      <div class='stat-label'>Win Rate</div>
                      <div class='stat-value {"green" if wr >= 55 else "red"}'>{wr}%</div>
                      <div style='font-family:Space Mono,monospace;font-size:8px;color:#3a4a5c;margin-top:2px;'>{wins}W / {losses}L</div>
                    </div>"""

            # Open positions
            pos_html = ""
            if show_positions and wallet:
                positions = fetch_open_positions(wallet)
                if positions:
                    cards = ""
                    for p in positions[:8]:
                        title     = (p.get("title") or "Unknown market")[:55]
                        outcome   = (p.get("outcome") or "?").upper()
                        cur_val   = float(p.get("currentValue") or 0)
                        init_val  = float(p.get("initialValue") or 0)
                        cash_pnl  = float(p.get("cashPnl") or 0)
                        pct_pnl   = float(p.get("percentPnl") or 0)
                        cur_price = float(p.get("curPrice") or 0)
                        side_cls  = "yes" if "YES" in outcome else "no"
                        pnl_cls   = "yes" if cash_pnl >= 0 else "no"
                        end_date  = (p.get("endDate") or "")[:10]

                        cards += f"""
                        <div class='pos-card {side_cls}'>
                          <div class='pos-title'>{title}</div>
                          <div class='pos-stats'>
                            <div class='pos-stat'>
                              <div class='pos-stat-label'>Side</div>
                              <div class='pos-stat-value {side_cls}'>{outcome}</div>
                            </div>
                            <div class='pos-stat'>
                              <div class='pos-stat-label'>Current Value</div>
                              <div class='pos-stat-value white'>{fmt_usdc(cur_val)}</div>
                            </div>
                            <div class='pos-stat'>
                              <div class='pos-stat-label'>P&L</div>
                              <div class='pos-stat-value {pnl_cls}'>{fmt_usdc(cash_pnl)} ({pct_pnl:+.0f}%)</div>
                            </div>
                            <div class='pos-stat'>
                              <div class='pos-stat-label'>Price</div>
                              <div class='pos-stat-value white'>{cur_price:.2f}¢</div>
                            </div>
                            {"<div class='pos-stat'><div class='pos-stat-label'>Closes</div><div class='pos-stat-value warn'>" + end_date + "</div></div>" if end_date else ""}
                          </div>
                        </div>"""

                    pos_html = f"""
                    <div class='pos-section'>
                      <div class='pos-header'>Current Open Positions ({len(positions)} found)</div>
                      <div class='pos-grid'>{cards}</div>
                    </div>"""
                else:
                    pos_html = "<div class='no-pos'>No open positions found (may be private or fully resolved)</div>"

            st.markdown(f"""
            <div class='trader-card {card_cls}'>
              <div style='display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;'>
                <div style='display:flex;align-items:center;gap:12px;'>
                  <div class='rank-badge {rank_cls}'>{rank_sym}</div>
                  <div>
                    <div class='trader-name'>
                      {name}{verified_html}{x_html}
                    </div>
                    <div class='trader-wallet'>{wallet}</div>
                  </div>
                </div>
                <a href='https://polymarket.com/profile/{wallet}' target='_blank'
                   style='font-family:Space Mono,monospace;font-size:9px;color:#a78bfa;text-decoration:none;
                          padding:4px 10px;border:1px solid rgba(124,58,237,0.3);border-radius:6px;'>
                  ↗ Profile
                </a>
              </div>

              <div class='stat-grid' style='grid-template-columns:{"repeat(3,1fr)" if not wr_html else "repeat(4,1fr)"};'>
                <div class='stat-box'>
                  <div class='stat-label'>PnL ({time_period.title()})</div>
                  <div class='stat-value {pnl_color(pnl)}'>{fmt_usdc(pnl)}</div>
                </div>
                <div class='stat-box'>
                  <div class='stat-label'>Volume</div>
                  <div class='stat-value purple'>{fmt_usdc(vol)}</div>
                </div>
                <div class='stat-box'>
                  <div class='stat-label'>Leaderboard Rank</div>
                  <div class='stat-value blue'>#{rank}</div>
                </div>
                {wr_html}
              </div>

              {pos_html}
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 2 — MISPRICING SCANNER
# ══════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style='font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:#f0f8ff;margin-bottom:4px;'>
      Mispricing Scanner
    </div>
    <div style='font-family:Space Mono,monospace;font-size:9px;color:#2a3a4c;text-transform:uppercase;
         letter-spacing:1.5px;margin-bottom:16px;'>
      Markets where YES + NO ≠ $1.00 — potential edge you can exploit
    </div>
    """, unsafe_allow_html=True)

    col_s, _ = st.columns([1, 5])
    with col_s:
        scan_mp = st.button("🔍 Scan Mispricings", key="mp_scan", use_container_width=True)

    if "mispricings" not in st.session_state:
        st.session_state.mispricings = []

    if scan_mp:
        with st.spinner("Scanning 300 active markets..."):
            st.session_state.mispricings = fetch_mispricings()
        st.rerun()

    mps = st.session_state.mispricings

    if not mps:
        st.markdown("""
        <div class='empty-state'>
          <div class='empty-icon'>🔍</div>
          <div class='empty-title'>No scan results yet</div>
          <div class='empty-desc'>
            Click <b style='color:#a78bfa;'>Scan Mispricings</b> to check 300 active markets.<br><br>
            <b>How it works:</b> On Polymarket, YES + NO should always sum to ~$1.00.<br>
            When they don't, one side is mispriced — that's your edge.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        extreme = [m for m in mps if m["severity"] == "extreme"]
        st.metric("Markets Scanned", "300")

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Mispricings Found",   len(mps))
        with c2: st.metric("Extreme (>8% off)",   len(extreme))
        with c3: st.metric("Largest Gap",         f"{round(mps[0]['deviation']*100,1)}%" if mps else "—")
        st.markdown("---")

        st.markdown("""
        <div style='background:#080c14;border:1px solid rgba(251,146,60,0.2);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-family:Space Mono,monospace;font-size:10px;color:#fb923c;line-height:1.8;'>
        💡 <b>Strategy:</b> If YES + NO &lt; $1.00 → buy BOTH sides → guaranteed profit at resolution regardless of outcome.<br>
        If YES + NO &gt; $1.00 → one side is overpriced → bet the cheaper/more likely side.
        </div>
        """, unsafe_allow_html=True)

        for mp in mps:
            total     = mp["sum"]
            dev_pct   = round(mp["deviation"] * 100, 2)
            arb_profit= round((1 - total) * 100, 2) if total < 1 else 0

            if total < 1:
                edge_txt = f"BUY BOTH → +{arb_profit:.1f}% guaranteed"
                edge_cls = "green"
            else:
                edge_txt = f"Overpriced by {dev_pct:.1f}%"
                edge_cls = "orange"

            st.markdown(f"""
            <div class='misprice-card {mp["severity"]}'>
              <div class='mp-q'>{mp["question"]}</div>
              <div class='mp-grid'>
                <div>
                  <div class='mp-label'>YES Price</div>
                  <div class='mp-value'>{mp["yes_price"]:.3f}</div>
                </div>
                <div>
                  <div class='mp-label'>NO Price</div>
                  <div class='mp-value'>{mp["no_price"]:.3f}</div>
                </div>
                <div>
                  <div class='mp-label'>Sum (target ~1.00)</div>
                  <div class='mp-value {"red" if total > 1 else "green"}'>{total:.4f}</div>
                </div>
                <div>
                  <div class='mp-label'>Edge</div>
                  <div class='mp-value {edge_cls}'>{edge_txt}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns([4, 1])
            with c2:
                st.markdown(
                    f'<a href="{mp["url"]}" target="_blank" '
                    f'style="font-family:Space Mono,monospace;font-size:9px;color:#a78bfa;text-decoration:none;">↗ Open Market</a>',
                    unsafe_allow_html=True
                )

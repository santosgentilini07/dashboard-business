"""
Meridian Logistics & Retail Co. — Finance & Operations Dashboard
24 months of realistic synthetic P&L, cash-flow, cost and variance data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Finance & Operations | Meridian Co.",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 20px;
}
[data-testid="stMetricLabel"]  { font-size: 0.74rem; color: #64748b; letter-spacing: .04em; text-transform: uppercase; }
[data-testid="stMetricValue"]  { font-size: 1.3rem;  font-weight: 700; }
[data-testid="stMetricDelta"]  { font-size: 0.78rem; }
.block-container               { padding-top: 1.5rem; padding-bottom: 2rem; }
h2                             { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Palette ────────────────────────────────────────────────────────────────────

C = dict(
    revenue    = "#2563EB",
    gp         = "#16A34A",
    ebitda     = "#7C3AED",
    net        = "#D97706",
    warehouse  = "#0891B2",
    fleet      = "#0369A1",
    labour     = "#6D28D9",
    marketing  = "#BE185D",
    technology = "#047857",
    admin      = "#92400E",
    pos        = "#16A34A",
    neg        = "#DC2626",
    neutral    = "#94A3B8",
    budget     = "#94A3B8",
)

OPEX_KEYS   = ["warehouse", "fleet", "labour", "marketing", "technology", "admin"]
OPEX_LABELS = ["Warehouse & Rent", "Fleet & Fuel", "Labour", "Marketing", "Technology", "Admin & G&A"]
OPEX_COLORS = [C[k] for k in OPEX_KEYS]

_FONT = dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b")
_HOVER = dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0")
_YAXIS = dict(showgrid=True, gridcolor="#f1f5f9", zeroline=True,
              zerolinecolor="#d1d5db", tickfont_size=11)
_XAXIS = dict(showgrid=False, zeroline=False, tickfont_size=11)
_LEGEND = dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
               font_size=11, bgcolor="rgba(0,0,0,0)")

def base_layout(**kw):
    return dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=_FONT, hoverlabel=_HOVER,
        margin=dict(l=8, r=8, t=36, b=8),
        legend=_LEGEND,
        **kw,
    )

# ── Formatting helpers ─────────────────────────────────────────────────────────

def gbp(v: float, d: int = 0) -> str:
    sign = "−" if v < 0 else ""
    a    = abs(v)
    if a >= 1_000_000: return f"{sign}£{a/1_000_000:.{d+1}f}M"
    if a >= 1_000:     return f"{sign}£{a/1_000:.{d}f}k"
    return f"{sign}£{a:,.0f}"

def pct(new: float, old: float) -> str:
    if old == 0: return "n/a"
    return f"{(new-old)/abs(old)*100:+.1f}%"

def var_color(actual, budget, is_cost=False):
    favorable = actual > budget if not is_cost else actual < budget
    return C["pos"] if favorable else C["neg"]

# ── Data generation ────────────────────────────────────────────────────────────

@st.cache_data
def generate_data() -> pd.DataFrame:
    rng    = np.random.default_rng(42)
    months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
    n      = len(months)

    SEASON = np.array([0.82, 0.80, 0.88, 0.92, 0.95, 0.94,
                       0.91, 0.93, 1.03, 1.18, 1.36, 1.43])
    s      = SEASON[[m.month - 1 for m in months]]
    growth = 1.0 + 0.08 * np.arange(n) / (n - 1)

    # ── Revenue ──────────────────────────────────────────────────────────────
    prod  = 195_000 * s * growth * rng.uniform(0.97, 1.03, n)
    deliv = prod * 0.158 * rng.uniform(0.96, 1.04, n)
    svc   = 28_000 * (1 + 0.05 * np.arange(n) / 12) * rng.uniform(0.98, 1.02, n)
    rev   = prod + deliv + svc

    # ── COGS ─────────────────────────────────────────────────────────────────
    cogs = prod * (0.548 - 0.004 * growth) + deliv * 0.69
    gp   = rev - cogs

    # ── Operating expenses ────────────────────────────────────────────────────
    yr24      = np.array([m.year == 2024 for m in months])
    warehouse = np.where(yr24, 22_300, 21_500) * rng.uniform(0.99, 1.01, n)

    fuel_cycle = 1.0 + 0.07 * np.sin(np.linspace(0, 3.5 * np.pi, n))
    fleet      = (np.where(yr24, 17_000, 15_900) + deliv * 0.115) \
                 * fuel_cycle * rng.uniform(0.96, 1.04, n)

    q4_lift  = np.array([1.17 if m.month in (11, 12) else 1.0 for m in months])
    labour   = np.where(yr24, 44_500, 42_000) * q4_lift * rng.uniform(0.99, 1.01, n)

    campaign = np.array([20_000 if m.month == 9  else
                         28_000 if m.month == 10 else
                         18_000 if m.month == 11 else 0 for m in months])
    marketing  = 7_500 * rng.uniform(0.85, 1.15, n) + campaign
    technology = 5_800 * (1 + 0.10 * np.arange(n) / 12) * rng.uniform(0.98, 1.02, n)
    admin      = 9_500 * (1 + 0.03 * np.arange(n) / 12) * rng.uniform(0.985, 1.015, n)
    opex       = warehouse + fleet + labour + marketing + technology + admin

    # ── P&L ──────────────────────────────────────────────────────────────────
    ebit    = gp - opex
    da      = np.full(n, 7_500.0)
    ebitda  = ebit + da
    interest= np.full(n, 2_800.0)
    ebt     = ebit - interest
    tax     = np.where(ebt > 0, ebt * 0.23, 0.0)
    net     = ebt - tax

    # ── Budget ────────────────────────────────────────────────────────────────
    mild_s  = (SEASON + 1.0) / 2.0
    mild_s /= mild_s.mean()
    brev23  = (rev[:12].mean() / 1.04) * mild_s[[m.month - 1 for m in months[:12]]]
    brev24  = (rev[:12].mean() * 1.06) * mild_s[[m.month - 1 for m in months[12:]]]
    brev    = np.concatenate([brev23, brev24])
    avg_gm  = (gp / rev).mean()
    avg_ox  = (opex / rev).mean()
    bgp     = brev * (avg_gm + 0.008)
    bebit   = bgp  - brev * (avg_ox - 0.005)

    # ── Cash flow ─────────────────────────────────────────────────────────────
    ar_chg  = np.diff(rev * 35 / 30, prepend=(rev * 35 / 30)[0])
    inv_chg = np.array([8_000 if m.month in (8, 9, 10) else
                        -7_000 if m.month in (1, 2)      else 0 for m in months])
    ap_chg  = -np.diff(cogs * 28 / 30, prepend=(cogs * 28 / 30)[0])
    op_cf   = net + da - ar_chg - inv_chg + ap_chg

    capex   = np.zeros(n)
    for idx, val in [(2, -35_000), (7, -22_000), (17, -58_000), (22, -18_000)]:
        capex[idx] = val
    fin_cf  = np.full(n, -8_500.0)
    fin_cf[0] += 80_000
    net_cf  = op_cf + capex + fin_cf
    cash    = 160_000 + np.cumsum(net_cf)

    return pd.DataFrame(dict(
        month            = months,
        year             = [m.year for m in months],
        lbl              = [m.strftime("%b %Y") for m in months],
        product_sales    = prod,
        delivery_fees    = deliv,
        service_contracts= svc,
        total_revenue    = rev,
        cogs             = cogs,
        gross_profit     = gp,
        gm_pct           = gp / rev * 100,
        warehouse        = warehouse,
        fleet            = fleet,
        labour           = labour,
        marketing        = marketing,
        technology       = technology,
        admin            = admin,
        total_opex       = opex,
        ebitda           = ebitda,
        ebit             = ebit,
        interest         = interest,
        tax              = tax,
        net_income       = net,
        nm_pct           = net / rev * 100,
        da               = da,
        budget_rev       = brev,
        budget_gp        = bgp,
        budget_ebit      = bebit,
        operating_cf     = op_cf,
        investing_cf     = capex,
        financing_cf     = fin_cf,
        net_cf           = net_cf,
        cash_balance     = cash,
    ))

# ── Load data ─────────────────────────────────────────────────────────────────

df = generate_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 Meridian Co.")
    st.caption("Finance & Operations")
    st.markdown("---")

    period = st.radio(
        "Period",
        options=["Full 24 months", "2023 only", "2024 only"],
        index=0,
    )
    year_map = {"Full 24 months": [2023, 2024], "2023 only": [2023], "2024 only": [2024]}
    years    = year_map[period]

    st.markdown("---")
    show_bgt = st.toggle("Show budget lines / targets", value=True)

    st.markdown("---")
    st.caption("Synthetic data · Fiscal Jan–Dec · Currency: GBP")

fd   = df[df["year"].isin(years)].copy()
comp = df[df["year"] == 2023] if period == "2024 only" else None

# ── Title ─────────────────────────────────────────────────────────────────────

st.title("Finance & Operations Dashboard")
st.caption("Meridian Logistics & Retail Co. · 2023–2024 · All figures in GBP")
st.divider()

# ── KPI cards ─────────────────────────────────────────────────────────────────

rev_s   = fd["total_revenue"].sum()
gp_s    = fd["gross_profit"].sum()
ebd_s   = fd["ebitda"].sum()
net_s   = fd["net_income"].sum()
cash_c  = fd["cash_balance"].iloc[-1]
brev_s  = fd["budget_rev"].sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Revenue",       gbp(rev_s),
          pct(rev_s, comp["total_revenue"].sum()) if comp is not None else None)
k2.metric("Gross Profit",  f"{gbp(gp_s)} · {gp_s/rev_s*100:.1f}%",
          pct(gp_s, comp["gross_profit"].sum()) if comp is not None else None)
k3.metric("EBITDA",        gbp(ebd_s),
          pct(ebd_s, comp["ebitda"].sum()) if comp is not None else None)
k4.metric("Net Income",    f"{gbp(net_s)} · {net_s/rev_s*100:.1f}%",
          pct(net_s, comp["net_income"].sum()) if comp is not None else None)
k5.metric("Cash on Hand",  gbp(cash_c))
k6.metric("vs Budget",     pct(rev_s, brev_s), delta_color="normal")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — P&L TREND
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("P&L Overview")

fig_pl = go.Figure()

for col, name, color, dash, width in [
    ("total_revenue", "Revenue",      C["revenue"], "solid", 2.5),
    ("gross_profit",  "Gross Profit", C["gp"],      "solid", 2.5),
    ("ebitda",        "EBITDA",       C["ebitda"],  "dash",  2.0),
    ("net_income",    "Net Income",   C["net"],     "solid", 2.0),
]:
    fig_pl.add_trace(go.Scatter(
        x=fd["month"], y=fd[col], name=name,
        mode="lines+markers",
        line=dict(color=color, width=width, dash=dash),
        marker=dict(size=4),
        hovertemplate=f"<b>{name}</b>  %{{x|%b %Y}}<br>%{{y:£,.0f}}<extra></extra>",
    ))

if show_bgt:
    fig_pl.add_trace(go.Scatter(
        x=fd["month"], y=fd["budget_rev"],
        name="Revenue Budget", mode="lines",
        line=dict(color=C["budget"], width=1.5, dash="dot"),
        opacity=0.7,
        hovertemplate="<b>Budget Rev</b>  %{x|%b %Y}<br>%{y:£,.0f}<extra></extra>",
    ))

fig_pl.add_hline(y=0, line_width=1, line_color="#d1d5db")
fig_pl.update_layout(
    **base_layout(height=320, hovermode="x unified"),
    yaxis=dict(**_YAXIS, tickprefix="£", tickformat=",.0f"),
    xaxis=dict(**_XAXIS, tickformat="%b %Y"),
    legend={**_LEGEND, "y": -0.22},
)
st.plotly_chart(fig_pl, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 + 3 — COST BREAKDOWN (stacked bar) + COST MIX (donut)
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Cost Breakdown by Category")
col_cost, col_donut = st.columns([3, 1], gap="large")

with col_cost:
    fig_cost = go.Figure()
    for key, label, color in zip(OPEX_KEYS, OPEX_LABELS, OPEX_COLORS):
        fig_cost.add_trace(go.Bar(
            x=fd["month"], y=fd[key], name=label,
            marker_color=color,
            hovertemplate=f"<b>{label}</b>  %{{x|%b %Y}}<br>%{{y:£,.0f}}<extra></extra>",
        ))
    if show_bgt:
        # Show total budget opex as a line reference
        bopex = fd["budget_rev"] * (fd["total_opex"] / fd["total_revenue"]).mean()
        fig_cost.add_trace(go.Scatter(
            x=fd["month"], y=bopex, name="Budget OpEx",
            mode="lines", line=dict(color="#1e293b", width=1.5, dash="dot"),
            opacity=0.6,
            hovertemplate="<b>Budget OpEx</b>  %{x|%b %Y}<br>%{y:£,.0f}<extra></extra>",
        ))

    fig_cost.update_layout(
        **base_layout(height=340, barmode="stack", hovermode="x unified"),
        yaxis=dict(**_YAXIS, tickprefix="£", tickformat=",.0f"),
        xaxis=dict(**_XAXIS, tickformat="%b %Y"),
        legend=dict(orientation="h", y=-0.28, x=0.5, xanchor="center",
                    font_size=10, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_cost, use_container_width=True)

with col_donut:
    totals = {lbl: fd[key].sum() for key, lbl in zip(OPEX_KEYS, OPEX_LABELS)}
    fig_dn = go.Figure(go.Pie(
        labels=list(totals.keys()),
        values=list(totals.values()),
        hole=0.54,
        marker_colors=OPEX_COLORS,
        textinfo="percent",
        textfont_size=11,
        direction="clockwise",
        sort=False,
        hovertemplate="<b>%{label}</b><br>%{value:£,.0f}  (%{percent})<extra></extra>",
    ))
    fig_dn.add_annotation(
        text=f"<b>{gbp(sum(totals.values()))}</b><br><span style='font-size:9px;color:#64748b'>Total OpEx</span>",
        x=0.5, y=0.5, showarrow=False, align="center",
        font=dict(size=12, color="#1e293b"),
    )
    fig_dn.update_layout(
        paper_bgcolor="white", margin=dict(l=4, r=4, t=28, b=60),
        height=340, showlegend=True,
        legend=dict(orientation="v", x=0.5, xanchor="center", y=-0.06,
                    font_size=9, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=_HOVER,
    )
    st.plotly_chart(fig_dn, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — CASH FLOW TREND (stacked bars + cash balance line)
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Cash Flow & Balance")

fig_cf = make_subplots(specs=[[{"secondary_y": True}]])

for col, name, color in [
    ("operating_cf",  "Operating CF",  C["gp"]),
    ("investing_cf",  "Investing CF",  C["neg"]),
    ("financing_cf",  "Financing CF",  C["ebitda"]),
]:
    fig_cf.add_trace(go.Bar(
        x=fd["month"], y=fd[col], name=name,
        marker_color=color, opacity=0.88,
        hovertemplate=f"<b>{name}</b>  %{{x|%b %Y}}<br>%{{y:£,.0f}}<extra></extra>",
    ), secondary_y=False)

fig_cf.add_trace(go.Scatter(
    x=fd["month"], y=fd["cash_balance"],
    name="Cash Balance",
    mode="lines+markers",
    line=dict(color=C["revenue"], width=2.5),
    marker=dict(size=5, symbol="circle"),
    hovertemplate="<b>Cash Balance</b>  %{x|%b %Y}<br>%{y:£,.0f}<extra></extra>",
), secondary_y=True)

# Mark CapEx events
capex_months = fd[fd["investing_cf"] < 0]
for _, row in capex_months.iterrows():
    fig_cf.add_annotation(
        x=row["month"], y=row["investing_cf"] * 1.05,
        text=f"CapEx<br>{gbp(abs(row['investing_cf']))}",
        showarrow=False, font=dict(size=8, color=C["neg"]),
        yref="y", align="center",
    )

fig_cf.update_layout(
    **base_layout(height=360, barmode="relative", hovermode="x unified"),
    legend={**_LEGEND, "y": -0.22},
)
fig_cf.update_yaxes(
    **_YAXIS, tickprefix="£", tickformat=",.0f", title_text="Cash Flow (£)",
    secondary_y=False,
)
fig_cf.update_yaxes(
    showgrid=False, tickprefix="£", tickformat=",.0f",
    title_text="Cash Balance (£)", tickfont_size=11,
    secondary_y=True,
)
fig_cf.update_xaxes(**_XAXIS, tickformat="%b %Y")
st.plotly_chart(fig_cf, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — P&L WATERFALL BRIDGE
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("P&L Bridge — Period Total")

t_rev = fd["total_revenue"].sum()
t_cogs = fd["cogs"].sum()
t_gp   = fd["gross_profit"].sum()
t_wh   = fd["warehouse"].sum()
t_fl   = fd["fleet"].sum()
t_la   = fd["labour"].sum()
t_mk   = fd["marketing"].sum()
t_te   = fd["technology"].sum()
t_ad   = fd["admin"].sum()
t_ebit = fd["ebit"].sum()
t_int  = fd["interest"].sum()
t_tax  = fd["tax"].sum()
t_net  = fd["net_income"].sum()

wf_x = ["Revenue", "COGS", "Gross Profit",
         "Warehouse", "Fleet & Fuel", "Labour",
         "Marketing", "Technology", "Admin",
         "EBIT", "Interest", "Tax", "Net Income"]
wf_m = ["absolute", "relative", "total",
        "relative", "relative", "relative",
        "relative", "relative", "relative",
        "total",    "relative", "relative", "total"]
wf_y = [t_rev,  -t_cogs, t_gp,
        -t_wh,   -t_fl,  -t_la,
        -t_mk,   -t_te,  -t_ad,
        t_ebit, -t_int, -t_tax, t_net]

wf_text = []
for m, v in zip(wf_m, wf_y):
    wf_text.append(gbp(abs(v)) if m != "total" else gbp(v))

fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=wf_m,
    x=wf_x,
    y=wf_y,
    text=wf_text,
    textposition="outside",
    textfont=dict(size=9, color="#1e293b"),
    connector=dict(line=dict(color="#cbd5e1", width=1, dash="dot")),
    decreasing=dict(marker=dict(color=C["neg"],  line=dict(color=C["neg"],  width=0.5))),
    increasing=dict(marker=dict(color=C["pos"],  line=dict(color=C["pos"],  width=0.5))),
    totals=dict(   marker=dict(color=C["revenue"],line=dict(color=C["revenue"],width=0.5))),
    hovertemplate="<b>%{x}</b><br>%{y:£,.0f}<extra></extra>",
))

fig_wf.update_layout(
    **base_layout(height=400),
    showlegend=False,
    yaxis=dict(**_YAXIS, tickprefix="£", tickformat=",.0f"),
    xaxis={**_XAXIS, "tickangle": -30, "tickfont": dict(size=10)},
    margin=dict(l=8, r=8, t=36, b=70),
)
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — MONTHLY VARIANCE: ACTUAL vs BUDGET
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Monthly Variance — Actual vs Budget")

tab_rev, tab_gp, tab_ebit = st.tabs(["Revenue", "Gross Profit", "EBIT"])

def variance_chart(actual_col: str, budget_col: str, label: str) -> go.Figure:
    act = fd[actual_col].values
    bgt = fd[budget_col].values
    var_abs = act - bgt
    var_pct = (act - bgt) / np.abs(bgt) * 100

    bar_colors = [C["pos"] if v >= 0 else C["neg"] for v in var_abs]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.62, 0.38],
        vertical_spacing=0.06,
    )

    # Row 1: actual vs budget grouped bars
    fig.add_trace(go.Bar(
        x=fd["month"], y=act, name=f"Actual {label}",
        marker_color=C["revenue"], opacity=0.9,
        hovertemplate=f"<b>Actual</b>  %{{x|%b %Y}}<br>%{{y:£,.0f}}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=fd["month"], y=bgt, name=f"Budget {label}",
        marker_color=C["budget"], opacity=0.7,
        hovertemplate=f"<b>Budget</b>  %{{x|%b %Y}}<br>%{{y:£,.0f}}<extra></extra>",
    ), row=1, col=1)

    # Row 2: variance bars (£)
    fig.add_trace(go.Bar(
        x=fd["month"], y=var_abs, name="Variance (£)",
        marker_color=bar_colors,
        text=[f"{v:+.0f}" for v in var_pct],
        textposition="outside",
        textfont=dict(size=8),
        hovertemplate="<b>Variance</b>  %{x|%b %Y}<br>£%{y:,.0f}  (%{text}%)<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=0, line_width=1, line_color="#d1d5db", row=2, col=1)

    fig.update_layout(
        **base_layout(height=400, barmode="group", hovermode="x unified"),
        legend={**_LEGEND, "y": -0.12},
    )
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", tickprefix="£",
                     tickformat=",.0f", tickfont_size=10, zeroline=True,
                     zerolinecolor="#d1d5db")
    fig.update_xaxes(showgrid=False, tickformat="%b %Y", tickfont_size=10, row=2, col=1)
    return fig

with tab_rev:
    st.plotly_chart(variance_chart("total_revenue", "budget_rev", "Revenue"),
                    use_container_width=True)

with tab_gp:
    st.plotly_chart(variance_chart("gross_profit", "budget_gp", "Gross Profit"),
                    use_container_width=True)

with tab_ebit:
    st.plotly_chart(variance_chart("ebit", "budget_ebit", "EBIT"),
                    use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — GROSS MARGIN % TREND
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Gross Margin % Trend")

fig_gm = go.Figure()

fig_gm.add_trace(go.Scatter(
    x=fd["month"], y=fd["gm_pct"],
    name="Gross Margin %",
    mode="lines+markers",
    line=dict(color=C["gp"], width=2.5),
    marker=dict(size=5),
    fill="tozeroy",
    fillcolor="rgba(22,163,74,0.07)",
    hovertemplate="<b>GM%</b>  %{x|%b %Y}<br>%{y:.1f}%<extra></extra>",
))

fig_gm.add_trace(go.Scatter(
    x=fd["month"], y=fd["nm_pct"],
    name="Net Margin %",
    mode="lines+markers",
    line=dict(color=C["net"], width=2.0, dash="dash"),
    marker=dict(size=4),
    hovertemplate="<b>Net Margin %</b>  %{x|%b %Y}<br>%{y:.1f}%<extra></extra>",
))

# Industry target band for GM%
if show_bgt:
    fig_gm.add_hrect(y0=47, y1=53, fillcolor="rgba(22,163,74,0.06)",
                     line_width=0, annotation_text="Target range 47–53%",
                     annotation_position="top right",
                     annotation_font=dict(size=10, color=C["gp"]))

fig_gm.add_hline(y=0, line_width=1, line_color="#d1d5db")
fig_gm.update_layout(
    **base_layout(height=260, hovermode="x unified"),
    yaxis=dict(**_YAXIS, ticksuffix="%", range=[-4, 58],
               tickfont_size=11),
    xaxis=dict(**_XAXIS, tickformat="%b %Y"),
    legend={**_LEGEND, "y": -0.28},
)
st.plotly_chart(fig_gm, use_container_width=True)

# ── Summary table ──────────────────────────────────────────────────────────────

with st.expander("Monthly P&L Summary Table"):
    tbl = fd[[
        "lbl", "total_revenue", "gross_profit", "gm_pct",
        "total_opex", "ebitda", "ebit", "net_income", "nm_pct", "cash_balance",
    ]].copy()
    tbl.columns = ["Month", "Revenue", "Gross Profit", "GM%",
                   "Total OpEx", "EBITDA", "EBIT", "Net Income", "NM%", "Cash Balance"]
    for col in ["Revenue", "Gross Profit", "Total OpEx", "EBITDA", "EBIT", "Net Income", "Cash Balance"]:
        tbl[col] = tbl[col].map(lambda v: gbp(v))
    tbl["GM%"] = tbl["GM%"].map(lambda v: f"{v:.1f}%")
    tbl["NM%"] = tbl["NM%"].map(lambda v: f"{v:.1f}%")
    st.dataframe(tbl, use_container_width=True, hide_index=True)

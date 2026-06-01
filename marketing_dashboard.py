"""
Meridian Co. — Marketing Dashboard
Synthetic Google Ads & Meta Ads data: 14 campaigns, Jan 2023 – Dec 2024.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Marketing Dashboard | Meridian Co.",
    page_icon="📈",
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
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Palette ────────────────────────────────────────────────────────────────────

CHAN_COLORS = {"Google Ads": "#4285F4", "Meta Ads": "#F25C05"}

TYPE_COLORS = {
    "Brand":       "#10B981",
    "Non-Brand":   "#6366F1",
    "Shopping":    "#F59E0B",
    "Remarketing": "#EF4444",
    "Retargeting": "#EC4899",
    "Prospecting": "#8B5CF6",
    "Awareness":   "#94A3B8",
}

_FONT   = dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b")
_HOVER  = dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0")
_GRID   = "#f1f5f9"

def chart_layout(**kw):
    defaults = dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=_FONT, hoverlabel=_HOVER,
        margin=dict(l=8, r=8, t=36, b=8),
    )
    return {**defaults, **kw}

# ── Helpers ────────────────────────────────────────────────────────────────────

def usd(v: float, d: int = 0) -> str:
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1_000_000: return f"{sign}${a/1_000_000:.{d+1}f}M"
    if a >= 1_000:     return f"{sign}${a/1_000:.{d}f}k"
    return f"{sign}${a:,.0f}"

def pct_delta(new, old):
    if old == 0: return None
    return f"{(new-old)/abs(old)*100:+.1f}%"

# ── Data generation ────────────────────────────────────────────────────────────

@st.cache_data
def generate_data() -> pd.DataFrame:
    rng    = np.random.default_rng(42)
    months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
    n      = len(months)

    SEASON = np.array([0.80, 0.78, 0.85, 0.90, 0.92, 0.88,
                       0.85, 0.88, 0.95, 1.10, 1.35, 1.45])

    # channel, name, type, base_spend, base_cpc, base_cvr, aov, base_ctr(%)
    CAMPAIGNS = [
        ("Google Ads", "Brand Keywords",        "Brand",       3200, 0.85, 0.080, 85,  13.0),
        ("Google Ads", "Non-Brand Keywords",    "Non-Brand",   8500, 0.78, 0.030, 78,   5.5),
        ("Google Ads", "Shopping – All Prods",  "Shopping",    6000, 0.58, 0.040, 72,   8.0),
        ("Google Ads", "Shopping – Top SKUs",   "Shopping",    3800, 0.71, 0.055, 90,   9.5),
        ("Google Ads", "Remarketing – Cart",    "Remarketing", 2200, 0.75, 0.110, 82,  10.5),
        ("Google Ads", "Display Remarketing",   "Remarketing", 1800, 0.45, 0.075, 78,   0.30),
        ("Google Ads", "YouTube Awareness",     "Awareness",   2500, 0.12, 0.011, 70,   0.12),
        ("Meta Ads",   "FB Prospecting – LAL",  "Prospecting", 5500, 0.85, 0.018, 68,   1.60),
        ("Meta Ads",   "FB Retargeting – Site", "Retargeting", 3200, 0.68, 0.045, 76,   2.50),
        ("Meta Ads",   "Instagram Stories",     "Prospecting", 3800, 0.55, 0.015, 65,   0.90),
        ("Meta Ads",   "FB Prospecting – Int.", "Prospecting", 4200, 0.72, 0.014, 62,   1.10),
        ("Meta Ads",   "Instagram Shopping",    "Shopping",    2800, 0.62, 0.032, 74,   2.10),
        ("Meta Ads",   "FB Brand Awareness",    "Awareness",   2000, 0.28, 0.005, 60,   0.55),
        ("Meta Ads",   "FB Retargeting – Eng.", "Retargeting", 2600, 0.73, 0.055, 80,   3.20),
    ]

    rows = []
    for ch, name, ctype, b_spend, b_cpc, b_cvr, aov, b_ctr in CAMPAIGNS:
        s      = SEASON[[m.month - 1 for m in months]]
        growth = 1.0 + 0.12 * np.arange(n) / (n - 1)

        spend   = b_spend * s * growth * rng.uniform(0.88, 1.12, n)
        cpc     = b_cpc   * rng.uniform(0.85, 1.15, n)
        clicks  = spend / cpc
        cvr     = b_cvr * (1 + 0.12 * (s - 1)) * rng.uniform(0.88, 1.12, n)
        convs   = clicks * cvr
        revenue = convs * aov * rng.uniform(0.92, 1.08, n)
        ctr     = b_ctr * rng.uniform(0.88, 1.12, n)
        impr    = clicks / (ctr / 100)

        for i, m in enumerate(months):
            rows.append(dict(
                month=m, channel=ch, campaign=name, campaign_type=ctype,
                spend=spend[i], impressions=impr[i], clicks=clicks[i],
                conversions=convs[i], revenue=revenue[i],
            ))

    df = pd.DataFrame(rows)
    df["year"]  = df["month"].dt.year
    df["roas"]  = df["revenue"] / df["spend"]
    df["cpa"]   = df["spend"]   / df["conversions"].clip(lower=0.01)
    df["ctr"]   = df["clicks"]  / df["impressions"] * 100
    df["cvr"]   = df["conversions"] / df["clicks"].clip(lower=1) * 100
    df["cpc"]   = df["spend"]   / df["clicks"].clip(lower=1)
    df["cpm"]   = df["spend"]   / df["impressions"] * 1000
    return df


df = generate_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📈 Meridian Co.")
    st.caption("Marketing Performance Dashboard")
    st.markdown("---")

    sel_channel = st.selectbox(
        "Channel",
        ["All Channels"] + sorted(df["channel"].unique()),
    )
    sel_type = st.selectbox(
        "Campaign Type",
        ["All Types"] + sorted(df["campaign_type"].unique()),
    )
    sel_year = st.radio("Year", ["All", "2023", "2024"], index=0)

    st.markdown("---")
    st.caption("Synthetic data · Google Ads & Meta Ads · Jan 2023 – Dec 2024")

# ── Apply filters ─────────────────────────────────────────────────────────────

filt = df.copy()
if sel_channel != "All Channels":
    filt = filt[filt["channel"] == sel_channel]
if sel_type != "All Types":
    filt = filt[filt["campaign_type"] == sel_type]
if sel_year != "All":
    filt = filt[filt["year"] == int(sel_year)]
comp = df[df["year"] == 2023] if sel_year == "2024" else None

if filt.empty:
    st.warning("No data for current filters.")
    st.stop()

# ── Header + KPIs ─────────────────────────────────────────────────────────────

st.title("Marketing Performance Dashboard")
st.caption("Meridian Co. · Google Ads & Meta Ads · 2023–2024")
st.divider()

tot_spend   = filt["spend"].sum()
tot_rev     = filt["revenue"].sum()
blended_roas= tot_rev / tot_spend
tot_convs   = filt["conversions"].sum()
avg_cpa     = tot_spend / tot_convs
tot_clicks  = filt["clicks"].sum()
blended_ctr = filt["clicks"].sum() / filt["impressions"].sum() * 100

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Total Spend",      usd(tot_spend),
          pct_delta(tot_spend, comp["spend"].sum()) if comp is not None else None)
k2.metric("Total Revenue",    usd(tot_rev),
          pct_delta(tot_rev, comp["revenue"].sum()) if comp is not None else None)
k3.metric("Blended ROAS",     f"{blended_roas:.2f}x",
          pct_delta(blended_roas, comp["revenue"].sum()/comp["spend"].sum()) if comp is not None else None)
k4.metric("Conversions",      f"{tot_convs:,.0f}",
          pct_delta(tot_convs, comp["conversions"].sum()) if comp is not None else None)
k5.metric("Avg CPA",          usd(avg_cpa, 2))
k6.metric("Blended CTR",      f"{blended_ctr:.2f}%")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — ROAS BY CHANNEL & CAMPAIGN TYPE (grouped bar)
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("ROAS by Channel & Campaign Type")
col1, col2 = st.columns([3, 2])

with col1:
    roas_df = (
        filt.groupby(["channel", "campaign_type"], as_index=False)
        .agg(spend=("spend","sum"), revenue=("revenue","sum"))
    )
    roas_df["roas"] = roas_df["revenue"] / roas_df["spend"]
    roas_df = roas_df.sort_values("roas", ascending=False)

    fig_roas = go.Figure()
    for ch, color in CHAN_COLORS.items():
        sub = roas_df[roas_df["channel"] == ch]
        if sub.empty:
            continue
        fig_roas.add_trace(go.Bar(
            x=sub["campaign_type"], y=sub["roas"],
            name=ch, marker_color=color,
            text=sub["roas"].map(lambda v: f"{v:.1f}x"),
            textposition="outside",
            textfont_size=10,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Channel: " + ch + "<br>"
                "ROAS: %{y:.2f}x<extra></extra>"
            ),
        ))

    fig_roas.add_hline(y=1, line_width=1, line_dash="dot", line_color="#94A3B8",
                       annotation_text="Break-even", annotation_font_size=10)
    fig_roas.update_layout(
        **chart_layout(height=340, barmode="group", hovermode="x unified",
                       legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
                                   font_size=11, bgcolor="rgba(0,0,0,0)")),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=True,
                   zerolinecolor="#d1d5db", ticksuffix="x", tickfont_size=11),
        xaxis=dict(showgrid=False, tickfont_size=11),
    )
    st.plotly_chart(fig_roas, use_container_width=True)

with col2:
    st.subheader("ROAS Trend by Channel")
    roas_trend = (
        filt.groupby(["month","channel"], as_index=False)
        .agg(spend=("spend","sum"), revenue=("revenue","sum"))
    )
    roas_trend["roas"] = roas_trend["revenue"] / roas_trend["spend"]

    fig_rt = go.Figure()
    for ch, color in CHAN_COLORS.items():
        sub = roas_trend[roas_trend["channel"] == ch]
        if sub.empty:
            continue
        fig_rt.add_trace(go.Scatter(
            x=sub["month"], y=sub["roas"],
            name=ch, mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{ch}</b>  %{{x|%b %Y}}<br>ROAS: %{{y:.2f}}x<extra></extra>",
        ))

    fig_rt.add_hline(y=1, line_width=1, line_dash="dot", line_color="#94A3B8")
    fig_rt.update_layout(
        **chart_layout(height=340, hovermode="x unified",
                       legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center",
                                   font_size=11, bgcolor="rgba(0,0,0,0)")),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=False,
                   ticksuffix="x", tickfont_size=11),
        xaxis=dict(showgrid=False, tickformat="%b %Y", tickfont_size=11),
    )
    st.plotly_chart(fig_rt, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — SPEND vs CONVERSIONS TREND (full width, dual axis)
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Spend vs Conversions Trend")

monthly = (
    filt.groupby(["month","channel"], as_index=False)
    .agg(spend=("spend","sum"), conversions=("conversions","sum"), revenue=("revenue","sum"))
)

fig_svc = make_subplots(specs=[[{"secondary_y": True}]])

for ch, color in CHAN_COLORS.items():
    sub = monthly[monthly["channel"] == ch]
    if sub.empty:
        continue
    fig_svc.add_trace(go.Bar(
        x=sub["month"], y=sub["spend"],
        name=f"{ch} Spend",
        marker_color=color, opacity=0.85,
        hovertemplate=f"<b>{ch} Spend</b>  %{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>",
    ), secondary_y=False)

# Total conversions line
total_monthly = filt.groupby("month", as_index=False).agg(
    conversions=("conversions","sum"), revenue=("revenue","sum"))
fig_svc.add_trace(go.Scatter(
    x=total_monthly["month"], y=total_monthly["conversions"],
    name="Conversions", mode="lines+markers",
    line=dict(color="#10B981", width=2.5),
    marker=dict(size=5, symbol="circle"),
    hovertemplate="<b>Conversions</b>  %{x|%b %Y}<br>%{y:,.0f}<extra></extra>",
), secondary_y=True)

fig_svc.update_layout(
    **chart_layout(height=340, barmode="stack", hovermode="x unified",
                   legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                               font_size=11, bgcolor="rgba(0,0,0,0)")),
)
fig_svc.update_yaxes(showgrid=True, gridcolor=_GRID, tickprefix="$",
                     tickformat=",.0f", secondary_y=False)
fig_svc.update_yaxes(showgrid=False, tickformat=",d",
                     title_text="Conversions", tickfont_size=11, secondary_y=True)
fig_svc.update_xaxes(showgrid=False, tickformat="%b %Y", tickfont_size=11)
st.plotly_chart(fig_svc, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — SPEND DISTRIBUTION (stacked bar) + CHART 4 — SPEND MIX (donut)
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Spend by Campaign Type")
col3, col4 = st.columns([3, 1], gap="large")

with col3:
    spend_type = (
        filt.groupby(["month","campaign_type"], as_index=False)["spend"].sum()
    )
    fig_st = go.Figure()
    for ctype, color in TYPE_COLORS.items():
        sub = spend_type[spend_type["campaign_type"] == ctype]
        if sub.empty:
            continue
        fig_st.add_trace(go.Bar(
            x=sub["month"], y=sub["spend"],
            name=ctype, marker_color=color,
            hovertemplate=f"<b>{ctype}</b>  %{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>",
        ))
    fig_st.update_layout(
        **chart_layout(height=320, barmode="stack", hovermode="x unified",
                       legend=dict(orientation="h", y=-0.24, x=0.5, xanchor="center",
                                   font_size=10, bgcolor="rgba(0,0,0,0)")),
        yaxis=dict(showgrid=True, gridcolor=_GRID, tickprefix="$",
                   tickformat=",.0f", tickfont_size=11),
        xaxis=dict(showgrid=False, tickformat="%b %Y", tickfont_size=11),
    )
    st.plotly_chart(fig_st, use_container_width=True)

with col4:
    spend_mix = filt.groupby("campaign_type", as_index=False)["spend"].sum()
    fig_dn = go.Figure(go.Pie(
        labels=spend_mix["campaign_type"],
        values=spend_mix["spend"],
        hole=0.52,
        marker_colors=[TYPE_COLORS.get(t, "#94A3B8") for t in spend_mix["campaign_type"]],
        textinfo="percent",
        textfont_size=11,
        sort=False,
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}  (%{percent})<extra></extra>",
    ))
    fig_dn.add_annotation(
        text=f"<b>{usd(tot_spend)}</b><br><span style='font-size:9px;color:#64748b'>Total Spend</span>",
        x=0.5, y=0.5, showarrow=False, align="center",
        font=dict(size=12, color="#1e293b"),
    )
    fig_dn.update_layout(
        paper_bgcolor="white", margin=dict(l=4, r=4, t=28, b=50),
        height=320, showlegend=False,
        hoverlabel=_HOVER,
    )
    st.plotly_chart(fig_dn, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — CTR vs CVR BUBBLE  +  CHART 6 — CONVERSION FUNNEL
# ══════════════════════════════════════════════════════════════════════════════

col5, col6 = st.columns(2)

with col5:
    st.subheader("Campaign Efficiency: CTR vs CVR")
    bubble = (
        filt.groupby(["campaign","channel","campaign_type"], as_index=False)
        .agg(spend=("spend","sum"), ctr=("ctr","mean"),
             cvr=("cvr","mean"), roas=("roas","mean"))
    )
    # Normalize bubble sizes
    s_min, s_max = bubble["spend"].min(), bubble["spend"].max()
    bubble["size"] = 8 + 40 * (bubble["spend"] - s_min) / (s_max - s_min + 1)

    fig_bbl = go.Figure()
    for ch, color in CHAN_COLORS.items():
        sub = bubble[bubble["channel"] == ch]
        if sub.empty:
            continue
        fig_bbl.add_trace(go.Scatter(
            x=sub["ctr"], y=sub["cvr"],
            name=ch, mode="markers",
            marker=dict(
                size=sub["size"], color=color, opacity=0.75,
                line=dict(color="white", width=1),
            ),
            text=sub["campaign"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "CTR: %{x:.2f}%<br>"
                "CVR: %{y:.2f}%<br>"
                "Spend: $%{customdata[0]:,.0f}<br>"
                "ROAS: %{customdata[1]:.2f}x"
                "<extra></extra>"
            ),
            customdata=sub[["spend","roas"]].values,
        ))

    fig_bbl.update_layout(
        **chart_layout(height=360, hovermode="closest",
                       legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                                   font_size=11, bgcolor="rgba(0,0,0,0)")),
        xaxis=dict(title="CTR (%)", showgrid=True, gridcolor=_GRID,
                   zeroline=False, tickfont_size=11),
        yaxis=dict(title="CVR (%)", showgrid=True, gridcolor=_GRID,
                   zeroline=False, tickfont_size=11),
    )
    st.caption("Bubble size = total spend")
    st.plotly_chart(fig_bbl, use_container_width=True)

with col6:
    st.subheader("Conversion Funnel by Channel")
    funnel = (
        filt.groupby("channel", as_index=False)
        .agg(impressions=("impressions","sum"),
             clicks=("clicks","sum"),
             conversions=("conversions","sum"))
    )

    fig_fn = make_subplots(
        rows=1, cols=2,
        subplot_titles=list(funnel["channel"]) if len(funnel) > 1 else list(funnel["channel"]),
        horizontal_spacing=0.08,
    )

    for idx, (_, row) in enumerate(funnel.iterrows(), start=1):
        if idx > 2:
            break
        ch    = row["channel"]
        color = CHAN_COLORS.get(ch, "#94A3B8")
        vals  = [row["impressions"], row["clicks"], row["conversions"]]
        pcts  = [100, row["clicks"]/row["impressions"]*100,
                 row["conversions"]/row["impressions"]*100]
        labels = ["Impressions", "Clicks", "Conversions"]
        text   = [
            f"{row['impressions']:,.0f}<br>({pcts[0]:.0f}%)",
            f"{row['clicks']:,.0f}<br>({pcts[1]:.2f}%)",
            f"{row['conversions']:,.0f}<br>({pcts[2]:.3f}%)",
        ]
        for j, (lbl, val, txt) in enumerate(zip(labels, vals, text)):
            fig_fn.add_trace(go.Bar(
                x=[lbl], y=[val],
                marker_color=color,
                opacity=1.0 - j * 0.25,
                text=[txt], textposition="inside",
                textfont=dict(size=9, color="white"),
                showlegend=False,
                hovertemplate=f"<b>{lbl}</b><br>{val:,.0f}<extra></extra>",
            ), row=1, col=idx)

    fig_fn.update_layout(
        **chart_layout(height=360,
                       legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                                   font_size=11, bgcolor="rgba(0,0,0,0)")),
    )
    fig_fn.update_yaxes(showgrid=True, gridcolor=_GRID, tickformat=",d",
                        tickfont_size=10)
    fig_fn.update_xaxes(showgrid=False, tickfont_size=11)
    st.plotly_chart(fig_fn, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE — TOP PERFORMING CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Top-Performing Campaigns")

tbl = (
    filt.groupby(["campaign","channel","campaign_type"], as_index=False)
    .agg(
        spend       = ("spend",       "sum"),
        revenue     = ("revenue",     "sum"),
        conversions = ("conversions", "sum"),
        clicks      = ("clicks",      "sum"),
        impressions = ("impressions", "sum"),
    )
)
tbl["roas"] = tbl["revenue"]  / tbl["spend"]
tbl["cpa"]  = tbl["spend"]    / tbl["conversions"].clip(lower=0.01)
tbl["ctr"]  = tbl["clicks"]   / tbl["impressions"] * 100
tbl["cvr"]  = tbl["conversions"] / tbl["clicks"].clip(lower=1) * 100
tbl = tbl.sort_values("roas", ascending=False).reset_index(drop=True)
tbl.index += 1

display = tbl[["campaign","channel","campaign_type",
               "spend","revenue","conversions","roas","cpa","ctr","cvr"]].copy()
display.columns = ["Campaign","Channel","Type",
                   "Spend","Revenue","Conversions","ROAS","CPA","CTR (%)","CVR (%)"]

display["Spend"]       = display["Spend"].map(lambda v: usd(v))
display["Revenue"]     = display["Revenue"].map(lambda v: usd(v))
display["Conversions"] = display["Conversions"].map(lambda v: f"{v:,.0f}")
display["ROAS"]        = display["ROAS"].map(lambda v: f"{v:.2f}x")
display["CPA"]         = display["CPA"].map(lambda v: usd(v, 2))
display["CTR (%)"]     = display["CTR (%)"].map(lambda v: f"{v:.2f}%")
display["CVR (%)"]     = display["CVR (%)"].map(lambda v: f"{v:.2f}%")

st.dataframe(
    display,
    use_container_width=True,
    column_config={
        "Campaign": st.column_config.TextColumn("Campaign", width="large"),
        "Channel":  st.column_config.TextColumn("Channel"),
        "Type":     st.column_config.TextColumn("Type"),
        "ROAS":     st.column_config.TextColumn("ROAS"),
    },
)

import os
import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="UK E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide",
)

# ── CSS tweaks ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="stMetric"] { background:#f8f9fb; border-radius:10px; padding:12px 18px; }
    [data-testid="stMetricLabel"] { font-size:0.8rem; color:#666; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def load_data() -> pd.DataFrame:
    base = os.path.dirname(__file__) or "."
    gz = os.path.join(base, "ecommerce_uk.csv.gz")
    csv = os.path.join(base, "ecommerce_uk.csv")
    if os.path.exists(gz):
        path, kw = gz, {"compression": "gzip"}
    elif os.path.exists(csv):
        path, kw = csv, {}
    else:
        raise FileNotFoundError("Dataset file not found. Expected ecommerce_uk.csv.gz alongside the app.")

    df = pd.read_csv(path, encoding="latin1", **kw)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Remove cancellations, returns, and free items
    df = df[
        (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
        & (~df["InvoiceNo"].astype(str).str.startswith("C"))
    ].copy()

    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    df["YearMonth"] = df["InvoiceDate"].dt.strftime("%Y-%m")
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    df["Hour"] = df["InvoiceDate"].dt.hour
    df["Country"] = df["Country"].str.strip()
    return df


df = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 UK E-Commerce")
    st.markdown("---")

    all_countries = sorted(df["Country"].unique())
    top_countries = (
        df.groupby("Country")["Revenue"].sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )
    selected_countries = st.multiselect(
        "Country",
        options=all_countries,
        default=top_countries[:5],
    )

    date_min = df["InvoiceDate"].dt.date.min()
    date_max = df["InvoiceDate"].dt.date.max()
    date_range = st.date_input(
        "Date range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    min_revenue = st.slider(
        "Min order revenue (£)",
        min_value=0,
        max_value=500,
        value=0,
        step=10,
    )

    st.markdown("---")
    st.caption("Data: UCI Online Retail (UK, Dec 2010 – Dec 2011)")

# ── Apply filters ─────────────────────────────────────────────────────────────
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_min, date_max

filt = df.copy()
if selected_countries:
    filt = filt[filt["Country"].isin(selected_countries)]
filt = filt[
    (filt["InvoiceDate"].dt.date >= start_date)
    & (filt["InvoiceDate"].dt.date <= end_date)
]

# Per-invoice revenue for the min-order filter
invoice_rev = filt.groupby("InvoiceNo")["Revenue"].sum()
valid_invoices = invoice_rev[invoice_rev >= min_revenue].index
filt = filt[filt["InvoiceNo"].isin(valid_invoices)]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("UK E-Commerce Analytics Dashboard")
st.caption(
    f"Filtered: **{len(selected_countries or all_countries)} countries** · "
    f"**{start_date}** to **{end_date}**"
)

if filt.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ── KPI cards ─────────────────────────────────────────────────────────────────
total_rev = filt["Revenue"].sum()
total_orders = filt["InvoiceNo"].nunique()
total_customers = filt["CustomerID"].nunique()
aov = filt.groupby("InvoiceNo")["Revenue"].sum().mean()
total_items = filt["Quantity"].sum()
unique_products = filt["StockCode"].nunique()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Revenue", f"£{total_rev:,.0f}")
c2.metric("Orders", f"{total_orders:,}")
c3.metric("Customers", f"{total_customers:,}")
c4.metric("Avg Order Value", f"£{aov:,.2f}")
c5.metric("Items Sold", f"{total_items:,}")
c6.metric("Unique Products", f"{unique_products:,}")

st.markdown("---")

# ── Row 1: Revenue over time  +  Revenue by country ──────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Revenue Over Time")
    monthly = (
        filt.groupby("Month", as_index=False)["Revenue"]
        .sum()
        .rename(columns={"Revenue": "revenue"})
    )
    line = (
        alt.Chart(monthly)
        .mark_area(
            line={"color": "#4F8EF7", "strokeWidth": 2},
            color="#4F8EF7",
            opacity=0.15,
        )
        .encode(
            x=alt.X("Month:T", title="Month", axis=alt.Axis(format="%b %Y")),
            y=alt.Y("revenue:Q", title="Revenue (£)", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("Month:T", title="Month", format="%B %Y"),
                alt.Tooltip("revenue:Q", title="Revenue (£)", format=",.2f"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(line, use_container_width=True)

with col_right:
    st.subheader("Revenue by Country")
    by_country = (
        filt.groupby("Country", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=True)   # ascending → largest at top in Altair
        .tail(10)
    )
    bar_country = (
        alt.Chart(by_country)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("Country:N", sort=None, title=None),
            x=alt.X("Revenue:Q", title="Revenue (£)", axis=alt.Axis(format=",.0f")),
            color=alt.Color(
                "Revenue:Q",
                scale=alt.Scale(scheme="blues"),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("Revenue:Q", title="Revenue (£)", format=",.2f"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(bar_country, use_container_width=True)

# ── Row 2: Top products  +  Orders by day + hour heatmap ─────────────────────
col_left2, col_right2 = st.columns([2, 3])

with col_left2:
    st.subheader("Top 15 Products by Revenue")
    top_products = (
        filt.groupby("Description", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=True)   # ascending → largest at top in Altair
        .tail(15)
    )
    top_products["short"] = top_products["Description"].str.slice(0, 30)
    bar_prod = (
        alt.Chart(top_products)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#F4845F")
        .encode(
            y=alt.Y("short:N", sort=None, title=None),
            x=alt.X("Revenue:Q", title="Revenue (£)", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("Description:N", title="Product"),
                alt.Tooltip("Revenue:Q", title="Revenue (£)", format=",.2f"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(bar_prod, use_container_width=True)

with col_right2:
    st.subheader("Order Volume Heatmap (Day × Hour)")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_data = (
        filt.groupby(["DayOfWeek", "Hour"])["InvoiceNo"]
        .nunique()
        .reset_index()
        .rename(columns={"InvoiceNo": "orders"})
    )
    heatmap = (
        alt.Chart(heatmap_data)
        .mark_rect()
        .encode(
            x=alt.X("Hour:O", title="Hour of Day"),
            y=alt.Y("DayOfWeek:N", sort=day_order, title=None),
            color=alt.Color(
                "orders:Q",
                scale=alt.Scale(scheme="greenblue"),
                title="Orders",
            ),
            tooltip=[
                alt.Tooltip("DayOfWeek:N", title="Day"),
                alt.Tooltip("Hour:O", title="Hour"),
                alt.Tooltip("orders:Q", title="Orders"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(heatmap, use_container_width=True)

# ── Row 3: Customer spend distribution  +  Monthly quantity vs revenue ────────
col_left3, col_right3 = st.columns(2)

with col_left3:
    st.subheader("Customer Spend Distribution")
    cust_spend = (
        filt.groupby("CustomerID")["Revenue"]
        .sum()
        .reset_index()
        .rename(columns={"Revenue": "total_spend"})
    )
    cust_spend["bucket"] = pd.cut(
        cust_spend["total_spend"],
        bins=[0, 100, 250, 500, 1000, 2500, 5000, float("inf")],
        labels=["<£100", "£100–250", "£250–500", "£500–1k", "£1k–2.5k", "£2.5k–5k", "£5k+"],
    )
    bucket_counts = (
        cust_spend["bucket"]
        .value_counts()
        .reset_index()
        .rename(columns={"count": "customers"})
        .sort_values("bucket")
    )
    bar_cust = (
        alt.Chart(bucket_counts)
        .mark_bar(color="#7B61FF", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("bucket:N", title="Spend Bracket", sort=None),
            y=alt.Y("customers:Q", title="Customers"),
            tooltip=[
                alt.Tooltip("bucket:N", title="Bracket"),
                alt.Tooltip("customers:Q"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(bar_cust, use_container_width=True)

with col_right3:
    st.subheader("Monthly Quantity vs Revenue")
    monthly_qr = (
        filt.groupby("Month")
        .agg(revenue=("Revenue", "sum"), quantity=("Quantity", "sum"))
        .reset_index()
    )
    fig_qr = make_subplots(specs=[[{"secondary_y": True}]])
    fig_qr.add_trace(go.Scatter(
        x=monthly_qr["Month"], y=monthly_qr["revenue"],
        name="Revenue (£)", mode="lines+markers",
        line=dict(color="#4F8EF7", width=2),
        marker=dict(size=4),
        hovertemplate="%{x|%b %Y}<br>Revenue: £%{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig_qr.add_trace(go.Scatter(
        x=monthly_qr["Month"], y=monthly_qr["quantity"],
        name="Quantity", mode="lines+markers",
        line=dict(color="#F4845F", width=2, dash="dash"),
        marker=dict(size=4),
        hovertemplate="%{x|%b %Y}<br>Qty: %{y:,.0f}<extra></extra>",
    ), secondary_y=True)
    fig_qr.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        height=280, margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.25,
                    font_size=11, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
        font=dict(family="sans-serif", size=11),
    )
    fig_qr.update_yaxes(tickprefix="£", tickformat=",.0f", showgrid=True,
                        gridcolor="#f1f5f9", secondary_y=False)
    fig_qr.update_yaxes(tickformat=",d", showgrid=False, secondary_y=True)
    fig_qr.update_xaxes(showgrid=False)
    st.plotly_chart(fig_qr, use_container_width=True)

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("View raw data sample (500 rows)"):
    st.dataframe(
        filt[["InvoiceNo", "InvoiceDate", "StockCode", "Description",
              "Quantity", "UnitPrice", "Revenue", "CustomerID", "Country"]]
        .head(500),
        use_container_width=True,
    )

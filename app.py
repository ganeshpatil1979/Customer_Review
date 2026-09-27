
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Customer & Loan Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    [data-testid="stMetricValue"] { font-size: 1.65rem; }
    .small-note { color: #6b7280; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading customer features…")
def load_summary():
    df = pd.read_csv(DATA_DIR / "customer_summary.csv")
    for c in ["first_transaction", "last_transaction"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

@st.cache_data(show_spinner="Loading transaction ledger…")
def load_transactions():
    cols = [
        "transaction_id", "customer_id", "date", "amount",
        "direction", "channel", "narration_raw", "true_category"
    ]
    df = pd.read_csv(DATA_DIR / "transaction_ledger.csv", usecols=cols)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

@st.cache_data(show_spinner="Loading behavioral log…")
def load_behavior():
    cols = [
        "event_id", "customer_id", "timestamp", "event_type",
        "product_viewed", "session_duration_seconds"
    ]
    df = pd.read_csv(DATA_DIR / "behavioral_log.csv", usecols=cols)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

@st.cache_data(show_spinner="Loading customer master…")
def load_customer_master():
    return pd.read_csv(DATA_DIR / "customer_master.csv")

@st.cache_data(show_spinner="Loading labels…")
def load_labels():
    return pd.read_csv(DATA_DIR / "labels.csv")

df = load_summary()

st.title("📊 Customer & Loan Conversion Analytics")
st.caption("Interactive analysis of customer profile, financial activity, digital behavior, applications and conversions.")

# Sidebar filters
st.sidebar.header("Filters")

def multi_filter(label, column):
    options = sorted(df[column].dropna().astype(str).unique().tolist())
    return st.sidebar.multiselect(label, options, default=options)

city_filter = multi_filter("City tier", "city_tier")
occupation_filter = multi_filter("Occupation", "occupation_type")
residence_filter = multi_filter("Residence", "residence_type")
loan_filter = multi_filter("Loan type", "loan_type")

age_min, age_max = int(df.age.min()), int(df.age.max())
age_range = st.sidebar.slider("Age", age_min, age_max, (age_min, age_max))
bureau_min, bureau_max = int(df.bureau_score_proxy.min()), int(df.bureau_score_proxy.max())
bureau_range = st.sidebar.slider("Bureau score proxy", bureau_min, bureau_max, (bureau_min, bureau_max))

applied_only = st.sidebar.checkbox("Applications only", False)
converted_only = st.sidebar.checkbox("Converted customers only", False)

filtered = df[
    df.city_tier.astype(str).isin(city_filter)
    & df.occupation_type.astype(str).isin(occupation_filter)
    & df.residence_type.astype(str).isin(residence_filter)
    & df.loan_type.astype(str).isin(loan_filter)
    & df.age.between(age_range[0], age_range[1])
    & df.bureau_score_proxy.between(bureau_range[0], bureau_range[1])
].copy()

if applied_only:
    filtered = filtered[filtered.applied_flag.eq(1)]
if converted_only:
    filtered = filtered[filtered.converted_flag.eq(1)]

st.sidebar.markdown("---")
st.sidebar.metric("Customers in view", f"{len(filtered):,}")

view = st.sidebar.radio(
    "Dashboard view",
    ["Overview", "Customer Explorer", "Digital Behavior", "Financial Activity", "Data Dictionary"],
)

# ---------- Overview ----------
if view == "Overview":
    st.subheader("Overview")

    customers = len(filtered)
    applicants = int(filtered.applied_flag.sum())
    converters = int(filtered.converted_flag.sum())
    conversion = converters / applicants * 100 if applicants else 0
    avg_application = filtered.loc[filtered.applied_flag.eq(1), "application_amount"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Customers", f"{customers:,}")
    c2.metric("Applications", f"{applicants:,}")
    c3.metric("Conversions", f"{converters:,}")
    c4.metric("Conversion rate", f"{conversion:.1f}%")
    c5.metric("Avg application", f"₹{avg_application:,.0f}" if pd.notna(avg_application) else "—")

    st.markdown("### Application funnel")
    funnel = pd.DataFrame({
        "Stage": ["Customer base", "Applied", "Converted"],
        "Customers": [customers, applicants, converters],
    })
    fig = px.funnel(funnel, x="Customers", y="Stage", title="Customer → Application → Conversion")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Conversion by loan type")
        loan = filtered[filtered.applied_flag.eq(1)].groupby("loan_type").agg(
            Applicants=("customer_id", "size"),
            Conversions=("converted_flag", "sum"),
        ).reset_index()
        loan["Conversion rate"] = np.where(
            loan["Applicants"] > 0, loan["Conversions"] / loan["Applicants"] * 100, 0
        )
        fig = px.bar(
            loan, x="loan_type", y="Conversion rate",
            text=loan["Conversion rate"].map(lambda x: f"{x:.1f}%"),
            labels={"loan_type": "Loan type", "Conversion rate": "Conversion rate (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Conversion by city tier")
        city = filtered.groupby("city_tier").agg(
            Customers=("customer_id", "size"),
            Applicants=("applied_flag", "sum"),
            Conversions=("converted_flag", "sum"),
        ).reset_index()
        city["Conversion rate"] = np.where(
            city["Applicants"] > 0, city["Conversions"] / city["Applicants"] * 100, 0
        )
        fig = px.bar(
            city, x="city_tier", y="Conversion rate",
            text=city["Conversion rate"].map(lambda x: f"{x:.1f}%"),
            labels={"city_tier": "City tier", "Conversion rate": "Conversion rate (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Applicant profile")
    profile = filtered[filtered.applied_flag.eq(1)]
    if len(profile):
        p1, p2, p3 = st.columns(3)
        p1.metric("Median age", f"{profile.age.median():.0f}")
        p2.metric("Median bureau score proxy", f"{profile.bureau_score_proxy.median():.0f}")
        p3.metric("Median declared income", f"₹{profile.declared_annual_income.median():,.0f}")
    else:
        st.info("No applicants match the selected filters.")

# ---------- Customer Explorer ----------
elif view == "Customer Explorer":
    st.subheader("Customer Explorer")
    st.caption("Search and inspect customer-level profile, application, transaction and engagement features.")

    search = st.text_input("Search customer ID", placeholder="e.g. CUST000123").strip().upper()
    table = filtered.copy()

    if search:
        table = table[table.customer_id.str.contains(search, na=False)]

    display_cols = [
        "customer_id", "age", "occupation_type", "city_tier",
        "declared_annual_income", "bureau_score_proxy", "existing_loan_count",
        "applied_flag", "converted_flag", "loan_type", "application_amount",
        "txn_count", "total_credit", "total_debit", "cash_flow",
        "event_count", "calculator_uses", "product_views"
    ]
    st.dataframe(
        table[display_cols].sort_values("customer_id"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "declared_annual_income": st.column_config.NumberColumn("Income", format="₹%.0f"),
            "application_amount": st.column_config.NumberColumn("Application", format="₹%.0f"),
            "total_credit": st.column_config.NumberColumn("Credits", format="₹%.0f"),
            "total_debit": st.column_config.NumberColumn("Debits", format="₹%.0f"),
            "cash_flow": st.column_config.NumberColumn("Net cash flow", format="₹%.0f"),
        },
    )

    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered customer data",
        csv,
        "filtered_customer_data.csv",
        "text/csv",
    )

    if search and len(table) == 1:
        r = table.iloc[0]
        st.markdown("### Customer detail")
        a, b, c, d = st.columns(4)
        a.metric("Application", "Yes" if r.applied_flag else "No")
        b.metric("Converted", "Yes" if r.converted_flag else "No")
        c.metric("Loan type", str(r.loan_type))
        d.metric("Application amount", f"₹{r.application_amount:,.0f}")

# ---------- Digital Behavior ----------
elif view == "Digital Behavior":
    st.subheader("Digital Behavior")
    st.caption("Digital engagement signals summarized at customer level.")

    applicants = filtered[filtered.applied_flag.eq(1)].copy()
    if applicants.empty:
        st.info("No applicants match the selected filters.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg events / applicant", f"{applicants.event_count.mean():.1f}")
        c2.metric("Avg calculator uses", f"{applicants.calculator_uses.mean():.1f}")
        c3.metric("Avg product views", f"{applicants.product_views.mean():.1f}")
        c4.metric("Avg session", f"{applicants.avg_session_seconds.mean():.0f}s")

        # Engagement bands
        applicants["engagement_band"] = pd.cut(
            applicants["event_count"],
            bins=[-1, 20, 50, 100, np.inf],
            labels=["0–20", "21–50", "51–100", "100+"],
        )
        band = applicants.groupby("engagement_band", observed=False).agg(
            Applicants=("customer_id", "size"),
            Conversions=("converted_flag", "sum"),
        ).reset_index()
        band["Conversion rate"] = band["Conversions"] / band["Applicants"] * 100

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                band, x="engagement_band", y="Applicants",
                labels={"engagement_band": "Engagement events", "Applicants": "Applicants"},
                title="Applicants by engagement band",
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(
                band, x="engagement_band", y="Conversion rate",
                text=band["Conversion rate"].map(lambda x: f"{x:.1f}%"),
                labels={"engagement_band": "Engagement events", "Conversion rate": "Conversion rate (%)"},
                title="Conversion rate by engagement band",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Calculator use relationship
        calc = applicants.groupby(applicants.calculator_user).agg(
            Applicants=("customer_id", "size"),
            Conversions=("converted_flag", "sum"),
        ).reset_index()
        calc["Group"] = calc.calculator_user.map({0: "No calculator use", 1: "Used calculator"})
        calc["Conversion rate"] = calc["Conversions"] / calc["Applicants"] * 100
        fig = px.bar(
            calc, x="Group", y="Conversion rate",
            text=calc["Conversion rate"].map(lambda x: f"{x:.1f}%"),
            title="Observed conversion rate by calculator usage",
            labels={"Group": "", "Conversion rate": "Conversion rate (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("These are observational group comparisons; they do not establish that calculator use causes conversion.")

# ---------- Financial Activity ----------
elif view == "Financial Activity":
    st.subheader("Financial Activity")
    st.caption("Transaction patterns from the ledger. The detailed ledger is loaded only for this view.")

    tx = load_transactions()
    tx_view = tx[tx.customer_id.isin(filtered.customer_id)].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{len(tx_view):,}")
    c2.metric("Credit value", f"₹{tx_view.loc[tx_view.amount > 0, 'amount'].sum():,.0f}")
    c3.metric("Debit value", f"₹{abs(tx_view.loc[tx_view.amount < 0, 'amount'].sum()):,.0f}")
    c4.metric("Bounce transactions", f"{(tx_view.true_category == 'bounce').sum():,}")

    col1, col2 = st.columns(2)
    with col1:
        cat = tx_view.groupby("true_category").agg(
            Transactions=("transaction_id", "size"),
            Value=("amount", lambda s: s.abs().sum()),
        ).reset_index().sort_values("Transactions", ascending=False)
        fig = px.bar(
            cat, x="true_category", y="Transactions",
            title="Transaction mix by category",
            labels={"true_category": "Category"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        channel = tx_view.groupby("channel").agg(
            Transactions=("transaction_id", "size"),
            Value=("amount", lambda s: s.abs().sum()),
        ).reset_index()
        fig = px.pie(channel, names="channel", values="Transactions", title="Transactions by channel")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Monthly transaction volume")
    monthly = tx_view.assign(month=tx_view.date.dt.to_period("M").astype(str)).groupby(
        "month", as_index=False
    ).agg(Transactions=("transaction_id", "size"), Value=("amount", lambda s: s.abs().sum()))
    fig = px.line(monthly, x="month", y="Transactions", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Transaction search")
    q = st.text_input("Narration contains", placeholder="e.g. SWIGGY, RENT, SAL").strip()
    detail = tx_view
    if q:
        detail = detail[detail.narration_raw.str.contains(q, case=False, na=False)]

    st.dataframe(
        detail.sort_values("date", ascending=False).head(500),
        use_container_width=True,
        hide_index=True,
        column_config={
            "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
            "date": st.column_config.DatetimeColumn("Date"),
        },
    )
    st.caption("Showing up to 500 matching transactions in the table for responsiveness.")

# ---------- Data Dictionary ----------
else:
    st.subheader("Data Dictionary & Project Notes")
    dictionary = pd.DataFrame([
        ["customer_summary.csv", "Precomputed customer-level feature table used by most dashboard views.", "5,000 rows × 38 columns"],
        ["transaction_ledger.csv", "Transaction-level ledger with amount, channel, narration and category.", "1,033,406 rows × 8 columns"],
        ["behavioral_log.csv", "Digital event/session activity by customer.", "489,663 rows × 6 columns"],
        ["customer_master.csv", "Customer demographics, income, tenure and bureau proxy.", "5,000 rows × 11 columns"],
        ["labels.csv", "Application and conversion outcome labels.", "5,000 rows × 5 columns"],
    ], columns=["File", "Purpose", "Size"])
    st.table(dictionary)

    st.markdown("### Key definitions")
    st.markdown("""
    - **Application rate** = applicants ÷ customers in the selected population.
    - **Conversion rate** = converted customers ÷ applicants.
    - **Cash flow** = total credits − total debits.
    - **Calculator user** = customer with at least one `loan_calculator_used` event.
    - **Product viewer** = customer with at least one `product_page_view` event.
    - **Bureau score proxy** is treated as a supplied feature, not as an independently verified bureau score.
    - The dashboard describes observed data; it does not claim causal relationships.
    """)

    st.markdown("### Source data coverage")
    st.write(
        f"Transactions: {df.first_transaction.min():%Y-%m-%d} to {df.last_transaction.max():%Y-%m-%d}. "
        "Behavioral timestamps and label dates are retained in their source files."
    )

st.markdown("---")
st.caption("Built with Streamlit • Pandas • Plotly • Designed for GitHub + Streamlit Community Cloud")

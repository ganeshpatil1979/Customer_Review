
from pathlib import Path
import pandas as pd
import numpy as np

DATA = Path(__file__).parent / "data"

tx = pd.read_csv(DATA / "transaction_ledger.csv", parse_dates=["date"])
bh = pd.read_csv(DATA / "behavioral_log.csv", parse_dates=["timestamp"])
cm = pd.read_csv(DATA / "customer_master.csv")
lb = pd.read_csv(DATA / "labels.csv")

txg = tx.groupby("customer_id").agg(
    txn_count=("transaction_id", "count"),
    total_credit=("amount", lambda s: s[s > 0].sum()),
    total_debit=("amount", lambda s: -s[s < 0].sum()),
    avg_transaction=("amount", lambda s: s.abs().mean()),
    bounce_count=("true_category", lambda s: (s == "bounce").sum()),
    salary_credits=("true_category", lambda s: (s == "salary").sum()),
    emi_count=("true_category", lambda s: (s == "emi").sum()),
    discretionary_count=("true_category", lambda s: (s == "discretionary").sum()),
    business_income_count=("true_category", lambda s: (s == "business_income").sum()),
    first_transaction=("date", "min"),
    last_transaction=("date", "max"),
).reset_index()

bhg = bh.groupby("customer_id").agg(
    event_count=("event_id", "count"),
    app_logins=("event_type", lambda s: (s == "app_login").sum()),
    calculator_uses=("event_type", lambda s: (s == "loan_calculator_used").sum()),
    product_views=("event_type", lambda s: (s == "product_page_view").sum()),
    sms_clicks=("event_type", lambda s: (s == "sms_click").sum()),
    customer_care_chats=("event_type", lambda s: (s == "customer_care_chat").sum()),
    avg_session_seconds=("session_duration_seconds", "mean"),
    total_session_seconds=("session_duration_seconds", "sum"),
).reset_index()

summary = cm.merge(lb, on="customer_id").merge(txg, on="customer_id", how="left").merge(
    bhg, on="customer_id", how="left"
)
summary[summary.select_dtypes(include=np.number).columns] = summary.select_dtypes(
    include=np.number
).fillna(0)
summary["cash_flow"] = summary["total_credit"] - summary["total_debit"]
summary["calculator_user"] = (summary["calculator_uses"] > 0).astype(int)
summary["product_viewer"] = (summary["product_views"] > 0).astype(int)
summary["engagement_events"] = summary["event_count"]

summary.to_csv(DATA / "customer_summary.csv", index=False)
print(f"Wrote {len(summary):,} customer rows.")

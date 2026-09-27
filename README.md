# Customer & Loan Conversion Analytics — Streamlit

An interactive Streamlit dashboard built from the supplied customer, transaction, behavioral and conversion-label datasets.

## What is included

- `app.py` — complete Streamlit application
- `data/customer_summary.csv` — precomputed 5,000-customer feature table for fast startup
- `data/transaction_ledger.csv` — original transaction ledger
- `data/behavioral_log.csv` — original behavioral event log
- `data/customer_master.csv` — original customer master
- `data/labels.csv` — original application/conversion labels
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — Streamlit configuration
- `.gitignore` — Git ignore rules

## Dashboard sections

1. **Overview**
   - Customer/application/conversion KPIs
   - Funnel
   - Conversion by loan type and city tier
   - Applicant profile

2. **Customer Explorer**
   - Customer ID search
   - Profile + financial + engagement features
   - Filtered CSV download

3. **Digital Behavior**
   - Engagement bands
   - Calculator usage
   - Observed conversion comparisons
   - Session metrics

4. **Financial Activity**
   - Transaction mix
   - Channels
   - Monthly transaction volume
   - Narration search
   - Recent matching transaction table

5. **Data Dictionary**
   - Dataset descriptions
   - Metric definitions
   - Coverage notes

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

### 1. Create a GitHub repository

Create a new repository and put these files/folders at its root:

```text
app.py
requirements.txt
README.md
.streamlit/config.toml
data/
  customer_summary.csv
  transaction_ledger.csv
  behavioral_log.csv
  customer_master.csv
  labels.csv
```

### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial Streamlit analytics dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

### 3. Streamlit Cloud

Open Streamlit Community Cloud, connect the GitHub repository, select:

- **Main file path:** `app.py`
- **Python version:** use a current supported Python version

Deploy.

## Important GitHub note about the raw transaction CSV

`transaction_ledger.csv` is approximately 97 MB. GitHub's recommended repository file size is much lower, and GitHub enforces a 100 MB hard limit for ordinary Git objects.

If GitHub rejects the transaction file, use **Git LFS** for the large CSV:

```bash
git lfs install
git lfs track "data/transaction_ledger.csv"
git add .gitattributes data/transaction_ledger.csv
git commit -m "Track transaction ledger with Git LFS"
git push
```

If your Streamlit deployment environment does not retrieve LFS objects as expected, store the raw transaction file in a suitable external data store and change `load_transactions()` in `app.py` to read that source. The precomputed `customer_summary.csv` is intentionally small so the main dashboard can still start quickly.

## Data assumptions

All four supplied source files share `customer_id`, allowing them to be joined. The app does not train a predictive model; it provides descriptive and exploratory analytics.

The dashboard uses the supplied `bureau_score_proxy` as a feature and does not represent it as a verified credit-bureau score.

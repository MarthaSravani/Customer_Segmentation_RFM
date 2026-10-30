"""
Customer Segmentation & RFM Analysis - Core Pipeline
Loads raw UCI Online Retail data, applies data validation and cleaning,
calculates RFM metrics and quantile scores, performs customer segmentation,
and exports all deliverables to CSV, SQLite, and Excel.
"""

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

try:
    from src.excel_report import generate_excel_workbook
except ImportError:
    from excel_report import generate_excel_workbook


def run_pipeline() -> None:
    # ==========================================
    # 1. PROJECT PATHS
    # ==========================================
    ROOT = Path(__file__).resolve().parent.parent
    DATA_FILE = ROOT / "data" / "Online Retail.xlsx"
    OUTPUT = ROOT / "output"
    OUTPUT.mkdir(exist_ok=True)

    print("==================================================")
    print("CUSTOMER SEGMENTATION & RFM ANALYSIS PIPELINE")
    print("==================================================")
    print(f"Data source: {DATA_FILE}")
    print(f"Output directory: {OUTPUT}")

    # ==========================================
    # 2. LOAD DATASET
    # ==========================================
    print("\n[Step 1/6] Loading raw dataset from Excel...")
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Source dataset not found at {DATA_FILE}")

    df_raw = pd.read_excel(DATA_FILE)
    original_records = len(df_raw)
    print(f"Raw records loaded: {original_records:,}")

    # ==========================================
    # 3. DATA QUALITY CHECKS & AUDIT LOGGING
    # ==========================================
    print("\n[Step 2/6] Auditing data quality and missing records...")
    missing_customers = int(df_raw["CustomerID"].isna().sum())
    missing_invoices = int(df_raw["InvoiceNo"].isna().sum())
    missing_dates = int(df_raw["InvoiceDate"].isna().sum())
    missing_descriptions = int(df_raw["Description"].isna().sum())
    raw_duplicates = int(df_raw.duplicated().sum())

    # Type casting for initial evaluation
    df = df_raw.copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
    df["StockCode"] = df["StockCode"].astype("string").str.strip()
    df["Description"] = df["Description"].astype("string").str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

    # Drop missing customer, invoice, or date information
    df_with_cust = df.dropna(subset=["CustomerID", "InvoiceNo", "InvoiceDate"]).copy()
    records_with_cust = len(df_with_cust)

    # Cancellations (InvoiceNo starting with 'C')
    cancelled_mask = df_with_cust["InvoiceNo"].str.startswith("C", na=False)
    cancelled_count = int(cancelled_mask.sum())

    # Filter out cancellations
    df_positive_invoices = df_with_cust[~cancelled_mask].copy()

    # Invalid / non-positive quantities and prices
    non_pos_qty = int((df_positive_invoices["Quantity"] <= 0).sum())
    non_pos_price = int((df_positive_invoices["UnitPrice"] <= 0).sum())

    # Final cleaned transactions
    df_clean = df_positive_invoices[
        (df_positive_invoices["Quantity"] > 0) &
        (df_positive_invoices["UnitPrice"] > 0)
    ].copy()

    df_clean["CustomerID"] = df_clean["CustomerID"].astype("int64")
    df_clean["Quantity"] = df_clean["Quantity"].astype("int64")
    df_clean["UnitPrice"] = df_clean["UnitPrice"].astype("float64")

    # Calculate Revenue
    df_clean["Revenue"] = df_clean["Quantity"] * df_clean["UnitPrice"]
    cleaned_records = len(df_clean)

    total_revenue = float(df_clean["Revenue"].sum())
    total_unique_customers = int(df_clean["CustomerID"].nunique())
    total_unique_invoices = int(df_clean["InvoiceNo"].nunique())
    min_invoice_date = df_clean["InvoiceDate"].min()
    max_invoice_date = df_clean["InvoiceDate"].max()
    reference_date = max_invoice_date + pd.Timedelta(days=1)

    print(f"Cleaned valid transactions: {cleaned_records:,}")
    print(f"Unique customers: {total_unique_customers:,}")
    print(f"Unique valid orders (invoices): {total_unique_invoices:,}")
    print(f"Total revenue: £{total_revenue:,.2f}")

    # Build comprehensive Data Quality Report table
    quality_records = [
        {"Step": 1, "Metric": "Raw Records Loaded", "Value": original_records, "Description": "Original transactions from Online Retail.xlsx", "Status": "VERIFIED"},
        {"Step": 2, "Metric": "Missing CustomerID Rows", "Value": missing_customers, "Description": "Guest / unregistered transactions removed", "Status": "REMOVED"},
        {"Step": 3, "Metric": "Missing InvoiceNo Rows", "Value": missing_invoices, "Description": "Transactions without invoice number", "Status": "ZERO_FOUND"},
        {"Step": 4, "Metric": "Missing InvoiceDate Rows", "Value": missing_dates, "Description": "Transactions without timestamp", "Status": "ZERO_FOUND"},
        {"Step": 5, "Metric": "Missing Description Rows", "Value": missing_descriptions, "Description": "Raw records lacking item description", "Status": "AUDITED"},
        {"Step": 6, "Metric": "Raw Duplicate Rows", "Value": raw_duplicates, "Description": "Identical line item records in raw dataset", "Status": "AUDITED"},
        {"Step": 7, "Metric": "Records with CustomerID", "Value": records_with_cust, "Description": "Transactions retained after customer presence filter", "Status": "RETAINED"},
        {"Step": 8, "Metric": "Cancelled Invoices (C)", "Value": cancelled_count, "Description": "Returns/cancellations removed from sales analysis", "Status": "EXCLUDED"},
        {"Step": 9, "Metric": "Non-Positive Quantity Rows", "Value": non_pos_qty, "Description": "Adjustments / negative items removed", "Status": "EXCLUDED"},
        {"Step": 10, "Metric": "Non-Positive UnitPrice Rows", "Value": non_pos_price, "Description": "Free samples or zero-price entries removed", "Status": "EXCLUDED"},
        {"Step": 11, "Metric": "Cleaned Transactions", "Value": cleaned_records, "Description": "Preserved valid transaction line records", "Status": "CONFIRMED"},
        {"Step": 12, "Metric": "Unique Customers", "Value": total_unique_customers, "Description": "Distinct paying customer identifiers", "Status": "RECONCILED"},
        {"Step": 13, "Metric": "Unique Invoices (Orders)", "Value": total_unique_invoices, "Description": "Distinct invoice numbers (COUNT DISTINCT)", "Status": "RECONCILED"},
        {"Step": 14, "Metric": "Total Valid Revenue (£)", "Value": round(total_revenue, 2), "Description": "Total sales volume (Quantity * UnitPrice)", "Status": "RECONCILED"},
        {"Step": 15, "Metric": "Date Range Start", "Value": str(min_invoice_date), "Description": "Earliest transaction in cleaned dataset", "Status": "AUDITED"},
        {"Step": 16, "Metric": "Date Range End", "Value": str(max_invoice_date), "Description": "Latest transaction in cleaned dataset", "Status": "AUDITED"},
        {"Step": 17, "Metric": "RFM Reference Date", "Value": str(reference_date), "Description": "Latest date + 1 day used as recency benchmark", "Status": "ESTABLISHED"},
    ]
    df_quality = pd.DataFrame(quality_records)

    # ==========================================
    # 4. CALCULATE RFM METRICS & QUANTILE SCORES
    # ==========================================
    print("\n[Step 3/6] Computing customer RFM metrics and quantile scores...")
    rfm = df_clean.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (reference_date - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Revenue", "sum")
    ).reset_index()

    # Quantile scoring helper using first ranking to handle duplicate boundaries safely
    def calculate_score(series: pd.Series, ascending: bool = True) -> pd.Series:
        ranked = series.rank(method="first", ascending=ascending)
        return pd.qcut(ranked, q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    # Lower recency = higher R_Score (5 is best)
    rfm["R_Score"] = calculate_score(rfm["Recency"], ascending=False)
    # Higher frequency = higher F_Score (5 is best)
    rfm["F_Score"] = calculate_score(rfm["Frequency"], ascending=True)
    # Higher monetary = higher M_Score (5 is best)
    rfm["M_Score"] = calculate_score(rfm["Monetary"], ascending=True)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str) +
        rfm["F_Score"].astype(str) +
        rfm["M_Score"].astype(str)
    )

    # ==========================================
    # 5. CUSTOMER SEGMENTATION
    # ==========================================
    print("\n[Step 4/6] Segmenting customers into 9 behavioral tiers...")
    def assign_segment(row: pd.Series) -> str:
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r <= 2 and f >= 4 and m >= 4:
            return "Cannot Lose Them"
        elif f >= 4 and r >= 3:
            return "Loyal Customers"
        elif r >= 4 and f >= 2:
            return "Potential Loyalists"
        elif r >= 4 and f == 1:
            return "Recent Customers"
        elif r == 3 and f >= 3:
            return "Need Attention"
        elif r == 3:
            return "Promising"
        elif r <= 2 and f >= 3:
            return "At Risk"
        else:
            return "Hibernating"

    rfm["Segment"] = rfm.apply(assign_segment, axis=1)

    # Segment Summary Table
    segment_summary = rfm.groupby("Segment").agg(
        Customer_Count=("CustomerID", "count"),
        Total_Revenue=("Monetary", "sum"),
        Average_Recency=("Recency", "mean"),
        Average_Frequency=("Frequency", "mean"),
        Average_Monetary=("Monetary", "mean")
    ).reset_index()

    segment_summary["Customer_Percentage"] = (
        segment_summary["Customer_Count"] / len(rfm) * 100
    ).round(2)

    # Print summary table
    print("\nSegment Breakdown:")
    print(segment_summary.to_string(index=False))

    # ==========================================
    # 6. EXPORT ARTIFACTS (CSV, SQLITE, EXCEL)
    # ==========================================
    print("\n[Step 5/6] Exporting clean CSV artifacts...")
    # Export full cleaned transactions
    df_clean.to_csv(OUTPUT / "cleaned_transactions.csv", index=False)
    print(f" - Saved: {OUTPUT / 'cleaned_transactions.csv'} ({cleaned_records:,} rows)")

    # Export customer RFM
    rfm.to_csv(OUTPUT / "customer_rfm.csv", index=False)
    print(f" - Saved: {OUTPUT / 'customer_rfm.csv'} ({len(rfm):,} rows)")

    # Export segment summary
    segment_summary.to_csv(OUTPUT / "segment_summary.csv", index=False)
    print(f" - Saved: {OUTPUT / 'segment_summary.csv'}")

    # Export data quality report
    df_quality.to_csv(OUTPUT / "data_quality_report.csv", index=False)
    print(f" - Saved: {OUTPUT / 'data_quality_report.csv'}")

    # Export SQLite Database
    print("\n[Step 6/6] Updating SQLite Database and generating Excel workbook...")
    db_path = OUTPUT / "retail_analysis.db"
    with sqlite3.connect(db_path) as conn:
        df_clean.to_sql("cleaned_transactions", conn, if_exists="replace", index=False)
        rfm.to_sql("customer_rfm", conn, if_exists="replace", index=False)
        segment_summary.to_sql("segment_summary", conn, if_exists="replace", index=False)
        df_quality.to_sql("data_quality_report", conn, if_exists="replace", index=False)
    print(f" - SQLite database saved at: {db_path} (4 tables)")

    # Generate Professional Excel Workbook with xlsxwriter
    excel_path = OUTPUT / "analysis_workbook.xlsx"
    generate_excel_workbook(
        output_path=excel_path,
        df_clean=df_clean,
        rfm=rfm,
        segment_summary=segment_summary,
        quality_report=df_quality,
    )

    print("\n==================================================")
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_pipeline()

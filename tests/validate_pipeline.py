"""
Automated Pipeline Validation & Verification Test Suite
Tests data cleaning, RFM scoring, segmentation counts, SQLite database tables,
SQL queries, Excel workbook sheets, and cross-reconciles Python against SQL.
"""

from pathlib import Path
import sqlite3
import sys

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
DB_PATH = OUTPUT / "retail_analysis.db"
EXCEL_PATH = OUTPUT / "analysis_workbook.xlsx"

# Reference ground-truth targets
EXPECTED_RAW_COUNT = 541909
EXPECTED_CLEANED_COUNT = 397884
EXPECTED_CUSTOMER_COUNT = 4338
EXPECTED_TOTAL_REVENUE = 8911407.90
EXPECTED_UNIQUE_INVOICES = 18532

EXPECTED_SEGMENTS = {
    "Champions": 945,
    "Loyal Customers": 506,
    "Potential Loyalists": 481,
    "Recent Customers": 135,
    "Promising": 349,
    "Need Attention": 187,
    "At Risk": 488,
    "Cannot Lose Them": 172,
    "Hibernating": 1075,
}

EXPECTED_SHEETS = [
    "Executive Summary",
    "RFM Analysis",
    "Segment Summary",
    "Monthly Sales Analysis",
    "Country Analysis",
    "Top 10 Customers",
    "Data Quality",
]


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0

    def assert_test(self, condition: bool, test_name: str, details: str = ""):
        self.tests_run += 1
        if condition:
            self.passed += 1
            print(f"  [PASS] {test_name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {test_name} -> {details}")

    def run_all(self):
        print("==================================================")
        print("AUTOMATED PIPELINE & RECONCILIATION TEST SUITE")
        print("==================================================")

        # ----------------------------------------------------
        # 1. File Artifact Existence
        # ----------------------------------------------------
        print("\n--- Test Suite 1: Output File Deliverables ---")
        files_to_check = [
            OUTPUT / "cleaned_transactions.csv",
            OUTPUT / "customer_rfm.csv",
            OUTPUT / "segment_summary.csv",
            OUTPUT / "data_quality_report.csv",
            DB_PATH,
            EXCEL_PATH,
        ]
        for f in files_to_check:
            self.assert_test(f.exists() and f.stat().st_size > 0, f"File exists: {f.name}", f"Size: {f.stat().st_size if f.exists() else 0}")

        # ----------------------------------------------------
        # 2. Data Cleaning Validation
        # ----------------------------------------------------
        print("\n--- Test Suite 2: Data Cleaning & Integrity ---")
        df_clean = pd.read_csv(OUTPUT / "cleaned_transactions.csv")
        
        self.assert_test(len(df_clean) == EXPECTED_CLEANED_COUNT, f"Cleaned transaction line count ({len(df_clean):,} == {EXPECTED_CLEANED_COUNT:,})")
        self.assert_test(df_clean["CustomerID"].isna().sum() == 0, "No missing CustomerID in cleaned data")
        self.assert_test(df_clean["InvoiceNo"].isna().sum() == 0, "No missing InvoiceNo in cleaned data")
        self.assert_test(df_clean["InvoiceDate"].isna().sum() == 0, "No missing InvoiceDate in cleaned data")
        self.assert_test((df_clean["Quantity"] <= 0).sum() == 0, "All Quantities strictly positive (> 0)")
        self.assert_test((df_clean["UnitPrice"] <= 0).sum() == 0, "All UnitPrices strictly positive (> 0)")
        self.assert_test(df_clean["InvoiceNo"].astype(str).str.startswith("C").sum() == 0, "No cancellation invoices (starting with 'C')")
        
        # Check revenue calculation
        expected_rev = (df_clean["Quantity"] * df_clean["UnitPrice"]).round(3)
        actual_rev = df_clean["Revenue"].round(3)
        self.assert_test((expected_rev == actual_rev).all(), "Revenue calculation consistency (Revenue == Quantity * UnitPrice)")

        # ----------------------------------------------------
        # 3. Customer & Revenue Reconciliation
        # ----------------------------------------------------
        print("\n--- Test Suite 3: Totals & Ground Truth Reconciliation ---")
        unique_customers = df_clean["CustomerID"].nunique()
        total_rev = df_clean["Revenue"].sum()
        unique_invoices = df_clean["InvoiceNo"].nunique()

        self.assert_test(unique_customers == EXPECTED_CUSTOMER_COUNT, f"Unique customer count ({unique_customers} == {EXPECTED_CUSTOMER_COUNT})")
        self.assert_test(abs(total_rev - EXPECTED_TOTAL_REVENUE) < 1.0, f"Total Revenue (GBP {total_rev:,.2f} ~= GBP {EXPECTED_TOTAL_REVENUE:,.2f})")
        self.assert_test(unique_invoices == EXPECTED_UNIQUE_INVOICES, f"Unique valid invoices ({unique_invoices:,} == {EXPECTED_UNIQUE_INVOICES:,})")

        # ----------------------------------------------------
        # 4. RFM Metrics and Segmentation Validation
        # ----------------------------------------------------
        print("\n--- Test Suite 4: RFM Scoring and Segment Assignment ---")
        df_rfm = pd.read_csv(OUTPUT / "customer_rfm.csv")
        df_seg = pd.read_csv(OUTPUT / "segment_summary.csv")

        self.assert_test(len(df_rfm) == EXPECTED_CUSTOMER_COUNT, f"Customer RFM row count ({len(df_rfm)} == {EXPECTED_CUSTOMER_COUNT})")
        self.assert_test(abs(df_rfm["Monetary"].sum() - EXPECTED_TOTAL_REVENUE) < 1.0, f"Customer RFM total spend matches cleaned revenue (£{df_rfm['Monetary'].sum():,.2f})")
        self.assert_test(abs(df_seg["Total_Revenue"].sum() - EXPECTED_TOTAL_REVENUE) < 1.0, f"Segment summary total revenue matches (£{df_seg['Total_Revenue'].sum():,.2f})")
        self.assert_test(df_seg["Customer_Count"].sum() == EXPECTED_CUSTOMER_COUNT, f"Segment customer counts sum to total customers ({df_seg['Customer_Count'].sum()} == {EXPECTED_CUSTOMER_COUNT})")
        self.assert_test(abs(df_seg["Customer_Percentage"].sum() - 100.0) < 0.1, f"Segment customer percentages sum to ~100% ({df_seg['Customer_Percentage'].sum():.2f}%)")

        # Validate exact customer counts per segment
        actual_segments = df_rfm["Segment"].value_counts().to_dict()
        for seg_name, exp_count in EXPECTED_SEGMENTS.items():
            act_count = actual_segments.get(seg_name, 0)
            self.assert_test(act_count == exp_count, f"Segment '{seg_name}' count ({act_count} == {exp_count})")

        # ----------------------------------------------------
        # 5. SQLite Database Tables Validation
        # ----------------------------------------------------
        print("\n--- Test Suite 5: SQLite Database Integrity ---")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            required_tables = ["cleaned_transactions", "customer_rfm", "segment_summary", "data_quality_report"]
            for tbl in required_tables:
                self.assert_test(tbl in tables, f"Database table exists: {tbl}")

            cursor.execute("SELECT COUNT(*) FROM cleaned_transactions")
            db_trans_count = cursor.fetchone()[0]
            self.assert_test(db_trans_count == EXPECTED_CLEANED_COUNT, f"SQLite cleaned_transactions count ({db_trans_count:,} == {EXPECTED_CLEANED_COUNT:,})")

            cursor.execute("SELECT COUNT(*) FROM customer_rfm")
            db_rfm_count = cursor.fetchone()[0]
            self.assert_test(db_rfm_count == EXPECTED_CUSTOMER_COUNT, f"SQLite customer_rfm count ({db_rfm_count} == {EXPECTED_CUSTOMER_COUNT})")

            cursor.execute("SELECT COUNT(*) FROM segment_summary")
            db_seg_count = cursor.fetchone()[0]
            self.assert_test(db_seg_count == 9, f"SQLite segment_summary count ({db_seg_count} == 9)")

            cursor.execute("SELECT COUNT(*) FROM data_quality_report")
            db_qual_count = cursor.fetchone()[0]
            self.assert_test(db_qual_count >= 15, f"SQLite data_quality_report rows ({db_qual_count} >= 15)")

        # ----------------------------------------------------
        # 6. SQL Query Execution & Cross-Reconciliation with Python
        # ----------------------------------------------------
        print("\n--- Test Suite 6: SQL Execution & Cross-Reconciliation ---")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Q1: Total unique customers
            cursor.execute("SELECT COUNT(DISTINCT CustomerID) FROM cleaned_transactions;")
            sql_cust = cursor.fetchone()[0]
            self.assert_test(sql_cust == EXPECTED_CUSTOMER_COUNT, f"SQL Q1 Unique Customers ({sql_cust} == {EXPECTED_CUSTOMER_COUNT})")

            # Q4: Total revenue
            cursor.execute("SELECT ROUND(SUM(Total_Revenue), 2) FROM segment_summary;")
            sql_rev = cursor.fetchone()[0]
            self.assert_test(abs(sql_rev - EXPECTED_TOTAL_REVENUE) < 1.0, f"SQL Q4 Segment Total Revenue (£{sql_rev:,.2f})")

            # Q9: Total unique invoices
            cursor.execute("SELECT COUNT(DISTINCT InvoiceNo) FROM cleaned_transactions;")
            sql_inv = cursor.fetchone()[0]
            self.assert_test(sql_inv == EXPECTED_UNIQUE_INVOICES, f"SQL Q9 Distinct Invoices ({sql_inv:,} == {EXPECTED_UNIQUE_INVOICES:,})")

            # Q5: Monthly Sales Months Count
            cursor.execute("SELECT COUNT(DISTINCT strftime('%Y-%m', InvoiceDate)) FROM cleaned_transactions;")
            sql_months = cursor.fetchone()[0]
            self.assert_test(sql_months == 13, f"SQL Q5 Monthly Sales Months Count ({sql_months} == 13)")

            # Q6: Top Country is United Kingdom
            cursor.execute("SELECT Country, ROUND(SUM(Revenue), 2) FROM cleaned_transactions GROUP BY Country ORDER BY SUM(Revenue) DESC LIMIT 1;")
            top_ctry, top_ctry_rev = cursor.fetchone()
            self.assert_test(top_ctry == "United Kingdom" and top_ctry_rev > 7000000, f"SQL Q6 Top Country is '{top_ctry}' (£{top_ctry_rev:,.2f})")

            # Q8: High-Value Customers (> 2000)
            cursor.execute("SELECT COUNT(*) FROM customer_rfm WHERE Monetary > 2000;")
            sql_high_val = cursor.fetchone()[0]
            py_high_val = int((df_rfm["Monetary"] > 2000).sum())
            self.assert_test(sql_high_val == py_high_val, f"SQL Q8 High-Value Customers count reconciles ({sql_high_val} == {py_high_val})")

            # Q10: Top customer matches
            cursor.execute("SELECT CustomerID, ROUND(Monetary, 2) FROM customer_rfm ORDER BY Monetary DESC LIMIT 1;")
            top_cust_id, top_cust_mon = cursor.fetchone()
            self.assert_test(top_cust_id == 14646 and abs(top_cust_mon - 280206.02) < 1.0, f"SQL Q10 Top customer is #{top_cust_id} (£{top_cust_mon:,.2f})")

        # ----------------------------------------------------
        # 7. Excel Workbook Structure
        # ----------------------------------------------------
        print("\n--- Test Suite 7: Excel Workbook Verification ---")
        wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)
        sheet_names = wb.sheetnames
        for sheet in EXPECTED_SHEETS:
            self.assert_test(sheet in sheet_names, f"Excel worksheet present: '{sheet}'")
        wb.close()

        # Final Summary
        print("\n==================================================")
        print(f"TEST EXECUTION SUMMARY: {self.passed} PASSED, {self.failed} FAILED (TOTAL {self.tests_run})")
        print("==================================================")

        if self.failed > 0:
            print(f"Validation failed with {self.failed} error(s).")
            sys.exit(1)
        else:
            print("ALL VALIDATION CHECKS PASSED WITH 100% RECONCILIATION!")
            sys.exit(0)


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all()

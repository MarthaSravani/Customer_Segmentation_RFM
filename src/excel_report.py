"""
Excel Reporting Module for Customer Segmentation & RFM Analysis
Generates a professional, multi-tab Excel workbook with formatting, conditional formatting,
freeze panes, auto-fit column widths, summary KPI cards, and native Excel charts.
"""

from pathlib import Path
import pandas as pd
import xlsxwriter


def generate_excel_workbook(
    output_path: Path,
    df_clean: pd.DataFrame,
    rfm: pd.DataFrame,
    segment_summary: pd.DataFrame,
    quality_report: pd.DataFrame,
) -> None:
    """Generate professional Excel workbook with 7 formatted worksheets and native charts."""
    print("Generating professional Excel workbook:", output_path)

    # 1. Prepare auxiliary aggregations
    # Monthly sales
    df_clean_copy = df_clean.copy()
    df_clean_copy["Sales_Month"] = pd.to_datetime(df_clean_copy["InvoiceDate"]).dt.strftime("%Y-%m")
    
    monthly_sales = df_clean_copy.groupby("Sales_Month").agg(
        Monthly_Revenue=("Revenue", "sum"),
        Total_Orders=("InvoiceNo", "nunique"),
        Total_Items_Sold=("Quantity", "sum"),
        Active_Customers=("CustomerID", "nunique"),
    ).reset_index()
    monthly_sales["Average_Order_Value"] = (
        monthly_sales["Monthly_Revenue"] / monthly_sales["Total_Orders"]
    ).round(2)
    monthly_sales["Monthly_Revenue"] = monthly_sales["Monthly_Revenue"].round(2)

    # Country analysis
    country_sales = df_clean_copy.groupby("Country").agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Orders=("InvoiceNo", "nunique"),
        Unique_Customers=("CustomerID", "nunique"),
        Total_Items_Sold=("Quantity", "sum"),
    ).reset_index().sort_values(by="Total_Revenue", ascending=False)
    total_rev = country_sales["Total_Revenue"].sum()
    country_sales["Revenue_Percentage"] = (country_sales["Total_Revenue"] / total_rev * 100).round(2)
    country_sales["Average_Order_Value"] = (
        country_sales["Total_Revenue"] / country_sales["Total_Orders"]
    ).round(2)
    country_sales["Total_Revenue"] = country_sales["Total_Revenue"].round(2)

    # Top 10 customers
    top_10_customers = rfm.sort_values(by="Monetary", ascending=False).head(10).copy()
    # Add country for top customers
    customer_country = df_clean_copy.groupby("CustomerID")["Country"].agg(
        lambda x: x.mode()[0] if not x.empty else "Unknown"
    ).reset_index()
    top_10_customers = top_10_customers.merge(customer_country, on="CustomerID", how="left")
    top_10_customers["Revenue_Contribution_Pct"] = (
        top_10_customers["Monetary"] / total_rev * 100
    ).round(2)

    # Workbook initialization
    workbook = xlsxwriter.Workbook(str(output_path))

    # Color Palette & Styles
    # Primary: #1B365D (Deep Navy), Accent: #008080 (Teal), Neutral: #F4F6F9 (Soft Gray)
    fmt_title = workbook.add_format({
        "bold": True, "font_size": 16, "font_color": "#FFFFFF",
        "bg_color": "#1B365D", "align": "center", "valign": "vcenter",
        "border": 1, "border_color": "#1B365D"
    })
    fmt_subtitle = workbook.add_format({
        "italic": True, "font_size": 10, "font_color": "#555555",
        "align": "left", "valign": "vcenter"
    })
    fmt_header = workbook.add_format({
        "bold": True, "font_size": 11, "font_color": "#FFFFFF",
        "bg_color": "#1B365D", "align": "center", "valign": "vcenter",
        "border": 1, "border_color": "#D3D3D3", "text_wrap": True
    })
    fmt_section = workbook.add_format({
        "bold": True, "font_size": 12, "font_color": "#1B365D",
        "bg_color": "#EAECEE", "valign": "vcenter", "border": 1
    })
    fmt_card_title = workbook.add_format({
        "font_size": 9, "font_color": "#7F8C8D", "bold": True,
        "align": "center", "valign": "vcenter", "bg_color": "#F8F9FA",
        "top": 1, "left": 1, "right": 1, "border_color": "#BDC3C7"
    })
    fmt_card_value = workbook.add_format({
        "font_size": 14, "font_color": "#2C3E50", "bold": True,
        "align": "center", "valign": "vcenter", "bg_color": "#F8F9FA",
        "bottom": 1, "left": 1, "right": 1, "border_color": "#BDC3C7"
    })
    
    # Data cell formats
    fmt_text = workbook.add_format({"border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    fmt_text_center = workbook.add_format({"align": "center", "border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    fmt_int = workbook.add_format({"num_format": "#,##0", "align": "right", "border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    fmt_currency = workbook.add_format({"num_format": "£#,##0.00", "align": "right", "border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    fmt_pct = workbook.add_format({"num_format": "0.00%", "align": "right", "border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    fmt_decimal = workbook.add_format({"num_format": "#,##0.00", "align": "right", "border": 1, "border_color": "#E0E0E0", "valign": "vcenter"})
    
    # Total row format
    fmt_total_label = workbook.add_format({
        "bold": True, "bg_color": "#EAEDED", "border": 1, "border_color": "#BDC3C7", "valign": "vcenter"
    })
    fmt_total_int = workbook.add_format({
        "bold": True, "num_format": "#,##0", "bg_color": "#EAEDED", "border": 1, "border_color": "#BDC3C7", "align": "right", "valign": "vcenter"
    })
    fmt_total_currency = workbook.add_format({
        "bold": True, "num_format": "£#,##0.00", "bg_color": "#EAEDED", "border": 1, "border_color": "#BDC3C7", "align": "right", "valign": "vcenter"
    })
    fmt_total_pct = workbook.add_format({
        "bold": True, "num_format": "0.00%", "bg_color": "#EAEDED", "border": 1, "border_color": "#BDC3C7", "align": "right", "valign": "vcenter"
    })

    # ==========================================
    # SHEET 1: Executive Summary
    # ==========================================
    ws_exec = workbook.add_worksheet("Executive Summary")
    ws_exec.set_tab_color("#1B365D")
    ws_exec.hide_gridlines(False)
    
    # Banner
    ws_exec.merge_range("A1:G1", "CUSTOMER SEGMENTATION & RFM EXECUTIVE DASHBOARD", fmt_title)
    ws_exec.set_row(0, 32)
    ws_exec.write("A2", "Online Retail Transactional Intelligence | Analysis Period: Dec 2010 - Dec 2011", fmt_subtitle)
    ws_exec.set_row(1, 18)

    # KPI Cards
    total_customers = len(rfm)
    total_orders = df_clean["InvoiceNo"].nunique()
    total_revenue = rfm["Monetary"].sum()
    avg_customer_val = total_revenue / total_customers
    avg_order_val = total_revenue / total_orders
    
    cards = [
        ("TOTAL REVENUE", f"£{total_revenue:,.2f}", 3, 0, 4, 1),
        ("TOTAL CUSTOMERS", f"{total_customers:,}", 3, 2, 4, 2),
        ("TOTAL ORDERS", f"{total_orders:,}", 3, 3, 4, 3),
        ("AVG CUSTOMER VALUE", f"£{avg_customer_val:,.2f}", 3, 4, 4, 5),
        ("AVG ORDER VALUE", f"£{avg_order_val:,.2f}", 3, 6, 4, 6),
    ]

    for title, val, r_top, c_left, r_bot, c_right in cards:
        if c_left != c_right:
            ws_exec.merge_range(r_top, c_left, r_top, c_right, title, fmt_card_title)
            ws_exec.merge_range(r_bot, c_left, r_bot, c_right, val, fmt_card_value)
        else:
            ws_exec.write(r_top, c_left, title, fmt_card_title)
            ws_exec.write(r_bot, c_left, val, fmt_card_value)

    ws_exec.set_row(3, 16)
    ws_exec.set_row(4, 26)

    # Segment Breakdown Table in Executive Summary
    ws_exec.merge_range("A7:G7", "Customer Segmentation Performance Snapshot", fmt_section)
    ws_exec.set_row(6, 22)
    
    exec_headers = ["Customer Segment", "Customer Count", "Share of Customers", "Total Revenue", "Share of Revenue", "Avg Recency (Days)", "Avg Frequency (Orders)"]
    for col_idx, h in enumerate(exec_headers):
        ws_exec.write(7, col_idx, h, fmt_header)
    ws_exec.set_row(7, 24)

    seg_sorted = segment_summary.sort_values(by="Total_Revenue", ascending=False).reset_index(drop=True)
    row_idx = 8
    for _, row in seg_sorted.iterrows():
        ws_exec.write(row_idx, 0, row["Segment"], fmt_text)
        ws_exec.write(row_idx, 1, int(row["Customer_Count"]), fmt_int)
        ws_exec.write(row_idx, 2, row["Customer_Percentage"] / 100.0, fmt_pct)
        ws_exec.write(row_idx, 3, float(row["Total_Revenue"]), fmt_currency)
        ws_exec.write(row_idx, 4, float(row["Total_Revenue"]) / total_revenue, fmt_pct)
        ws_exec.write(row_idx, 5, float(row["Average_Recency"]), fmt_decimal)
        ws_exec.write(row_idx, 6, float(row["Average_Frequency"]), fmt_decimal)
        ws_exec.set_row(row_idx, 20)
        row_idx += 1

    # Total Row
    ws_exec.write(row_idx, 0, "Grand Total", fmt_total_label)
    ws_exec.write(row_idx, 1, total_customers, fmt_total_int)
    ws_exec.write(row_idx, 2, 1.0, fmt_total_pct)
    ws_exec.write(row_idx, 3, total_revenue, fmt_total_currency)
    ws_exec.write(row_idx, 4, 1.0, fmt_total_pct)
    ws_exec.write(row_idx, 5, float(rfm["Recency"].mean()), fmt_decimal)
    ws_exec.write(row_idx, 6, float(rfm["Frequency"].mean()), fmt_decimal)
    ws_exec.set_row(row_idx, 22)

    # Strategic Action Matrix
    matrix_start = row_idx + 3
    ws_exec.merge_range(f"A{matrix_start}:G{matrix_start}", "Strategic Action Recommendations by Segment", fmt_section)
    matrix_headers = ["Segment", "RFM Profile", "Strategic Objective", "Recommended Marketing Action", "Channel Priority"]
    ws_exec.merge_range(f"A{matrix_start+1}:B{matrix_start+1}", matrix_headers[0], fmt_header)
    ws_exec.write(f"C{matrix_start+1}", matrix_headers[1], fmt_header)
    ws_exec.write(f"D{matrix_start+1}", matrix_headers[2], fmt_header)
    ws_exec.merge_range(f"E{matrix_start+1}:F{matrix_start+1}", matrix_headers[3], fmt_header)
    ws_exec.write(f"G{matrix_start+1}", matrix_headers[4], fmt_header)

    strategies = [
        ("Champions", "High R, High F, High M", "Retain & Reward", "VIP loyalty programs, early access to new collections, personalized concierge", "Exclusive Email / VIP Line"),
        ("Loyal Customers", "Moderate/High R, High F", "Upsell & Advocate", "Cross-sell high-margin lines, referral incentives, brand ambassador invitations", "Targeted Push / Email"),
        ("Potential Loyalists", "Recent, Moderate F & M", "Cultivate Loyalty", "Membership loyalty onboarding, bundle promotions, category recommendations", "In-app / Omnichannel"),
        ("Recent Customers", "Very Recent, Low F", "Accelerate 2nd Order", "Welcome nurture series, discount vouchers for repeat purchase within 30 days", "Email Nurture Sequence"),
        ("Promising", "Average R, Low F", "Increase Engagement", "Re-engagement promotions, social proof showcases, limited-time category perks", "Social Retargeting / Email"),
        ("Need Attention", "Average R, Avg/High F", "Prevent Attrition", "Limited-time reactivation bonus, customer survey, personalized offers", "SMS / Direct Email"),
        ("At Risk", "Low R, High F & M", "Win Back High Value", "Aggressive win-back campaigns, premium incentives, feedback solicitation", "Personal Outreach / Email"),
        ("Cannot Lose Them", "Very Low R, High M", "Urgent Win Back", "Direct high-touch outreach, substantial store credit, proactive support review", "Account Exec / Direct Call"),
        ("Hibernating", "Lowest R, Lowest F & M", "Low-Cost Clearance", "Automated liquidation discounts, win-back drip or prune from active ad lists", "Low-cost Batch Email"),
    ]
    
    strat_row = matrix_start + 2
    for seg, prof, obj, act, ch in strategies:
        ws_exec.merge_range(f"A{strat_row}:B{strat_row}", seg, fmt_text)
        ws_exec.write(f"C{strat_row}", prof, fmt_text_center)
        ws_exec.write(f"D{strat_row}", obj, fmt_text)
        ws_exec.merge_range(f"E{strat_row}:F{strat_row}", act, fmt_text)
        ws_exec.write(f"G{strat_row}", ch, fmt_text_center)
        strat_row += 1

    # Auto column widths for Executive Summary
    ws_exec.set_column("A:A", 22)
    ws_exec.set_column("B:B", 16)
    ws_exec.set_column("C:C", 22)
    ws_exec.set_column("D:D", 22)
    ws_exec.set_column("E:E", 25)
    ws_exec.set_column("F:F", 25)
    ws_exec.set_column("G:G", 24)

    # ==========================================
    # SHEET 2: RFM Analysis (Customer Level)
    # ==========================================
    ws_rfm = workbook.add_worksheet("RFM Analysis")
    ws_rfm.set_tab_color("#2E86C1")
    ws_rfm.freeze_panes(1, 0)
    
    rfm_cols = ["CustomerID", "Recency (Days)", "Frequency (Orders)", "Monetary (£)", "R_Score", "F_Score", "M_Score", "RFM_Score", "Segment"]
    for c_idx, col_name in enumerate(rfm_cols):
        ws_rfm.write(0, c_idx, col_name, fmt_header)
    ws_rfm.set_row(0, 26)

    # Sort RFM by Monetary desc for immediate utility
    rfm_sorted = rfm.sort_values(by="Monetary", ascending=False).reset_index(drop=True)
    
    for r_idx, r in rfm_sorted.iterrows():
        ws_rfm.write(r_idx + 1, 0, int(r["CustomerID"]), fmt_int)
        ws_rfm.write(r_idx + 1, 1, int(r["Recency"]), fmt_int)
        ws_rfm.write(r_idx + 1, 2, int(r["Frequency"]), fmt_int)
        ws_rfm.write(r_idx + 1, 3, float(r["Monetary"]), fmt_currency)
        ws_rfm.write(r_idx + 1, 4, int(r["R_Score"]), fmt_text_center)
        ws_rfm.write(r_idx + 1, 5, int(r["F_Score"]), fmt_text_center)
        ws_rfm.write(r_idx + 1, 6, int(r["M_Score"]), fmt_text_center)
        ws_rfm.write(r_idx + 1, 7, str(r["RFM_Score"]), fmt_text_center)
        ws_rfm.write(r_idx + 1, 8, str(r["Segment"]), fmt_text)

    ws_rfm.autofilter(0, 0, len(rfm_sorted), len(rfm_cols) - 1)
    
    # Conditional formatting on Scores (3-color soft scale)
    ws_rfm.conditional_format(1, 4, len(rfm_sorted), 6, {
        "type": "3_color_scale",
        "min_color": "#FADBD8",  # soft red
        "mid_color": "#FCF3CF",  # soft yellow
        "max_color": "#D4EFDF"   # soft green
    })

    ws_rfm.set_column("A:A", 15)
    ws_rfm.set_column("B:B", 16)
    ws_rfm.set_column("C:C", 18)
    ws_rfm.set_column("D:D", 18)
    ws_rfm.set_column("E:G", 12)
    ws_rfm.set_column("H:H", 14)
    ws_rfm.set_column("I:I", 22)

    # ==========================================
    # SHEET 3: Segment Summary
    # ==========================================
    ws_seg = workbook.add_worksheet("Segment Summary")
    ws_seg.set_tab_color("#16A085")
    ws_seg.freeze_panes(1, 0)

    seg_headers = [
        "Segment", "Customer Count", "Total Revenue (£)",
        "Avg Recency (Days)", "Avg Frequency (Orders)", "Avg Monetary (£)",
        "Customer Percentage", "Revenue Percentage"
    ]
    for c_idx, h in enumerate(seg_headers):
        ws_seg.write(0, c_idx, h, fmt_header)
    ws_seg.set_row(0, 26)

    seg_display = segment_summary.copy()
    seg_display["Revenue_Percentage"] = (seg_display["Total_Revenue"] / total_revenue * 100).round(2)
    seg_display = seg_display.sort_values(by="Total_Revenue", ascending=False).reset_index(drop=True)

    for r_idx, r in seg_display.iterrows():
        ws_seg.write(r_idx + 1, 0, r["Segment"], fmt_text)
        ws_seg.write(r_idx + 1, 1, int(r["Customer_Count"]), fmt_int)
        ws_seg.write(r_idx + 1, 2, float(r["Total_Revenue"]), fmt_currency)
        ws_seg.write(r_idx + 1, 3, float(r["Average_Recency"]), fmt_decimal)
        ws_seg.write(r_idx + 1, 4, float(r["Average_Frequency"]), fmt_decimal)
        ws_seg.write(r_idx + 1, 5, float(r["Average_Monetary"]), fmt_currency)
        ws_seg.write(r_idx + 1, 6, float(r["Customer_Percentage"]) / 100.0, fmt_pct)
        ws_seg.write(r_idx + 1, 7, float(r["Revenue_Percentage"]) / 100.0, fmt_pct)
        ws_seg.set_row(r_idx + 1, 20)

    tot_row = len(seg_display) + 1
    ws_seg.write(tot_row, 0, "Total", fmt_total_label)
    ws_seg.write(tot_row, 1, total_customers, fmt_total_int)
    ws_seg.write(tot_row, 2, total_revenue, fmt_total_currency)
    ws_seg.write(tot_row, 3, float(rfm["Recency"].mean()), fmt_decimal)
    ws_seg.write(tot_row, 4, float(rfm["Frequency"].mean()), fmt_decimal)
    ws_seg.write(tot_row, 5, float(rfm["Monetary"].mean()), fmt_total_currency)
    ws_seg.write(tot_row, 6, 1.0, fmt_total_pct)
    ws_seg.write(tot_row, 7, 1.0, fmt_total_pct)
    ws_seg.set_row(tot_row, 22)

    ws_seg.autofilter(0, 0, len(seg_display), len(seg_headers) - 1)

    # Column widths
    ws_seg.set_column("A:A", 22)
    ws_seg.set_column("B:B", 16)
    ws_seg.set_column("C:C", 20)
    ws_seg.set_column("D:D", 18)
    ws_seg.set_column("E:E", 22)
    ws_seg.set_column("F:F", 20)
    ws_seg.set_column("G:H", 20)

    # Native Excel Chart 1: Customer Count by Segment
    chart_cust = workbook.add_chart({"type": "column"})
    chart_cust.add_series({
        "name": "Customer Count",
        "categories": ["Segment Summary", 1, 0, len(seg_display), 0],
        "values": ["Segment Summary", 1, 1, len(seg_display), 1],
        "fill": {"color": "#1B365D"},
        "data_labels": {"value": True}
    })
    chart_cust.set_title({"name": "Customer Distribution by Segment"})
    chart_cust.set_x_axis({"name": "Segment"})
    chart_cust.set_y_axis({"name": "Customers"})
    chart_cust.set_legend({"position": "none"})
    chart_cust.set_size({"width": 550, "height": 330})
    ws_seg.insert_chart(f"A{tot_row + 3}", chart_cust)

    # Native Excel Chart 2: Revenue Share Doughnut Chart
    chart_rev = workbook.add_chart({"type": "doughnut"})
    chart_rev.add_series({
        "name": "Revenue Share",
        "categories": ["Segment Summary", 1, 0, len(seg_display), 0],
        "values": ["Segment Summary", 1, 2, len(seg_display), 2],
        "data_labels": {"percentage": True}
    })
    chart_rev.set_title({"name": "Revenue Distribution by Segment"})
    chart_rev.set_style(10)
    chart_rev.set_size({"width": 550, "height": 330})
    ws_seg.insert_chart(f"E{tot_row + 3}", chart_rev)

    # ==========================================
    # SHEET 4: Monthly Sales Analysis
    # ==========================================
    ws_month = workbook.add_worksheet("Monthly Sales Analysis")
    ws_month.set_tab_color("#8E44AD")
    ws_month.freeze_panes(1, 0)

    month_headers = ["Sales Month", "Monthly Revenue (£)", "Total Orders (Unique Invoices)", "Total Items Sold", "Active Customers", "Average Order Value (£)"]
    for c_idx, h in enumerate(month_headers):
        ws_month.write(0, c_idx, h, fmt_header)
    ws_month.set_row(0, 26)

    for r_idx, r in monthly_sales.iterrows():
        ws_month.write(r_idx + 1, 0, str(r["Sales_Month"]), fmt_text_center)
        ws_month.write(r_idx + 1, 1, float(r["Monthly_Revenue"]), fmt_currency)
        ws_month.write(r_idx + 1, 2, int(r["Total_Orders"]), fmt_int)
        ws_month.write(r_idx + 1, 3, int(r["Total_ItemsSold"] if "Total_ItemsSold" in r else r["Total_Items_Sold"]), fmt_int)
        ws_month.write(r_idx + 1, 4, int(r["Active_Customers"]), fmt_int)
        ws_month.write(r_idx + 1, 5, float(r["Average_Order_Value"]), fmt_currency)
        ws_month.set_row(r_idx + 1, 20)

    m_tot_row = len(monthly_sales) + 1
    ws_month.write(m_tot_row, 0, "Total", fmt_total_label)
    ws_month.write(m_tot_row, 1, total_revenue, fmt_total_currency)
    ws_month.write(m_tot_row, 2, total_orders, fmt_total_int)
    ws_month.write(m_tot_row, 3, int(df_clean["Quantity"].sum()), fmt_total_int)
    ws_month.write(m_tot_row, 4, total_customers, fmt_total_int)
    ws_month.write(m_tot_row, 5, total_revenue / total_orders, fmt_total_currency)
    ws_month.set_row(m_tot_row, 22)

    ws_month.autofilter(0, 0, len(monthly_sales), len(month_headers) - 1)
    
    ws_month.set_column("A:A", 16)
    ws_month.set_column("B:B", 22)
    ws_month.set_column("C:C", 28)
    ws_month.set_column("D:D", 18)
    ws_month.set_column("E:E", 18)
    ws_month.set_column("F:F", 24)

    # Native Excel Chart: Monthly Revenue Line Chart
    chart_line = workbook.add_chart({"type": "line"})
    chart_line.add_series({
        "name": "Monthly Revenue (£)",
        "categories": ["Monthly Sales Analysis", 1, 0, len(monthly_sales), 0],
        "values": ["Monthly Sales Analysis", 1, 1, len(monthly_sales), 1],
        "line": {"color": "#8E44AD", "width": 2.5},
        "marker": {"type": "circle", "size": 6, "fill": {"color": "#8E44AD"}},
        "data_labels": {"value": False}
    })
    chart_line.set_title({"name": "Monthly Revenue Trend (Dec 2010 - Dec 2011)"})
    chart_line.set_x_axis({"name": "Month"})
    chart_line.set_y_axis({"name": "Revenue (£)"})
    chart_line.set_size({"width": 800, "height": 380})
    ws_month.insert_chart(f"A{m_tot_row + 3}", chart_line)

    # ==========================================
    # SHEET 5: Country Analysis
    # ==========================================
    ws_ctry = workbook.add_worksheet("Country Analysis")
    ws_ctry.set_tab_color("#D35400")
    ws_ctry.freeze_panes(1, 0)

    ctry_headers = ["Country", "Total Revenue (£)", "Total Orders (Unique Invoices)", "Unique Customers", "Total Items Sold", "Average Order Value (£)", "Revenue Share"]
    for c_idx, h in enumerate(ctry_headers):
        ws_ctry.write(0, c_idx, h, fmt_header)
    ws_ctry.set_row(0, 26)

    for r_idx, r in country_sales.reset_index(drop=True).iterrows():
        ws_ctry.write(r_idx + 1, 0, str(r["Country"]), fmt_text)
        ws_ctry.write(r_idx + 1, 1, float(r["Total_Revenue"]), fmt_currency)
        ws_ctry.write(r_idx + 1, 2, int(r["Total_Orders"]), fmt_int)
        ws_ctry.write(r_idx + 1, 3, int(r["Unique_Customers"]), fmt_int)
        ws_ctry.write(r_idx + 1, 4, int(r["Total_Items_Sold"]), fmt_int)
        ws_ctry.write(r_idx + 1, 5, float(r["Average_Order_Value"]), fmt_currency)
        ws_ctry.write(r_idx + 1, 6, float(r["Revenue_Percentage"]) / 100.0, fmt_pct)
        ws_ctry.set_row(r_idx + 1, 20)

    c_tot_row = len(country_sales) + 1
    ws_ctry.write(c_tot_row, 0, "Total", fmt_total_label)
    ws_ctry.write(c_tot_row, 1, total_revenue, fmt_total_currency)
    ws_ctry.write(c_tot_row, 2, total_orders, fmt_total_int)
    ws_ctry.write(c_tot_row, 3, total_customers, fmt_total_int)
    ws_ctry.write(c_tot_row, 4, int(df_clean["Quantity"].sum()), fmt_total_int)
    ws_ctry.write(c_tot_row, 5, total_revenue / total_orders, fmt_total_currency)
    ws_ctry.write(c_tot_row, 6, 1.0, fmt_total_pct)
    ws_ctry.set_row(c_tot_row, 22)

    ws_ctry.autofilter(0, 0, len(country_sales), len(ctry_headers) - 1)

    ws_ctry.set_column("A:A", 24)
    ws_ctry.set_column("B:B", 20)
    ws_ctry.set_column("C:C", 28)
    ws_ctry.set_column("D:D", 18)
    ws_ctry.set_column("E:E", 18)
    ws_ctry.set_column("F:F", 24)
    ws_ctry.set_column("G:G", 16)

    # Chart: Top 10 Countries by Revenue
    chart_ctry = workbook.add_chart({"type": "bar"})
    chart_ctry.add_series({
        "name": "Revenue (£)",
        "categories": ["Country Analysis", 1, 0, 10, 0],
        "values": ["Country Analysis", 1, 1, 10, 1],
        "fill": {"color": "#D35400"},
        "data_labels": {"value": True}
    })
    chart_ctry.set_title({"name": "Top 10 Geographic Markets by Revenue"})
    chart_ctry.set_x_axis({"name": "Revenue (£)"})
    chart_ctry.set_y_axis({"name": "Country"})
    chart_ctry.set_legend({"position": "none"})
    chart_ctry.set_size({"width": 750, "height": 380})
    ws_ctry.insert_chart(f"A{c_tot_row + 3}", chart_ctry)

    # ==========================================
    # SHEET 6: Top 10 Customers
    # ==========================================
    ws_top = workbook.add_worksheet("Top 10 Customers")
    ws_top.set_tab_color("#27AE60")
    ws_top.freeze_panes(1, 0)

    top_headers = ["Rank", "CustomerID", "Segment", "Country", "Total Spend (£)", "Order Count (Invoices)", "Recency (Days)", "RFM Score", "Revenue Contribution"]
    for c_idx, h in enumerate(top_headers):
        ws_top.write(0, c_idx, h, fmt_header)
    ws_top.set_row(0, 26)

    for rank, (_, r) in enumerate(top_10_customers.iterrows(), 1):
        ws_top.write(rank, 0, rank, fmt_text_center)
        ws_top.write(rank, 1, int(r["CustomerID"]), fmt_int)
        ws_top.write(rank, 2, str(r["Segment"]), fmt_text)
        ws_top.write(rank, 3, str(r["Country"]), fmt_text)
        ws_top.write(rank, 4, float(r["Monetary"]), fmt_currency)
        ws_top.write(rank, 5, int(r["Frequency"]), fmt_int)
        ws_top.write(rank, 6, int(r["Recency"]), fmt_int)
        ws_top.write(rank, 7, str(r["RFM_Score"]), fmt_text_center)
        ws_top.write(rank, 8, float(r["Revenue_Contribution_Pct"]) / 100.0, fmt_pct)
        ws_top.set_row(rank, 22)

    top_tot_row = 11
    ws_top.write(top_tot_row, 0, "Top 10 Total", fmt_total_label)
    ws_top.write(top_tot_row, 1, "-", fmt_total_label)
    ws_top.write(top_tot_row, 2, "-", fmt_total_label)
    ws_top.write(top_tot_row, 3, "-", fmt_total_label)
    top_10_rev = top_10_customers["Monetary"].sum()
    ws_top.write(top_tot_row, 4, top_10_rev, fmt_total_currency)
    ws_top.write(top_tot_row, 5, int(top_10_customers["Frequency"].sum()), fmt_total_int)
    ws_top.write(top_tot_row, 6, float(top_10_customers["Recency"].mean()), fmt_decimal)
    ws_top.write(top_tot_row, 7, "-", fmt_total_label)
    ws_top.write(top_tot_row, 8, top_10_rev / total_revenue, fmt_total_pct)
    ws_top.set_row(top_tot_row, 24)

    ws_top.autofilter(0, 0, 10, len(top_headers) - 1)

    ws_top.set_column("A:A", 10)
    ws_top.set_column("B:B", 16)
    ws_top.set_column("C:C", 22)
    ws_top.set_column("D:D", 18)
    ws_top.set_column("E:E", 20)
    ws_top.set_column("F:F", 24)
    ws_top.set_column("G:G", 16)
    ws_top.set_column("H:H", 14)
    ws_top.set_column("I:I", 22)

    # Top 10 Chart
    chart_top = workbook.add_chart({"type": "column"})
    chart_top.add_series({
        "name": "Total Spend (£)",
        "categories": ["Top 10 Customers", 1, 1, 10, 1],
        "values": ["Top 10 Customers", 1, 4, 10, 4],
        "fill": {"color": "#27AE60"},
        "data_labels": {"value": True}
    })
    chart_top.set_title({"name": "Top 10 Highest Spending Customers (£)"})
    chart_top.set_x_axis({"name": "CustomerID"})
    chart_top.set_y_axis({"name": "Total Spend (£)"})
    chart_top.set_legend({"position": "none"})
    chart_top.set_size({"width": 750, "height": 350})
    ws_top.insert_chart("A14", chart_top)

    # ==========================================
    # SHEET 7: Data Quality
    # ==========================================
    ws_qual = workbook.add_worksheet("Data Quality")
    ws_qual.set_tab_color("#7F8C8D")
    ws_qual.freeze_panes(1, 0)

    qual_headers = ["Audit Step", "Metric / Validation Check", "Row Count / Value", "Operational Impact & Rule Applied", "Status"]
    for c_idx, h in enumerate(qual_headers):
        ws_qual.write(0, c_idx, h, fmt_header)
    ws_qual.set_row(0, 26)

    for r_idx, r in quality_report.iterrows():
        ws_qual.write(r_idx + 1, 0, r_idx + 1, fmt_text_center)
        ws_qual.write(r_idx + 1, 1, str(r["Metric"]), fmt_text)
        
        val = r["Value"]
        if isinstance(val, (int, float)):
            if isinstance(val, float) and val > 1000:
                ws_qual.write(r_idx + 1, 2, val, fmt_currency)
            elif isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
                ws_qual.write(r_idx + 1, 2, int(val), fmt_int)
            else:
                ws_qual.write(r_idx + 1, 2, val, fmt_decimal)
        else:
            ws_qual.write(r_idx + 1, 2, str(val), fmt_text_center)

        ws_qual.write(r_idx + 1, 3, str(r.get("Description", "")), fmt_text)
        status = str(r.get("Status", "PASSED"))
        ws_qual.write(r_idx + 1, 4, status, fmt_text_center)
        ws_qual.set_row(r_idx + 1, 20)

    ws_qual.autofilter(0, 0, len(quality_report), len(qual_headers) - 1)

    ws_qual.set_column("A:A", 12)
    ws_qual.set_column("B:B", 32)
    ws_qual.set_column("C:C", 22)
    ws_qual.set_column("D:D", 50)
    ws_qual.set_column("E:E", 14)

    # Close workbook
    workbook.close()
    print("Excel workbook successfully created at:", output_path)

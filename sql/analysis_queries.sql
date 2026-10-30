-- =====================================================================
-- CUSTOMER SEGMENTATION & RFM ANALYSIS - SQL ANALYTICS SUITE
-- Database: retail_analysis.db
-- Dialect: SQLite / ANSI SQL Compatible
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Total Unique Customers
-- Calculates the total number of distinct paying customers.
-- Reconciles with Python: 4,338 customers
-- ---------------------------------------------------------------------
SELECT COUNT(DISTINCT CustomerID) AS Total_Unique_Customers
FROM cleaned_transactions;


-- ---------------------------------------------------------------------
-- 2. Customer Distribution by Segment
-- Aggregates customer count and customer percentage across all 9 segments.
-- Ordered by customer volume descending.
-- ---------------------------------------------------------------------
SELECT 
    Segment,
    Customer_Count,
    Customer_Percentage
FROM segment_summary
ORDER BY Customer_Count DESC;


-- ---------------------------------------------------------------------
-- 3. Top 10 Highest-Spending Customers
-- Identifies the top 10 customers by total monetary spend,
-- displaying their recency, frequency, RFM score, and assigned segment.
-- ---------------------------------------------------------------------
SELECT 
    CustomerID,
    Recency,
    Frequency,
    ROUND(Monetary, 2) AS Total_Spend,
    RFM_Score,
    Segment
FROM customer_rfm
ORDER BY Monetary DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 4. Revenue by Customer Segment
-- Computes total monetary revenue, customer count, and average spend per customer
-- for each RFM segment, sorted by total revenue descending.
-- Reconciles with Python: Total = £8,911,407.90
-- ---------------------------------------------------------------------
SELECT 
    Segment,
    ROUND(Total_Revenue, 2) AS Segment_Revenue,
    Customer_Count,
    ROUND(Average_Monetary, 2) AS Average_Spending_Per_Customer,
    ROUND(Total_Revenue * 100.0 / (SELECT SUM(Total_Revenue) FROM segment_summary), 2) AS Revenue_Percentage
FROM segment_summary
ORDER BY Total_Revenue DESC;


-- ---------------------------------------------------------------------
-- 5. Monthly Sales Analysis
-- Tracks monthly performance, revenue, distinct order count, active customers,
-- and average order value (AOV).
-- Note: Uses COUNT(DISTINCT InvoiceNo) for unique order calculation.
-- ---------------------------------------------------------------------
SELECT 
    strftime('%Y-%m', InvoiceDate) AS Sales_Month,
    ROUND(SUM(Revenue), 2) AS Monthly_Revenue,
    COUNT(DISTINCT InvoiceNo) AS Total_Orders,
    COUNT(DISTINCT CustomerID) AS Active_Customers,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS Average_Order_Value
FROM cleaned_transactions
GROUP BY Sales_Month
ORDER BY Sales_Month ASC;


-- ---------------------------------------------------------------------
-- 6. Country-wise Revenue
-- Summarizes revenue, distinct orders, unique customer count, and revenue share
-- by geographic market, sorted by total revenue descending.
-- ---------------------------------------------------------------------
SELECT 
    Country,
    ROUND(SUM(Revenue), 2) AS Total_Revenue,
    COUNT(DISTINCT InvoiceNo) AS Total_Orders,
    COUNT(DISTINCT CustomerID) AS Unique_Customers,
    ROUND(SUM(Revenue) * 100.0 / (SELECT SUM(Revenue) FROM cleaned_transactions), 2) AS Revenue_Share_Pct
FROM cleaned_transactions
GROUP BY Country
ORDER BY Total_Revenue DESC
LIMIT 10;


-- ---------------------------------------------------------------------
-- 7. Average RFM Metrics by Segment
-- Calculates the average Recency (days), Frequency (unique orders),
-- and Monetary value (£) across each customer segment.
-- ---------------------------------------------------------------------
SELECT 
    Segment,
    ROUND(AVG(Recency), 2) AS Average_Recency_Days,
    ROUND(AVG(Frequency), 2) AS Average_Frequency_Orders,
    ROUND(AVG(Monetary), 2) AS Average_Monetary_Value
FROM customer_rfm
GROUP BY Segment
ORDER BY Average_Monetary_Value DESC;


-- ---------------------------------------------------------------------
-- 8. High-Value Customers
-- Retrieves customers with lifetime spend exceeding £2,000,
-- highlighting Champions and Loyal customers driving business growth.
-- ---------------------------------------------------------------------
SELECT 
    CustomerID,
    Recency,
    Frequency,
    ROUND(Monetary, 2) AS Total_Monetary,
    RFM_Score,
    Segment
FROM customer_rfm
WHERE Monetary > 2000
ORDER BY Monetary DESC;


-- ---------------------------------------------------------------------
-- 9. Total Unique Invoices
-- Calculates distinct valid order count across the entire dataset.
-- Critical: Uses COUNT(DISTINCT InvoiceNo) to avoid conflating transaction lines with orders.
-- Reconciles with Python: 18,532 unique invoices
-- ---------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT InvoiceNo) AS Total_Unique_Invoices
FROM cleaned_transactions;


-- ---------------------------------------------------------------------
-- 10. Customer Revenue Contribution (Pareto Cumulative Analysis)
-- Evaluates revenue concentration and cumulative contribution across customers,
-- ranking customers from highest to lowest spend.
-- ---------------------------------------------------------------------
WITH CustomerSpending AS (
    SELECT 
        CustomerID,
        Monetary,
        Segment,
        ROUND(Monetary * 100.0 / (SELECT SUM(Monetary) FROM customer_rfm), 4) AS Revenue_Contribution_Pct,
        SUM(Monetary) OVER (ORDER BY Monetary DESC) AS Cumulative_Revenue,
        ROUND(SUM(Monetary) OVER (ORDER BY Monetary DESC) * 100.0 / (SELECT SUM(Monetary) FROM customer_rfm), 2) AS Cumulative_Revenue_Pct,
        ROW_NUMBER() OVER (ORDER BY Monetary DESC) AS Customer_Rank,
        ROUND(ROW_NUMBER() OVER (ORDER BY Monetary DESC) * 100.0 / (SELECT COUNT(*) FROM customer_rfm), 2) AS Cumulative_Customer_Pct
    FROM customer_rfm
)
SELECT 
    CustomerID,
    Customer_Rank,
    ROUND(Monetary, 2) AS Total_Spend,
    Segment,
    Revenue_Contribution_Pct,
    ROUND(Cumulative_Revenue, 2) AS Cumulative_Revenue,
    Cumulative_Revenue_Pct,
    Cumulative_Customer_Pct
FROM CustomerSpending
ORDER BY Customer_Rank ASC
LIMIT 20;

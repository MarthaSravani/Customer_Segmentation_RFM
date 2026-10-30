-- Query 05: Monthly Sales Analysis
-- Tracks monthly revenue, distinct order count (InvoiceNo), active customers, and AOV
SELECT 
    strftime('%Y-%m', InvoiceDate) AS Sales_Month,
    ROUND(SUM(Revenue), 2) AS Monthly_Revenue,
    COUNT(DISTINCT InvoiceNo) AS Total_Orders,
    COUNT(DISTINCT CustomerID) AS Active_Customers,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS Average_Order_Value
FROM cleaned_transactions
GROUP BY Sales_Month
ORDER BY Sales_Month ASC;

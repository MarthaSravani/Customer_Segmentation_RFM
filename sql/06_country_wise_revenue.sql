-- Query 06: Country-wise Revenue
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

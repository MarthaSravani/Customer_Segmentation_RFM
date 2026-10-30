-- Query 03: Top 10 Highest-Spending Customers
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

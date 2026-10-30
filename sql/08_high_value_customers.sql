-- Query 08: High-Value Customers
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

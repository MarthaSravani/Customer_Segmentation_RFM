-- Query 07: Average RFM Metrics by Segment
SELECT 
    Segment,
    ROUND(AVG(Recency), 2) AS Average_Recency_Days,
    ROUND(AVG(Frequency), 2) AS Average_Frequency_Orders,
    ROUND(AVG(Monetary), 2) AS Average_Monetary_Value
FROM customer_rfm
GROUP BY Segment
ORDER BY Average_Monetary_Value DESC;

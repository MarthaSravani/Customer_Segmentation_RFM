-- Query 10: Customer Revenue Contribution (Pareto Analysis)
-- Evaluates individual customer revenue share and cumulative contribution percentage
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
LIMIT 50;

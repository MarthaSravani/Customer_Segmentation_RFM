-- Query 04: Revenue by Customer Segment
SELECT 
    Segment,
    ROUND(Total_Revenue, 2) AS Segment_Revenue,
    Customer_Count,
    ROUND(Average_Monetary, 2) AS Average_Spending_Per_Customer,
    ROUND(Total_Revenue * 100.0 / (SELECT SUM(Total_Revenue) FROM segment_summary), 2) AS Revenue_Percentage
FROM segment_summary
ORDER BY Total_Revenue DESC;

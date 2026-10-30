-- Query 02: Customer Distribution by Segment
SELECT 
    Segment,
    Customer_Count,
    Customer_Percentage
FROM segment_summary
ORDER BY Customer_Count DESC;

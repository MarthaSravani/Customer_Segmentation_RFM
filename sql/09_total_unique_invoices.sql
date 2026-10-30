-- Query 09: Total Unique Invoices
-- Calculates total unique order count using COUNT(DISTINCT InvoiceNo).
-- Do not confuse line item records with unique invoices.
SELECT 
    COUNT(DISTINCT InvoiceNo) AS Total_Unique_Invoices
FROM cleaned_transactions;

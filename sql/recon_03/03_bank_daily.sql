-- Control 3B: Funding (Settlement) Module -> Bank Statement
-- Daily bank statement summary (disbursement)

SELECT
    CAST(statement_date AS DATE) AS statement_date,
    COUNT(*) AS statement_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount

FROM bank_statements

WHERE statement_category = 'DISBURSEMENT'
  AND CAST(statement_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(statement_date AS DATE) < DATE '{{ end_date }}'

GROUP BY 1
ORDER BY 1;

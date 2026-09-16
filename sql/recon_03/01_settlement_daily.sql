-- Control 3A: Transaction State B -> Funding (Settlement) Module
-- Daily funding-module summary (bank statement summary is in 03_bank_daily.sql)

SELECT
    CAST(settlement_date AS DATE) AS settlement_date,
    COUNT(*) AS settlement_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount

FROM settlement_records

WHERE settlement_category = 'DISBURSEMENT'
  AND CAST(settlement_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(settlement_date AS DATE) < DATE '{{ end_date }}'

GROUP BY 1
ORDER BY 1;
-- Control 4: Payment -> Repayment

SELECT
    CAST(event_date AS DATE) AS repayment_date,
    COUNT(*) AS repayment_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount

FROM transaction_events

WHERE event_type = 'REPAYMENT'
  AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(event_date AS DATE) < DATE '{{ end_date }}'

GROUP BY 1
ORDER BY 1;
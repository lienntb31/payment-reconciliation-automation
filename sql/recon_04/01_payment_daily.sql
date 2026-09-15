-- Control 4: Payment -> Repayment

SELECT
    CAST(payment_date AS DATE) AS payment_date,
    COUNT(*) AS payment_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount

FROM payment_records

WHERE payment_status = 'SUCCESS'
  AND CAST(payment_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(payment_date AS DATE) < DATE '{{ end_date }}'

GROUP BY 1
ORDER BY 1;
-- Control 2: Transaction State A -> Transaction State B
-- Daily State B summary

SELECT
    CAST(event_date AS DATE) AS event_date,
    COUNT(*) AS transaction_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount
FROM transaction_events
WHERE event_type = 'STATE_B'
  AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(event_date AS DATE) < DATE '{{ end_date }}'
GROUP BY 1
ORDER BY 1;
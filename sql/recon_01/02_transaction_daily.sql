-- Control 1: Source -> Transaction State A
-- Daily transaction-state summary

SELECT
    CAST(event_date AS DATE) AS event_date,
    COUNT(*) AS transaction_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount
FROM transaction_events
WHERE event_type = 'STATE_A'
  AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(event_date AS DATE) < DATE '{{ end_date }}'
GROUP BY 1
ORDER BY 1;
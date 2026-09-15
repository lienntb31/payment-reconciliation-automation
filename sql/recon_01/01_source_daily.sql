-- Control 1: Source -> Transaction State A
-- Daily source-level summary

SELECT
    CAST(transaction_date AS DATE) AS transaction_date,
    COUNT(*) AS transaction_count,
    SUM(CAST(amount AS DECIMAL(18, 2))) AS total_amount
FROM source_transactions
WHERE CAST(transaction_date AS DATE) >= DATE '{{ start_date }}'
  AND CAST(transaction_date AS DATE) < DATE '{{ end_date }}'
GROUP BY 1
ORDER BY 1;
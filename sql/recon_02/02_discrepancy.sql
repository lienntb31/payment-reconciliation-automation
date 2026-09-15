-- Control 2: Transaction State A -> Transaction State B

WITH state_a_pool AS (
    SELECT
        transaction_id AS recon_key,
        CAST(event_date AS DATE) AS date_a,
        CAST(amount AS DECIMAL(18, 2)) AS amount_a
    FROM transaction_events
    WHERE event_type = 'STATE_A'
      AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(event_date AS DATE) < DATE '{{ end_date }}'
),

state_b_pool AS (
    SELECT
        transaction_id AS recon_key,
        CAST(event_date AS DATE) AS date_b,
        CAST(amount AS DECIMAL(18, 2)) AS amount_b
    FROM transaction_events
    WHERE event_type = 'STATE_B'
      AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(event_date AS DATE) < DATE '{{ end_date }}'
),

reconciliation_pool AS (
    SELECT
        COALESCE(a.recon_key, b.recon_key) AS recon_key,
        a.date_a,
        b.date_b,
        a.amount_a,
        b.amount_b,

        COALESCE(a.amount_a, DECIMAL '0.00')
            - COALESCE(b.amount_b, DECIMAL '0.00') AS diff,

        SUBSTR(
            CAST(COALESCE(a.date_a, b.date_b) AS VARCHAR),
            1,
            7
        ) AS month

    FROM state_a_pool a

    FULL OUTER JOIN state_b_pool b
        ON a.recon_key = b.recon_key
),

timing_mapping AS (
    SELECT
        month,
        recon_key
    FROM reconciliation_pool
    GROUP BY 1, 2
    HAVING SUM(diff) = DECIMAL '0.00'
)

SELECT
    r.recon_key,
    r.date_a,
    r.date_b,
    r.amount_a,
    r.amount_b,
    r.diff,

    CASE
        WHEN t.recon_key IS NOT NULL
            THEN 'TIMING_DIFFERENCE'

        WHEN r.amount_a IS NULL
            THEN 'MISSING_STATE_A'

        WHEN r.amount_b IS NULL
            THEN 'MISSING_STATE_B'

        WHEN r.diff <> DECIMAL '0.00'
            THEN 'AMOUNT_DIFFERENCE'

        WHEN r.date_a <> r.date_b
            THEN 'DATE_DIFFERENCE'

        ELSE 'OTHER'
    END AS discrepancy_type

FROM reconciliation_pool r

LEFT JOIN timing_mapping t
    ON r.month = t.month
   AND r.recon_key = t.recon_key

WHERE
       r.amount_a IS NULL
    OR r.amount_b IS NULL
    OR r.diff <> DECIMAL '0.00'
    OR r.date_a <> r.date_b

ORDER BY r.recon_key;
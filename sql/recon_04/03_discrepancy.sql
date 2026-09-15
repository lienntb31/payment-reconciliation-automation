-- Control 4: Payment -> Repayment

WITH payment_pool AS (

    SELECT
        payment_id AS recon_key,
        CAST(payment_date AS DATE) AS date_a,
        CAST(amount AS DECIMAL(18, 2)) AS amount_a

    FROM payment_records

    WHERE payment_status = 'SUCCESS'
      AND CAST(payment_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(payment_date AS DATE) < DATE '{{ end_date }}'
),

repayment_pool AS (

    SELECT
        payment_id AS recon_key,
        CAST(event_date AS DATE) AS date_b,
        CAST(amount AS DECIMAL(18, 2)) AS amount_b

    FROM transaction_events

    WHERE event_type = 'REPAYMENT'
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
        -
        COALESCE(b.amount_b, DECIMAL '0.00') AS diff,

        SUBSTR(
            CAST(
                COALESCE(a.date_a, b.date_b)
                AS VARCHAR
            ),
            1,
            7
        ) AS month

    FROM payment_pool a

    FULL OUTER JOIN repayment_pool b
        ON a.recon_key = b.recon_key
),

timing_mapping AS (

    SELECT
        month,
        recon_key

    FROM reconciliation_pool

    GROUP BY 1, 2

    HAVING SUM(diff) = DECIMAL '0.00'
),

known_issue_mapping AS (

    SELECT
        recon_key,
        issue_category,
        issue_note

    FROM known_issues

    WHERE recon_control = 'CONTROL_4'
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
            THEN 'MISSING_PAYMENT'

        WHEN r.amount_b IS NULL
            THEN 'MISSING_REPAYMENT'

        WHEN r.diff <> DECIMAL '0.00'
            THEN 'AMOUNT_DIFFERENCE'

        WHEN r.date_a <> r.date_b
            THEN 'DATE_DIFFERENCE'

        ELSE 'OTHER'

    END AS discrepancy_type,

    k.issue_category,
    k.issue_note

FROM reconciliation_pool r

LEFT JOIN timing_mapping t
    ON r.month = t.month
   AND r.recon_key = t.recon_key

LEFT JOIN known_issue_mapping k
    ON r.recon_key = k.recon_key

WHERE
       r.amount_a IS NULL
    OR r.amount_b IS NULL
    OR r.diff <> DECIMAL '0.00'
    OR r.date_a <> r.date_b

ORDER BY r.recon_key;
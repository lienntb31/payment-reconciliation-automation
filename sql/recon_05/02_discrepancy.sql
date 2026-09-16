-- Control 5A: Repayment -> Funding (Settlement) Module
-- Supports direct and grouped settlement reconciliation.
-- Stage 2 (Funding Module -> Bank Statement) is in 04_discrepancy_bank.sql.

WITH repayment_pool AS (

    SELECT
        transaction_id,
        settlement_group_id,
        CAST(event_date AS DATE) AS repayment_date,
        CAST(amount AS DECIMAL(18, 2)) AS repayment_amount

    FROM transaction_events

    WHERE event_type = 'REPAYMENT'
      AND CAST(event_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(event_date AS DATE) < DATE '{{ end_date }}'
),

settlement_pool AS (

    SELECT
        settlement_reference,
        transaction_id,
        settlement_group_id,
        CAST(settlement_date AS DATE) AS settlement_date,
        CAST(amount AS DECIMAL(18, 2)) AS settlement_amount,
        settlement_type

    FROM settlement_records

    WHERE settlement_category = 'REPAYMENT'
      AND CAST(settlement_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(settlement_date AS DATE) < DATE '{{ end_date }}'
),

/* =========================================================
   DIRECT 1:1
   ========================================================= */

direct_reconciliation AS (

    SELECT

        COALESCE(
            r.transaction_id,
            s.transaction_id
        ) AS recon_key,

        r.repayment_date AS date_a,
        s.settlement_date AS date_b,

        r.repayment_amount AS amount_a,
        s.settlement_amount AS amount_b,

        COALESCE(
            r.repayment_amount,
            DECIMAL '0.00'
        )
        -
        COALESCE(
            s.settlement_amount,
            DECIMAL '0.00'
        ) AS diff,

        SUBSTR(
            CAST(
                COALESCE(
                    r.repayment_date,
                    s.settlement_date
                ) AS VARCHAR
            ),
            1,
            7
        ) AS month

    FROM repayment_pool r

    FULL OUTER JOIN settlement_pool s
        ON r.transaction_id = s.transaction_id

    WHERE
        r.settlement_group_id IS NULL
        AND s.settlement_group_id IS NULL
),

/* =========================================================
   GROUPED REPAYMENT
   ========================================================= */

repayment_grouped AS (

    SELECT

        settlement_group_id AS recon_key,

        MIN(repayment_date) AS date_a,

        SUM(repayment_amount) AS amount_a

    FROM repayment_pool

    WHERE settlement_group_id IS NOT NULL

    GROUP BY settlement_group_id
),

/* =========================================================
   GROUPED SETTLEMENT
   ========================================================= */

settlement_grouped AS (

    SELECT

        settlement_group_id AS recon_key,

        MIN(settlement_date) AS date_b,

        SUM(settlement_amount) AS amount_b

    FROM settlement_pool

    WHERE settlement_group_id IS NOT NULL

    GROUP BY settlement_group_id
),

/* =========================================================
   GROUPED RECONCILIATION
   ========================================================= */

grouped_reconciliation AS (

    SELECT

        COALESCE(
            r.recon_key,
            s.recon_key
        ) AS recon_key,

        r.date_a,
        s.date_b,

        r.amount_a,
        s.amount_b,

        COALESCE(
            r.amount_a,
            DECIMAL '0.00'
        )
        -
        COALESCE(
            s.amount_b,
            DECIMAL '0.00'
        ) AS diff,

        SUBSTR(
            CAST(
                COALESCE(r.date_a, s.date_b)
                AS VARCHAR
            ),
            1,
            7
        ) AS month

    FROM repayment_grouped r

    FULL OUTER JOIN settlement_grouped s
        ON r.recon_key = s.recon_key
),

reconciliation_pool AS (

    SELECT *
    FROM direct_reconciliation

    UNION ALL

    SELECT *
    FROM grouped_reconciliation
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

    WHERE recon_control = 'CONTROL_5A'
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
            THEN 'MISSING_REPAYMENT'

        WHEN r.amount_b IS NULL
            THEN 'MISSING_SETTLEMENT'

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
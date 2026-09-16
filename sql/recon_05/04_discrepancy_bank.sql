-- Control 5B: Funding (Settlement) Module -> Bank Statement
-- Reconciles the funding module against the actual bank statement for
-- repayment, using the funding module as the key bridge between the
-- credit transaction module and the bank. Also surfaces the latest
-- funding status held for that order.
-- Supports both direct (1:1) and grouped/batch repayments.

WITH funding_pool AS (

    SELECT
        settlement_reference,
        settlement_group_id,
        CAST(settlement_date AS DATE) AS funding_date,
        CAST(amount AS DECIMAL(18, 2)) AS funding_amount,
        funding_status

    FROM settlement_records

    WHERE settlement_category = 'REPAYMENT'
      AND CAST(settlement_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(settlement_date AS DATE) < DATE '{{ end_date }}'
),

bank_pool AS (

    SELECT
        settlement_reference,
        settlement_group_id,
        CAST(statement_date AS DATE) AS bank_date,
        CAST(amount AS DECIMAL(18, 2)) AS bank_amount

    FROM bank_statements

    WHERE statement_category = 'REPAYMENT'
      AND CAST(statement_date AS DATE) >= DATE '{{ start_date }}'
      AND CAST(statement_date AS DATE) < DATE '{{ end_date }}'
),

/* =========================================================
   DIRECT 1:1
   ========================================================= */

direct_reconciliation AS (

    SELECT
        COALESCE(f.settlement_reference, b.settlement_reference) AS recon_key,

        f.funding_date AS date_a,
        b.bank_date AS date_b,

        f.funding_amount AS amount_a,
        b.bank_amount AS amount_b,

        COALESCE(f.funding_amount, DECIMAL '0.00')
            - COALESCE(b.bank_amount, DECIMAL '0.00') AS diff,

        f.funding_status,

        SUBSTR(
            CAST(COALESCE(f.funding_date, b.bank_date) AS VARCHAR),
            1,
            7
        ) AS month

    FROM funding_pool f

    FULL OUTER JOIN bank_pool b
        ON f.settlement_reference = b.settlement_reference

    WHERE
        COALESCE(f.settlement_group_id, b.settlement_group_id) IS NULL
),

/* =========================================================
   GROUPED FUNDING SIDE
   ========================================================= */

funding_grouped AS (

    SELECT
        settlement_group_id AS recon_key,

        MIN(funding_date) AS date_a,

        SUM(funding_amount) AS amount_a,

        MAX(funding_status) AS funding_status

    FROM funding_pool

    WHERE settlement_group_id IS NOT NULL

    GROUP BY settlement_group_id
),

/* =========================================================
   GROUPED BANK SIDE
   ========================================================= */

bank_grouped AS (

    SELECT
        settlement_group_id AS recon_key,

        MIN(bank_date) AS date_b,

        SUM(bank_amount) AS amount_b

    FROM bank_pool

    WHERE settlement_group_id IS NOT NULL

    GROUP BY settlement_group_id
),

/* =========================================================
   GROUPED RECONCILIATION
   ========================================================= */

grouped_reconciliation AS (

    SELECT
        COALESCE(f.recon_key, b.recon_key) AS recon_key,

        f.date_a,
        b.date_b,

        f.amount_a,
        b.amount_b,

        COALESCE(f.amount_a, DECIMAL '0.00')
            - COALESCE(b.amount_b, DECIMAL '0.00') AS diff,

        f.funding_status,

        SUBSTR(
            CAST(COALESCE(f.date_a, b.date_b) AS VARCHAR),
            1,
            7
        ) AS month

    FROM funding_grouped f

    FULL OUTER JOIN bank_grouped b
        ON f.recon_key = b.recon_key
),

/* =========================================================
   COMPLETE RECONCILIATION POOL
   ========================================================= */

reconciliation_pool AS (

    SELECT * FROM direct_reconciliation

    UNION ALL

    SELECT * FROM grouped_reconciliation
),

/* =========================================================
   TIMING DIFFERENCE
   ========================================================= */

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

    WHERE recon_control = 'CONTROL_5B'
)

SELECT

    r.recon_key,

    r.date_a,
    r.date_b,

    r.amount_a,
    r.amount_b,

    r.diff,

    r.funding_status,

    CASE

        WHEN t.recon_key IS NOT NULL
            THEN 'TIMING_DIFFERENCE'

        WHEN r.amount_a IS NULL
            THEN 'MISSING_FUNDING'

        WHEN r.amount_b IS NULL
            THEN 'MISSING_BANK'

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

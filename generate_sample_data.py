from pathlib import Path
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

OUTPUT_DIR = Path("data/sample")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. SOURCE TRANSACTIONS
#    Control 1: Source -> Transaction State A
# ============================================================

source_transactions = pd.DataFrame([
    # matched
    ["T001", "2026-08-01", 1000.00, "SOURCE_A"],
    ["T002", "2026-08-01", 2000.00, "SOURCE_A"],

    # timing difference candidate:
    # source = Aug 02, transaction event = Aug 03
    ["T003", "2026-08-02", 1500.00, "SOURCE_A"],

    # amount difference
    ["T004", "2026-08-03", 800.00, "SOURCE_A"],

    # missing on transaction side
    ["T005", "2026-08-04", 500.00, "SOURCE_A"],

    # date difference
    ["T006", "2026-08-05", 700.00, "SOURCE_A"],
], columns=[
    "transaction_id",
    "transaction_date",
    "amount",
    "source_system",
])


# ============================================================
# 2. TRANSACTION EVENTS
#    Used by Control 1 / 2 / 4
# ============================================================

transaction_events = pd.DataFrame([
    # -------------------------
    # Control 1 - STATE_A
    # -------------------------

    ["T001", "2026-08-01", 1000.00, "STATE_A", None],
    ["T002", "2026-08-01", 2000.00, "STATE_A", None],

    # date difference / timing candidate
    ["T003", "2026-08-03", 1500.00, "STATE_A", None],

    # amount difference
    ["T004", "2026-08-03", 750.00, "STATE_A", None],

    # T005 intentionally missing

    # date difference
    ["T006", "2026-08-06", 700.00, "STATE_A", None],

    # missing from source
    ["T007", "2026-08-05", 600.00, "STATE_A", None],

    # -------------------------
    # Control 2 - STATE_B
    # -------------------------

    ["T001", "2026-08-02", 1000.00, "STATE_B", None],
    ["T002", "2026-08-02", 2000.00, "STATE_B", None],
    ["T003", "2026-08-03", 1500.00, "STATE_B", None],
    ["T004", "2026-08-04", 750.00, "STATE_B", None],

    # missing STATE_B
    ["T006", "2026-08-06", 700.00, "STATE_B", None],

    # STATE_B only
    ["T008", "2026-08-06", 900.00, "STATE_B", None],

    # -------------------------
    # Control 4 - REPAYMENT
    # -------------------------

    ["R001", "2026-08-10", 400.00, "REPAYMENT", "P001"],
    ["R002", "2026-08-11", 500.00, "REPAYMENT", "P002"],

    # date difference
    ["R003", "2026-08-12", 300.00, "REPAYMENT", "P003"],

    # P004 intentionally missing
], columns=[
    "transaction_id",
    "event_date",
    "amount",
    "event_type",
    "payment_id",
])


# ============================================================
# 3. PAYMENT RECORDS
#    Control 4: Payment -> Repayment
# ============================================================

payment_records = pd.DataFrame([
    # matched
    ["P001", "2026-08-10", 400.00, "SUCCESS"],

    # matched
    ["P002", "2026-08-11", 500.00, "SUCCESS"],

    # date mismatch
    ["P003", "2026-08-13", 300.00, "SUCCESS"],

    # missing repayment
    ["P004", "2026-08-14", 200.00, "SUCCESS"],

    # failed payment should be filtered out
    ["P005", "2026-08-15", 100.00, "FAILED"],
], columns=[
    "payment_id",
    "payment_date",
    "amount",
    "payment_status",
])


# ============================================================
# 4. SETTLEMENT RECORDS
#    Control 3 / 5
#
#    Includes:
#    - direct 1:1 settlement
#    - grouped settlement
# ============================================================

settlement_records = pd.DataFrame([
    # ========================================================
    # DISBURSEMENT - DIRECT
    # ========================================================

    ["S001", "T001", None, "2026-08-02", 1000.00,
     "DIRECT", "DISBURSEMENT"],

    ["S002", "T002", None, "2026-08-02", 2000.00,
     "DIRECT", "DISBURSEMENT"],

    # timing/date difference
    ["S003", "T003", None, "2026-08-04", 1500.00,
     "DIRECT", "DISBURSEMENT"],

    # amount difference
    ["S004", "T004", None, "2026-08-04", 700.00,
     "DIRECT", "DISBURSEMENT"],

    # ========================================================
    # DISBURSEMENT - GROUPED
    # ========================================================

    # Two transaction records will reconcile to one settlement group.
    ["S005", None, "G001", "2026-08-06", 1200.00,
     "GROUPED", "DISBURSEMENT"],

    ["S006", None, "G001", "2026-08-06", 800.00,
     "GROUPED", "DISBURSEMENT"],

    # ========================================================
    # REPAYMENT - DIRECT
    # ========================================================

    ["S007", "R001", None, "2026-08-11", 400.00,
     "DIRECT", "REPAYMENT"],

    ["S008", "R002", None, "2026-08-12", 500.00,
     "DIRECT", "REPAYMENT"],

    # date difference
    ["S009", "R003", None, "2026-08-13", 300.00,
     "DIRECT", "REPAYMENT"],

    # ========================================================
    # REPAYMENT - GROUPED
    # ========================================================

    ["S010", None, "G002", "2026-08-16", 600.00,
     "GROUPED", "REPAYMENT"],

    ["S011", None, "G002", "2026-08-16", 400.00,
     "GROUPED", "REPAYMENT"],
], columns=[
    "settlement_reference",
    "transaction_id",
    "settlement_group_id",
    "settlement_date",
    "amount",
    "settlement_type",
    "settlement_category",
])


# ============================================================
# 5. GROUPED TRANSACTIONS
#
#    These are intentionally linked to settlement_group_id.
#    They allow testing grouped / batch reconciliation.
# ============================================================

grouped_transaction_events = pd.DataFrame([
    ["G-T001", "2026-08-05", 700.00, "STATE_B", None, "G001"],
    ["G-T002", "2026-08-05", 500.00, "STATE_B", None, "G001"],

    ["G-R001", "2026-08-15", 350.00, "REPAYMENT", "P006", "G002"],
    ["G-R002", "2026-08-15", 250.00, "REPAYMENT", "P007", "G002"],
], columns=[
    "transaction_id",
    "event_date",
    "amount",
    "event_type",
    "payment_id",
    "settlement_group_id",
])


# Add grouped records to main transaction event table.
transaction_events = pd.concat(
    [transaction_events, grouped_transaction_events],
    ignore_index=True,
)


# ============================================================
# 6. KNOWN ISSUES
#
#    Synthetic mapping only.
#    Demonstrates how known exceptions can be mapped
#    without embedding production business rules.
# ============================================================

known_issues = pd.DataFrame([
    [
        "T004",
        "CONTROL_1",
        "KNOWN_AMOUNT_DIFFERENCE",
        "Synthetic known exception for demonstration",
    ],
    [
        "R003",
        "CONTROL_5",
        "KNOWN_TIMING_DIFFERENCE",
        "Synthetic known timing scenario",
    ],
], columns=[
    "recon_key",
    "recon_control",
    "issue_category",
    "issue_note",
])


# ============================================================
# 7. DATA QUALITY / DUPLICATE TEST DATA
#
#    Optional dataset specifically for testing DQ checks.
# ============================================================

dq_test_records = pd.DataFrame([
    ["DQ001", "2026-08-01", 100.00, "VALID"],
    ["DQ002", "2026-08-01", 200.00, "VALID"],

    # duplicate key
    ["DQ003", "2026-08-02", 300.00, "DUPLICATE"],
    ["DQ003", "2026-08-02", 300.00, "DUPLICATE"],

    # missing amount
    ["DQ004", "2026-08-03", None, "MISSING_AMOUNT"],

    # invalid date
    ["DQ005", "INVALID_DATE", 500.00, "INVALID_DATE"],
], columns=[
    "record_id",
    "event_date",
    "amount",
    "test_case",
])


# ============================================================
# 8. WRITE FILES
# ============================================================

datasets = {
    "source_transactions.csv": source_transactions,
    "transaction_events.csv": transaction_events,
    "payment_records.csv": payment_records,
    "settlement_records.csv": settlement_records,
    "known_issues.csv": known_issues,
    "dq_test_records.csv": dq_test_records,
}


for filename, df in datasets.items():
    output_path = OUTPUT_DIR / filename
    df.to_csv(output_path, index=False)
    print(f"Created: {output_path} ({len(df):,} rows)")


# ============================================================
# 9. SUMMARY
# ============================================================

print("\nSynthetic dataset generated successfully.")
print(f"Output directory: {OUTPUT_DIR.resolve()}")

print("\nFiles:")
for filename in datasets:
    print(f"  - {filename}")

print("\nIntended test scenarios:")
print("  ✓ Matched records")
print("  ✓ Missing records")
print("  ✓ Amount differences")
print("  ✓ Date differences")
print("  ✓ Timing differences")
print("  ✓ Known issue mapping")
print("  ✓ Direct settlement")
print("  ✓ Grouped settlement")
print("  ✓ Basic data-quality issues")
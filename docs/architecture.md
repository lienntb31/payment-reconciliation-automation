# Architecture

## 1. Architecture Overview

This project demonstrates a generic architecture for automated financial data reconciliation.

It is intentionally designed as a **synthetic reference architecture** rather than a representation of any specific company's internal infrastructure.

```text
┌──────────────────────────────────────┐
│          Independent Sources         │
│                                      │
│  Transaction Data / Payment Data /   │
│  Settlement Data / Reference Data    │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│         Python Preparation           │
│                                      │
│ Cleaning                             │
│ Standardization                      │
│ Validation                           │
│ File Processing                      │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│             SQL / Trino              │
│                                      │
│ Source Filtering                     │
│ Aggregation                          │
│ Reconciliation                       │
│ Data Quality Checks                  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Classification & RCA           │
│                                      │
│ Timing Differences                   │
│ Known Issues                         │
│ Unresolved Cases                     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│             Output Layer             │
│                                      │
│ DataFrames / CSV / Google Sheets     │
└──────────────────────────────────────┘
```

---

# 2. Design Boundary

The architecture deliberately abstracts away:

* internal service names
* internal system relationships
* production database schemas
* proprietary APIs
* infrastructure topology
* message queues
* internal storage locations
* production transaction identifiers
* confidential business rules

Only generic data-processing patterns are represented.

---

# 3. Generic Transaction Lifecycle

The project models a simplified financial transaction lifecycle:

```text
Source Event
     ↓
Transaction Processing
     ↓
Funding / Settlement Module
     ↓
Bank Statement (external record)
```

Two generic scenarios are represented.

### Payment / Disbursement Scenario

```text
Source Records
     ↓
Transaction Records
     ↓
Funding (Settlement) Records
     ↓
Bank Statement Records
```

### Repayment Scenario

```text
Payment Records
     ↓
Repayment Records
     ↓
Funding (Settlement) Records
     ↓
Bank Statement Records
```

The funding/settlement module sits between the internal transaction records and the
external bank statement. It is the bridge that carries a common reconciliation key
(direct, transaction-level or grouped, batch-level) and the latest status the bank
side has communicated back for that order.

These flows are conceptual only and are not intended to describe any specific production architecture.

---

# 4. Reconciliation Controls

Five controls are implemented. Controls 3 and 5 are each split into two stages,
because the funding/settlement module sits between the internal transaction record
and the external bank statement:

```text
Control 1
Source → Transaction State

Control 2
Transaction State A → Transaction State B

Control 3A
Transaction → Funding (Settlement) Module

Control 3B
Funding (Settlement) Module → Bank Statement

Control 4
Payment → Repayment

Control 5A
Repayment → Funding (Settlement) Module

Control 5B
Funding (Settlement) Module → Bank Statement
```

Each control validates a different transition or consistency relationship.

---

# 5. Standard Reconciliation Pattern

Every control follows the same high-level architecture.

```text
                    Source A
                       │
                       ▼
              Independent Filter
                       │
                       ▼
                Source A Pool
                       │
                       │
                       │ FULL OUTER JOIN
                       │
                       ▼
                Source B Pool
                       ▲
                       │
              Independent Filter
                       │
                    Source B
                       │
                       ▼
              Reconciliation Pool
                       │
                       ▼
              Discrepancy Detection
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Classification          RCA
              │                 │
              └────────┬────────┘
                       ▼
                Operational Output
```

---

# 6. Source Pool Construction

Each source is independently filtered.

Conceptually:

```text
Source A
  │
  └── date >= start_date
      date < end_date
          │
          ▼
     Source A Pool


Source B
  │
  └── date >= start_date
      date < end_date
          │
          ▼
     Source B Pool
```

The source-specific date fields are intentionally generic.

This allows the reconciliation to handle situations where independent systems record the same event using different reporting dates.

---

# 7. Reconciliation Grain

Before joining, each source must be represented at the correct business grain.

For transaction-level reconciliation:

```text
transaction_id
```

For grouped settlement data:

```text
settlement_reference
```

or another appropriate synthetic reconciliation key may be used.

The general rule is:

```text
Raw Source
    ↓
Determine Business Grain
    ↓
Aggregate if Necessary
    ↓
Reconcile
```

This prevents unintended many-to-many joins.

---

# 8. FULL OUTER JOIN

The reconciliation uses a `FULL OUTER JOIN` because records missing from either source must remain visible.

Example:

```text
Source A             Source B

A001                 A001
A002                 A003
A003
A004
```

Result:

```text
A001   matched
A002   Source B missing
A003   matched
A004   Source B missing
```

This allows the workflow to detect:

* missing source records
* amount differences
* date differences
* matched records

Matched records can subsequently be excluded from the operational discrepancy output.

---

# 9. Difference Calculation

For financial reconciliation, the synthetic implementation uses:

```text
diff = amount_a - amount_b
```

A simplified reconciliation record can therefore contain:

```text
recon_key
date_a
date_b
amount_a
amount_b
diff
```

Example:

```text
A001
2026-08-10
2026-08-10
1000
1000
0
```

versus:

```text
A002
2026-08-10
2026-08-11
1000
1000
0
```

The second example demonstrates why a date difference should not automatically be interpreted as a financial discrepancy.

---

# 10. Discrepancy Layer

The detailed output is created from the reconciliation pool.

```text
Reconciliation Pool
        │
        ▼
Discrepancy Filter
        │
        ├── Missing side
        ├── Amount mismatch
        └── Date mismatch
        │
        ▼
Discrepancy Dataset
```

The discrepancy dataset is the primary operational investigation output.

---

# 11. Timing Difference Mapping

Timing classification uses the complete reconciliation pool rather than only already-filtered discrepancy records.

Conceptually:

```sql
SELECT
    month,
    recon_key
FROM reconciliation_pool
GROUP BY
    month,
    recon_key
HAVING SUM(diff) = 0
```

This produces a mapping of reconciliation keys where financial differences net to zero within the relevant period.

The mapping can then be joined to the discrepancy output.

```text
Complete Reconciliation Pool
          │
          ├───────────────┐
          │               │
          ▼               ▼
 Discrepancy Output   Timing Mapping
          │               │
          └───────┬───────┘
                  ▼
            Classification
```

The specific classification methodology is synthetic and does not reproduce any proprietary production rule.

---

# 12. Known Issue Mapping

Known operational exceptions can be maintained separately from the reconciliation logic.

```text
                 Discrepancy
                      │
                      ▼
              Known Issue Mapping
                      │
              ┌───────┴───────┐
              ▼               ▼
          Known Issue       Unknown
              │               │
              ▼               ▼
          Annotate       Investigation
                              Queue
```

This design prevents operational explanations from being hard-coded into core reconciliation SQL.

---

# 13. RCA Workflow

The reconciliation system provides an investigation starting point rather than automatically resolving every issue.

```text
Automated Control
       ↓
Discrepancy
       ↓
Classification
       │
       ├── Timing
       │
       ├── Known Issue
       │
       └── Unresolved
                ↓
          Investigation Queue
                ↓
       Business / Data Investigation
                ↓
             Root Cause
                ↓
            Resolution
```

This creates a feedback loop between automated data quality monitoring and operational teams.

---

# 14. Python Architecture

Python provides the preparation and orchestration layer.

```text
src/
│
├── config.py
├── utils.py
├── bank_a.py
├── bank_b.py
├── ingestion.py
├── export.py
├── trino_client.py
└── gsheet_client.py
```

### `utils.py`

Common utilities for:

* file discovery
* header detection
* type conversion
* standardization

### Source processing modules

Source-specific modules handle:

* file parsing
* field normalization
* transaction categorization

The source examples in this repository are synthetic.

### `trino_client.py`

Responsible for:

* creating a Trino connection
* executing SQL
* returning query results

### `gsheet_client.py`

Responsible for:

* Google authentication
* worksheet access
* publishing DataFrames

### Orchestrator

The daily script coordinates:

```text
Configuration
      ↓
SQL Loading
      ↓
Date Parameterization
      ↓
Query Execution
      ↓
Output Validation
      ↓
Publication
```

---

# 15. SQL Architecture

SQL contains the reconciliation and data-quality logic.

```text
sql/
│
├── recon_01/
├── recon_02/
├── recon_03/
├── recon_04/
└── recon_05/
```

The separation follows:

```text
Python
    = orchestration + source preparation

SQL
    = transformation + reconciliation + controls

Google Sheets
    = operational consumption
```

This keeps reconciliation logic explicit and independently executable.

---

# 16. Output Architecture

Each control produces a small set of outputs.

```text
Control 1
├── Source Daily Summary
├── Transaction Daily Summary
└── Discrepancy / RCA

Control 2
├── Transaction Daily Summary
└── Discrepancy / RCA

Control 3A (Transaction -> Funding)
├── Funding Daily Summary
└── Discrepancy / RCA

Control 3B (Funding -> Bank Statement)
├── Bank Statement Daily Summary
└── Discrepancy / RCA

Control 4
├── Payment Daily Summary
├── Repayment Daily Summary
└── Discrepancy / RCA

Control 5A (Repayment -> Funding)
├── Funding Daily Summary
└── Discrepancy / RCA

Control 5B (Funding -> Bank Statement)
├── Bank Statement Daily Summary
└── Discrepancy / RCA
```

The exact names and structures are synthetic.

---

# 17. Automation Architecture

The complete workflow can run on a recurring schedule.

```text
┌────────────────────────┐
│   Daily Scheduler      │
│ Windows Task Scheduler │
│       / Cron           │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Python Orchestrator    │
└───────────┬────────────┘
            │
            ├───────────────┐
            ▼               ▼
       Configuration     SQL Templates
            │               │
            └───────┬───────┘
                    ▼
             Trino Execution
                    │
                    ▼
             Result DataFrames
                    │
                    ▼
              Output Validation
                    │
                    ▼
             Google Sheets API
                    │
                    ▼
             Operational Reports
```

---

# 18. Security & Confidentiality Boundary

The public architecture deliberately stops at the level of generic data-processing components.

```text
PUBLIC
────────────────────────────────
Generic source data
Generic transaction records
Generic settlement records
Synthetic SQL
Synthetic sample data
Generic reconciliation logic
Generic automation architecture


NOT PUBLIC
────────────────────────────────
Production data
Internal system names
Internal service topology
Production schemas
Production table names
Production API endpoints
Credentials
Tokens
Infrastructure details
Internal transaction rules
Confidential business logic
```

The purpose is to demonstrate engineering capability without exposing information that could identify or reconstruct a production environment.

---

# 19. Architectural Principles

### Separation of concerns

```text
Preparation
    ≠
Reconciliation
    ≠
Classification
    ≠
Reporting
```

### Source independence

Each source is prepared and validated independently before reconciliation.

### Correct business grain

The reconciliation key must represent the actual comparison grain of the data.

### Exception-focused output

Matched records are useful for validation but should not dominate operational investigation outputs.

### Explainability

Every discrepancy should have enough information for a human investigator to understand what was compared.

### Automation

Repeatable reconciliation and reporting steps should be executable without manual data preparation.

### Security by abstraction

Public documentation should communicate the engineering pattern without reproducing production architecture.

---

# 20. Summary

The architecture combines:

```text
Source Preparation
       ↓
Independent Source Validation
       ↓
Correct-Grain Reconciliation
       ↓
FULL OUTER JOIN
       ↓
Discrepancy Detection
       ↓
Timing / Known-Issue Classification
       ↓
RCA Queue
       ↓
Automated Reporting
       ↓
Scheduled Execution
```

The result is a lightweight, repeatable framework for **financial reconciliation, data quality monitoring, and operational exception management**.

This repository intentionally demonstrates the **methodology and engineering design**, not the implementation details of any specific production environment.

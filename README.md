# Payment Reconciliation Automation

> An automated reconciliation workflow designed to reduce manual operational effort, improve data quality, and make high-volume financial transaction reconciliation more scalable.

---

## Overview

As transaction volume increased, the Payment Operations team relied heavily on manual Excel-based reconciliation workflows. Large datasets had to be split across multiple files and processed manually, creating operational bottlenecks, increasing the risk of errors, and making the process difficult to scale.

I designed and implemented an automated reconciliation workflow combining **Python, SQL, distributed data processing, workflow orchestration, Google Apps Script, and cloud object storage** to streamline the end-to-end process.

The solution reduced reconciliation processing effort by **more than 50%**, improved data accuracy, and enabled the operations team to move from a highly manual workflow toward a more scalable data-processing and automation model.

> **Confidentiality notice**
>
> This repository is an independent synthetic reconstruction inspired by the original workflow. No proprietary company code, SQL, production datasets, internal system names, schemas, credentials, API endpoints, infrastructure details, or confidential business logic are included.

---

# Business Problem

The original reconciliation workflow had several limitations:

* Large transaction datasets were manually processed across multiple Excel files.
* Reconciliation consumed more than half a workday and could take significantly longer when data or system issues occurred.
* Manual processing increased the risk of operational errors.
* The process became increasingly difficult to scale with transaction volume.
* Investigating discrepancies required substantial manual effort.
* Different data sources and processing stages made it difficult to identify the root cause of a variance efficiently.

The objective was therefore not simply to automate Excel processing, but to redesign the workflow into a **repeatable financial data control process**.

---

# Before → After

### Before

```text
Large Transaction Files
        ↓
Manual Excel Processing
        ↓
Manual Reconciliation
        ↓
Manual Variance Checking
        ↓
Manual Investigation
        ↓
Operational Reporting
```

### After

```text
Source Data
     ↓
Automated Ingestion
     ↓
Python Data Preparation
     ↓
SQL Transformation
     ↓
Automated Reconciliation
     ↓
Data Quality & Variance Analysis
     ↓
RCA / Investigation Queue
     ↓
Operational Reporting
```

The key transformation was moving the workflow from **manual file manipulation** toward a **data-driven reconciliation pipeline**.

---

# Solution

The solution was designed as a hybrid data-processing pipeline.

```text
                    Source Data
                        │
                        ▼
                 Data Ingestion
                        │
                        ▼
              Python Preparation
             Cleaning / Validation
                        │
                        ▼
                SQL Processing
          Transformation / Reconciliation
                        │
                        ▼
          Distributed Data Processing
             Flink / Kafka / Spark
                        │
                        ▼
             Workflow Orchestration
                        │
                        ▼
             Cloud Object Storage
                        │
                        ▼
          Reconciliation & DQ Outputs
                        │
                        ▼
              Payment Operations
```

Different technologies were used for different responsibilities rather than forcing the entire workflow into a single tool.

---

# Reconciliation Framework

The reconciliation layer is structured around multiple control points across the generic financial transaction lifecycle. Controls 3 and 5 are each split into two stages, since a funding/settlement module sits between the internal transaction record and the external bank statement and is used as the key bridge between the two.

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

Each control follows a common analytical pattern:

```text
Source A
   │
   ▼
Independent Filtering
   │
   ▼
Source A Pool ───────┐
                     │
                     │ FULL OUTER JOIN
                     │
Source B Pool ───────┘
   │
   ▼
Reconciliation Pool
   │
   ▼
Discrepancy Detection
   │
   ├── Amount Difference
   ├── Date Difference
   ├── Missing Record
   └── Other Data Quality Issues
   │
   ▼
Classification / RCA
   │
   ▼
Operational Output
```

The public implementation uses synthetic data and generic business entities. The actual production architecture is intentionally not reproduced.

---

# Technical Approach

## 1. Data Preparation

Python is used for source preparation and workflow automation.

Key responsibilities include:

* Input file discovery and processing
* Header and schema normalization
* Data type conversion
* Date and numeric standardization
* Basic validation
* Transaction categorization
* Preparing datasets for downstream processing

The preparation layer is designed to make heterogeneous source files suitable for consistent downstream reconciliation.

---

## 2. SQL-Based Reconciliation

SQL is used as the core analytical layer.

Responsibilities include:

* Source-level filtering
* Data transformation
* Aggregation
* Joining independent data sources
* Reconciliation
* Variance calculation
* Data quality checks
* Generating operational outputs

A simplified reconciliation pattern is:

```sql
SELECT
    COALESCE(a.recon_key, b.recon_key) AS recon_key,
    a.amount AS amount_a,
    b.amount AS amount_b,
    COALESCE(a.amount, 0)
        - COALESCE(b.amount, 0) AS diff
FROM source_a a
FULL OUTER JOIN source_b b
    ON a.recon_key = b.recon_key
```

A `FULL OUTER JOIN` is important because the reconciliation needs to identify records that exist on only one side, not just records that successfully match.

---

## 3. Reconciliation at the Correct Grain

A key design consideration is choosing the correct reconciliation grain.

Depending on the dataset, reconciliation may occur at:

```text
Transaction level
        or
Grouped / settlement level
```

Source data is therefore aggregated where necessary before reconciliation to avoid unintended many-to-many joins and inflated amounts.

This is particularly important when one financial event can correspond to multiple source records or when settlement data is represented at a different level of granularity.

---

## 4. Discrepancy Detection

The detailed reconciliation output focuses on records requiring investigation.

Typical discrepancy categories include:

```text
Matched
   │
   ├── Amount mismatch
   ├── Date mismatch
   ├── Missing from Source A
   ├── Missing from Source B
   ├── Duplicate / aggregation issue
   └── Other data quality issue
```

Instead of returning the entire transaction population to Operations, the workflow produces a **discrepancy-focused investigation dataset**.

---

## 5. Timing Difference Analysis

A date difference does not necessarily represent a financial mismatch.

Transactions can cross reporting periods or be reflected at different stages of processing.

The workflow therefore separates potential timing differences from actual financial variances by analyzing the reconciliation relationship across the relevant period.

Conceptually:

```text
Reconciliation Pool
        │
        ├── Financial Difference
        │
        └── Net-zero / Timing Relationship
                    │
                    ▼
             Classification
```

The synthetic implementation demonstrates this concept without reproducing proprietary production classification rules.

---

## 6. Data Quality & Root Cause Analysis

A major part of the workflow is moving beyond:

> "These two datasets do not match."

toward:

> "Why do they not match, and what should happen next?"

The analytical workflow therefore separates:

```text
Data Quality Issue
        ↓
Transformation / Processing Issue
        ↓
Reconciliation Variance
        ↓
Known Operational Exception
        ↓
Root Cause Investigation
        ↓
Resolution
```

Known issues can be mapped to discrepancy records so that already-understood exceptions do not repeatedly require manual investigation.

Unresolved discrepancies remain in an investigation queue for collaboration between Operations, Finance, Data, and Engineering teams.

---

# Distributed Data Processing

For larger-scale transaction processing, the original workflow integrated with distributed technologies including:

* **Apache Flink**
* **Apache Kafka**
* **Apache Spark**

These technologies support processing volumes beyond what is practical with spreadsheet-based workflows.

The portfolio reconstruction does not reproduce the production streaming architecture. Instead, it demonstrates the analytical and reconciliation patterns using synthetic data and a simplified processing environment.

---

# Workflow Automation

The workflow was designed to minimize repetitive operational work.

```text
Scheduled Trigger
       ↓
Python Orchestrator
       ↓
Prepare / Process Data
       ↓
Execute SQL
       ↓
Validate Results
       ↓
Publish Outputs
       ↓
Operational Consumption
```

Automation components include:

* Python workflow orchestration
* Google Apps Script
* Cloud object storage
* Scheduled execution
* Automated output generation

The objective was to make reconciliation **repeatable, observable, and less dependent on manual file handling**.

---

# Operational Output

The workflow produces outputs at two levels.

### Summary

Used to monitor the overall reconciliation status:

```text
Source-level totals
Transaction-level totals
Funding (settlement) module totals
Bank statement totals
```

### Detailed

Used for investigation:

```text
Discrepancy records
Difference amounts
Date differences
Classification
Known-issue mapping
RCA / investigation information
```

This separation allows Operations to quickly monitor reconciliation health while still having access to detailed records when investigation is required.

---

# Business Impact

The automation delivered measurable operational improvements:

| Area                             | Impact                                           |
| -------------------------------- | ------------------------------------------------ |
| Reconciliation processing effort | **Reduced by >50%**                              |
| Manual Excel processing          | Significantly reduced                            |
| Data accuracy                    | Improved                                         |
| Scalability                      | Improved for increasing transaction volume       |
| Investigation workflow           | More structured and repeatable                   |
| Operational adoption             | Supported through training and hands-on guidance |

The project also included workshops and on-the-job support to help the Payment Operations team adopt the new workflow and automation techniques.

The most important impact was the shift from **manual reconciliation execution** toward a more standardized and scalable financial data control process.

---

# My Role

I was responsible for the **end-to-end design and implementation** of the reconciliation automation.

My responsibilities included:

* Identifying bottlenecks in the existing operational workflow
* Translating business requirements into technical solutions
* Designing the reconciliation framework
* Developing Python-based data processing components
* Developing SQL-based reconciliation logic
* Designing data quality and discrepancy checks
* Working with distributed data-processing technologies
* Automating repetitive operational tasks
* Investigating reconciliation variances and supporting RCA
* Collaborating with Payment Operations and technical teams
* Designing outputs for operational consumption
* Training and supporting end users during adoption

The project required a combination of:

**Business understanding + SQL + Python + data quality + automation + distributed data processing + cross-functional problem solving**

---

# Engineering Decisions

Several design decisions were important to the solution.

### SQL as the reconciliation layer

Reconciliation logic was kept close to the data-processing layer rather than relying on manual spreadsheet formulas.

### Python for preparation and orchestration

Python handled tasks better suited to procedural automation, file processing, validation, and workflow coordination.

### Correct reconciliation grain

Sources were normalized or aggregated before joining when necessary to prevent incorrect many-to-many reconciliation.

### Discrepancy-focused outputs

Operational users received exceptions requiring attention rather than having to manually inspect the entire transaction population.

### Separation of detection and RCA

The automated workflow identifies and structures discrepancies, while unresolved business or technical causes can be investigated by the appropriate teams.

### Automation over manual execution

Repeatable processing steps were converted into scheduled workflows to reduce operational dependency on manual execution.

---

# Technology Stack

### Data & Analytics

* SQL
* Python
* pandas
* Data validation
* Financial reconciliation
* Root cause analysis

### Distributed Data Processing

* Apache Flink
* Apache Kafka
* Apache Spark

### Automation & Integration

* Google Apps Script
* Workflow orchestration
* Cloud object storage
* Scheduled execution

### Portfolio Reconstruction

* Python
* SQL
* Trino
* pandas
* Google Sheets API
* Synthetic datasets

---

# Portfolio Version

Because the original implementation involves proprietary systems and confidential company information, this repository does **not** reproduce the production implementation.

Instead, the public version reconstructs the core engineering concepts using synthetic data:

```text
Synthetic Source Data
        ↓
Python Preparation
        ↓
SQL / Trino
        ↓
Reconciliation Controls
        ↓
Data Quality Checks
        ↓
Variance Classification
        ↓
RCA Support
        ↓
Operational Reporting
        ↓
Scheduled Automation
```

The public implementation intentionally abstracts away:

* Internal system names
* Production database schemas
* Production table names
* Internal service relationships
* API endpoints
* Infrastructure topology
* Production transaction identifiers
* Confidential business rules
* Production data

The purpose is to demonstrate the **engineering methodology, analytical reasoning, and automation approach** without exposing confidential information.

---

# Key Takeaways

This project demonstrates how a manually intensive financial operations process can be transformed into a scalable data and automation workflow.

The key contribution was not simply automating Excel processing.

It was designing a repeatable control framework around:

```text
Reliable Data
      ↓
Automated Processing
      ↓
Transparent Reconciliation
      ↓
Data Quality Controls
      ↓
Actionable Discrepancy Analysis
      ↓
Operational Resolution
```

The result is a workflow that combines **financial data analysis, data engineering, automation, data quality, and business operations** into a single practical solution.

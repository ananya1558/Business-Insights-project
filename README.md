# Business Insights 360 - AtliQ Hardware (Version 2.0)

[![Power BI](https://img.shields.io/badge/Power_BI-Desktop_%26_Service-F2C811?logo=powerbi&logoColor=black)](#)
[![MySQL](https://img.shields.io/badge/Database-MySQL_8.0-4479A1?logo=mysql&logoColor=white)](#)
[![DAX](https://img.shields.io/badge/Calculations-DAX-0078D4)](#)
[![Excel](https://img.shields.io/badge/Data_Feeds-MS_Excel-217346?logo=microsoftexcel&logoColor=white)](#)

> **End-to-End Enterprise BI Solution** designed for **AtliQ Hardware** to monitor, evaluate, and optimize performance across **Finance, Sales, Marketing, Supply Chain**, and **Executive Leadership**.

---

## 📌 Executive Summary

AtliQ Hardware is a rapidly growing global manufacturer and retailer of consumer computer hardware, peripherals, and storage solutions. Historically, key regional business decisions were made using ad-hoc Excel spreadsheets, leading to data silos, delayed reporting, and substantial losses—such as opening an under-performing store in Latin America based on intuition rather than actionable data.

To overcome these operational challenges, AtliQ's senior leadership initiated the **Business Insights 360** initiative:
1. **Centralize Data Pipeline:** Migrate disparate operational records from MySQL databases and Excel workbooks into an optimized Power BI data warehouse.
2. **Deliver 360-Degree Views:** Equip departmental stakeholders with targeted, role-based dashboards.
3. **Iterative Stakeholder Enhancements (v2.0):** Implement dynamic benchmarking (Targets vs. Last Year), user-driven margin variance slicers, marketing view toggle switches, and an executive command center.

---

## 🚀 What's New in Version 2.0

Following the initial deployment (v1.0), feedback from key department heads was incorporated to release **Version 2.0**:

| Feature / Enhancement | Requester | Implementation Details |
|---|---|---|
| **Dynamic Benchmarking (Targets vs. LY)** | *Nick Puri (Finance) & Thor Hathodawla* | Dynamic DAX toggle allowing users to switch P&L visuals and KPI cards between annual budgeted Targets (`targets.xlsx`) and Last Year (LY) benchmarks. |
| **Dynamic GM % Tolerance Slicer** | *Bruce Haryali (Sales)* | Interactive numeric parameter slider (-20% to +20%) enabling sales reps to dynamically filter the Performance Matrix for entities failing margin thresholds. |
| **Marketing View Visual Switcher** | *Natasha Rao (Marketing)* | Dual-state toggle button utilizing Power BI Bookmarks to switch the Performance Matrix between **GM %** and **Net Profit %** without page duplicates. |
| **Executive View Dashboard** | *C-Level Management* | Brand new C-suite dashboard featuring Market Share trends (AtliQ vs. Dell, HP, Lenovo, Sony), Division/Channel revenue splits, and Sub-zone performance. |
| **Quick Fixes & Governance** | *Tchalla Tiwari (Supply Chain)* | Standardized all currency figures to **USD Millions ($M)**, added dynamic last-refreshed timestamps, and hardened forecast accuracy formulas against zero-division errors. |

---

## 🏗️ Architecture & Data Modeling

The solution utilizes a high-performance **Snowflake Schema** optimized for large transaction volumes across multiple fiscal cycles (FY 2018 - FY 2022).

```
                            +--------------------+
                            |    dim_customer    |
                            +--------------------+
                                      | 1
                                      |
                                      | *
+--------------------+      +--------------------+      +--------------------+
|    dim_market      | 1--* | fact_sales_monthly | *--1 |    dim_product     |
+--------------------+      +--------------------+      +--------------------+
                                      | *                         | 1
                                      |                           |
                                      | 1                         | *
                            +--------------------+      +--------------------+
                            |      dim_date      |      |   fact_gross_price |
                            +--------------------+      +--------------------+
                                      |
         +----------------------------+----------------------------+
         | 1                          | 1                          | 1
         | *                          | *                          | *
+--------------------+      +--------------------+      +--------------------+
| fact_forecast_mthly|      |    targets.xlsx    |      | marketshare-v2022  |
+--------------------+      +--------------------+      +--------------------+
```

### Integrated Data Sources
- **`gdb041` (MySQL Core):** `dim_customer`, `dim_market`, `dim_product`, `fact_sales_monthly`, `fact_forecast_monthly`.
- **`gdb056` (MySQL Financials):** `fact_gross_price`, `fact_manufacturing_cost`, `fact_pre_invoice_deductions`, `fact_post_invoice_deductions`, `fact_freight_cost`.
- **Excel External Feeds:** `targets.xlsx` (annual financial targets), `operating-expenses-table.xlsx` (operational expenditure rates), `marketshare-v2022.xlsx` (competitor intelligence).

---

## 📊 Dashboard Views (360° Overview)

### 1. Finance View
* **Dynamic P&L Statement:** Waterfall from Gross Sales down to Net Profit (`Gross Sales -> Pre-Invoice -> Net Invoice Sales -> Post-Invoice -> Net Sales -> COGS -> Gross Margin -> OpEx -> Net Profit`).
* **KPI Header:** Net Sales, Gross Margin %, and Net Profit % with dynamic variance indicators against Target / Last Year.
* **Trend Analysis:** Monthly Net Sales performance overlaid with historical and target trajectories.
* **Top/Bottom Performers:** Instant ranking of top and bottom products and customers by Net Sales.

### 2. Sales View
* **Unit Economics Analysis:** Complete visibility into promotional deductions, contractual allowances, and manufacturing/freight cost burdens.
* **Customer & Product Performance:** Tabular drilldowns across Net Sales, Gross Margin, and GM %.
* **Dynamic GM % Tolerance Filter:** User-driven slicer highlighting underperforming accounts.
* **Customer Sales Trend Tooltip:** Rich hover tooltip displaying customer-specific historical trend and margin trajectory.

### 3. Marketing View
* **Unit Economics & OpEx Breakdown:** Deduction of operational expenses (Ads, Promotions, Logistics) to track True Product Net Profit.
* **Dynamic Performance Matrix:** Switchable visual toggling between **Net Sales vs. GM %** and **Net Sales vs. NP %**.
* **Segment & Category Matrix:** Quadrant analysis identifying high-volume/high-margin driver products.

### 4. Supply Chain View
* **Core KPIs:** Forecast Accuracy %, Net Error, Absolute Error, and YoY Accuracy Variance.
* **Inventory Risk Matrix:** Dynamic categorization into **Out of Stock** (Net Error < 0) and **Excess Inventory** (Net Error > 0).
* **Accuracy vs. Net Error Trend:** Monthly tracking to prevent supply bottlenecks and overstocking carrying costs.

### 5. Executive View
* **Macro Command Center:** C-suite summary tailored for CEO, CFO, and COO review.
* **Market Share Analysis:** Year-over-Year market share comparisons between AtliQ and top industry competitors.
* **Revenue Bifurcations:** Division-wise (Peripherals, PC, Storage, Networking) and Channel-wise (Retailer, Direct, Distributor).
* **Sub-Zone Insights:** Geographic contribution percentages across APAC, EU, NA, and LATAM.

---

## 💻 SQL Analytical Modules (MySQL 8.0+)

The repository contains production-ready, optimized SQL scripts equipped with deterministic functions, stored procedures, window functions, and real-time triggers:

1. **[`project business/Sql Insights-1 Advance Finance Analysis..sql`](./project%20business/Sql%20Insights-1%20Advance%20Finance%20Analysis..sql)**
   - Deterministic fiscal calendar functions (`get_fiscal_year`, `get_fiscal_quarter`).
   - Customer gross sales aggregation reports (Croma India case study).
   - Stored procedures: `get_monthly_gross_sales_for_customer`, `get_market_badge` (Gold/Silver classification compliant with MySQL `ONLY_FULL_GROUP_BY`).

2. **[`project business/Sql Insights-2 Advance Top Performer Analysis..sql`](./project%20business/Sql%20Insights-2%20Advance%20Top%20Performer%20Analysis..sql)**
   - Scalable P&L data views: `pre_invoice_sales`, `post_invoice_sales`, `net_sales`.
   - Chained CTEs (fixed MySQL 8 nested CTE syntax) for Top N markets, customers, and products.
   - Window functions (`DENSE_RANK()`, `SUM() OVER ()`) for regional contribution percentages and division-level rankings.

3. **[`project business/Sql Insights-3 Advance Supply Chain Analysis..sql`](./project%20business/Sql%20Insights-3%20Advance%20Supply%20Chain%20%20Analysis..sql)**
   - Automated real-time pipeline triggers (`fact_sales_monthly_after_insert`, `fact_forecast_monthly_after_insert`) updated to modern `NEW.<col>` syntax.
   - Stored procedure `get_forecast_accuracy_report` calculating Net Error, Absolute Error, Forecast Accuracy %, and Inventory Risk flags.
   - Year-over-Year forecast accuracy variance auditing (FY 2020 vs. FY 2021/2022).

---

## 📐 DAX Master Reference

For the comprehensive list of 50+ DAX measures, table formulas, and dynamic toggle logic, consult the companion guide:
📖 **[DAX Measures & Data Model v2.0 Guide](./project%20business/DAX_Measures_and_Data_Model_v2.md)**

---

## 📈 Key Business Learnings & ROI

1. **Gross Margin vs. Net Profit Governance:** Sales teams should be incentivized on Gross Margin rather than Net Profit, as operating and promotional overheads are outside their direct control.
2. **Forecast Accuracy Impact:** Even a **1% improvement** in forecast accuracy saves millions in inventory carrying costs and prevents revenue loss from stock-outs.
3. **Iterative Stakeholder Feedback:** Implementing dynamic benchmarks and user-driven slicers transformed passive dashboard viewers into active data investigators.

---

## 📂 Repository Structure

```
Business-Insights-Project/
├── README.md                             # Root Project Documentation (v2.0)
└── project business/
    ├── DataSet/
    │   ├── gdb041.sql.gz                 # MySQL database dump (core tables)
    │   ├── marketshare-v2022.xlsx / .csv # Competitor market share benchmark
    │   ├── operating-expenses-table.xlsx / .csv # Operational expenditure rates
    │   ├── targets.xlsx / .csv           # Budgeted financial targets
    │   ├── p-l-structure.csv             # Profit and loss line item order
    │   └── atliq-data-catalog.csv        # Database server and table catalog
    ├── Stakeholders_Implementation/      # Stakeholder requirements & mockups
    │   ├── adding-dynamic-slicer-to-filter-visual.pptx
    │   ├── create-a-toggle-button-to-switch-between-visuals.pptx
    │   ├── create-an-executive-view.pptx
    │   ├── practice-exercise-implementing-dynamic-benchmark.pptx
    │   └── practice-exercise-quick-fixes.pptx
    ├── DAX_Measures_and_Data_Model_v2.md # Complete DAX dictionary & modeling guide
    ├── Mock-up Dashboard.pdf             # Initial dashboard wireframes
    ├── README.md                         # Project documentation (v2.0)
    ├── Sql Insights-1 Advance Finance Analysis..sql
    ├── Sql Insights-2 Advance Top Performer Analysis..sql
    └── Sql Insights-3 Advance Supply Chain  Analysis..sql
```

# Business Insights 360 - Version 2.0 Implementation Guide & DAX Master Reference

This document outlines the complete technical specifications, data modeling schema, and production-grade DAX measures implemented in **Version 2.0** of the **Business Insights 360** Power BI solution for **AtliQ Hardware**, incorporating all post-stakeholder review enhancements.

---

## 1. Architecture & Data Model (Snowflake Schema)

The reporting data model is built using an optimized **Snowflake Schema** connecting transactional MySQL tables with operational Excel feeds:

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

### Table Dictionary
| Table Name | Source | Description |
|---|---|---|
| `fact_sales_monthly` | MySQL (`gdb041`) | Actual sold quantity aggregated monthly by customer and product |
| `fact_forecast_monthly` | MySQL (`gdb041`) | Demand forecasting quantities by customer and product |
| `fact_gross_price` | MySQL (`gdb056`) | Standard gross price per product per fiscal year |
| `fact_manufacturing_cost`| MySQL (`gdb056`) | Production cost per product code per fiscal year |
| `fact_pre_invoice_deductions` | MySQL (`gdb056`) | Contractual pre-invoice discount percentages by customer/year |
| `fact_post_invoice_deductions`| MySQL (`gdb056`) | Promotional rebates and placement fees by customer/product/month |
| `fact_freight_cost` | MySQL (`gdb056`) | Freight and logistics percentage rates per market/fiscal year |
| `targets` | Excel (`targets.xlsx`) | Annual benchmark targets for Net Sales and Gross Margin % |
| `marketshare` | Excel (`marketshare-v2022.xlsx`) | Competitor and AtliQ market shares across operational regions |
| `dim_customer` | MySQL (`gdb041`) | Customer hierarchy (Customer, Channel, Market, Region) |
| `dim_product` | MySQL (`gdb041`) | Product catalog (Division, Segment, Category, Product, Variant) |
| `dim_market` | MySQL (`gdb041`) | Geographic market metadata and sub-zones |
| `dim_date` | Power Query Generated | Calendar dates, AtliQ Fiscal Year, Fiscal Quarter, Fiscal Month |

---

## 2. Version 2.0 Stakeholder Enhancements Implemented

### A. Dynamic Benchmark Switching (Targets vs. Last Year)
- **Problem**: Management previously had static YoY comparisons. They needed the ability to evaluate actual performance against either **Targets** or **Last Year (LY)** dynamically.
- **Solution**:
  - Ingested `targets.xlsx` and linked on `Market`, `Customer`, and `Fiscal Year`.
  - Created disconnected table `Benchmark Selector` with values `["Target", "Last Year"]`.
  - Implemented dynamic DAX measures that evaluate the selected slicer value and adjust KPI cards, variance bars, and P&L waterfalls on the fly.

### B. Dynamic GM % Tolerance Slicer
- **Problem**: The sales team needed to instantly identify customers and markets whose Gross Margin fell outside an acceptable variance threshold from the target.
- **Solution**:
  - Created a numeric range parameter `GM % Tolerance Slicer` (-20% to +20%, step 1%).
  - Built filtering DAX measure `[GM % Variance Filter Flag]` set to return `1` or `0`.
  - Applied the flag to visual-level filters, enabling interactive threshold auditing.

### C. Marketing View Visual Toggle Button
- **Problem**: Product managers needed to toggle the scatter/bubble matrix between **Net Sales vs. GM %** and **Net Sales vs. Net Profit %** without cluttering the screen with duplicate pages.
- **Solution**:
  - Implemented Power BI Bookmarks paired with a dual-state button for seamless in-place visual toggling.

### D. Dedicated Executive View
- **Problem**: C-level executives (CEO, CFO, CMO) required a high-level command center with macro metrics.
- **Solution**:
  - Market Share Trend (AtliQ vs. Competitors like Sony, Dell, HP, Logitech).
  - Revenue by Division (Peripherals, PC, Storage, Networking) & Channel (Retailer, Direct, Distributor).
  - Top 5 Products and Top 5 Customers by Revenue with contribution percentages.
  - Sub-zone revenue contribution waterfall.

### E. Quick-Fix Enhancements
- Standardized all monetary figures in **USD Millions ($M)** with two-decimal precision.
- Added dynamic **Last Refresh Date & Timestamp** header visual.
- Resolved Supply Chain forecast formula edge cases (`DIVIDE` protection against zero forecast).

---

## 3. Production DAX Measures Reference

### 3.1 Base Revenue & Volume Measures
```dax
-- Total Sold Quantity
Total Quantity = 
SUM(fact_sales_monthly[sold_quantity])

-- Total Forecast Quantity
Total Forecast Quantity = 
SUM(fact_forecast_monthly[forecast_quantity])

-- Gross Sales Amount
Gross Sales = 
SUMX(
    fact_sales_monthly,
    fact_sales_monthly[sold_quantity] * RELATED(fact_gross_price[gross_price])
)

-- Pre-Invoice Deductions Amount
Pre-Invoice Deductions = 
SUMX(
    fact_sales_monthly,
    fact_sales_monthly[sold_quantity] * 
    RELATED(fact_gross_price[gross_price]) * 
    RELATED(fact_pre_invoice_deductions[pre_invoice_discount_pct])
)

-- Net Invoice Sales
Net Invoice Sales = 
[Gross Sales] - [Pre-Invoice Deductions]

-- Post-Invoice Deductions Amount
Post-Invoice Deductions = 
SUMX(
    fact_sales_monthly,
    [Net Invoice Sales] * 
    RELATED(fact_post_invoice_deductions[post_invoice_discount_pct])
)

-- Net Sales
Net Sales = 
[Net Invoice Sales] - [Post-Invoice Deductions]
```

### 3.2 Cost of Goods Sold & Profitability Measures
```dax
-- Manufacturing Cost
Manufacturing Cost = 
SUMX(
    fact_sales_monthly,
    fact_sales_monthly[sold_quantity] * RELATED(fact_manufacturing_cost[manufacturing_cost])
)

-- Freight & Other Cost
Freight Cost = 
SUMX(
    fact_sales_monthly,
    [Net Sales] * RELATED(fact_freight_cost[freight_pct])
)

-- Total COGS
COGS = 
[Manufacturing Cost] + [Freight Cost]

-- Gross Margin (GM)
Gross Margin = 
[Net Sales] - [COGS]

-- Gross Margin % (GM %)
Gross Margin % = 
DIVIDE([Gross Margin], [Net Sales], 0)

-- Operational Expenses (Ads & Promotion, Overhead)
Operational Expenses = 
SUMX(
    fact_sales_monthly,
    [Net Sales] * RELATED(operating_expenses[op_cost_pct])
)

-- Net Profit (NP)
Net Profit = 
[Gross Margin] - [Operational Expenses]

-- Net Profit % (NP %)
Net Profit % = 
DIVIDE([Net Profit], [Net Sales], 0)
```

### 3.3 Dynamic Benchmark Measures (Targets vs. LY)
```dax
-- Selected Benchmark Slicer Capture
Selected Benchmark = 
SELECTEDVALUE('Benchmark Selector'[Benchmark], "Target")

-- Net Sales - Last Year (LY)
Net Sales LY = 
CALCULATE(
    [Net Sales],
    SAMEPERIODLASTYEAR(dim_date[date])
)

-- Net Sales - Target
Net Sales Target = 
SUM(targets[ns_target])

-- Dynamic Benchmark Net Sales
BM Net Sales = 
IF(
    [Selected Benchmark] = "Target",
    [Net Sales Target],
    [Net Sales LY]
)

-- Net Sales Variance to Benchmark
Net Sales Variance = 
[Net Sales] - [BM Net Sales]

-- Net Sales Variance %
Net Sales Variance % = 
DIVIDE([Net Sales Variance], [BM Net Sales], 0)

-- Gross Margin % - Last Year
GM % LY = 
CALCULATE(
    [Gross Margin %],
    SAMEPERIODLASTYEAR(dim_date[date])
)

-- Gross Margin % - Target
GM % Target = 
AVERAGE(targets[gm_target_pct])

-- Dynamic Benchmark GM %
BM GM % = 
IF(
    [Selected Benchmark] = "Target",
    [GM % Target],
    [GM % LY]
)

-- GM % Variance to Benchmark
GM % Variance = 
[Gross Margin %] - [BM GM %]
```

### 3.4 Dynamic Slicer Filtering Measure
```dax
-- User Tolerance Limit Selection
Selected GM Tolerance = 
SELECTEDVALUE('GM % Tolerance Slicer'[Value], 0)

-- Visual Filter Flag for Performance Matrix
GM % Variance Filter Flag = 
VAR MarginGap = [Gross Margin %] - [BM GM %]
RETURN
IF(
    [Selected GM Tolerance] >= 0,
    IF(MarginGap >= [Selected GM Tolerance], 1, 0),
    IF(MarginGap <= [Selected GM Tolerance], 1, 0)
)
```

### 3.5 Supply Chain & Inventory Risk Measures
```dax
-- Net Forecast Error
Net Error = 
[Total Forecast Quantity] - [Total Quantity]

-- Net Error %
Net Error % = 
DIVIDE([Net Error], [Total Forecast Quantity], 0)

-- Absolute Error
Absolute Error = 
SUMX(
    VALUES(dim_product[product_code]),
    ABS([Total Forecast Quantity] - [Total Quantity])
)

-- Absolute Error %
Absolute Error % = 
DIVIDE([Absolute Error], [Total Forecast Quantity], 0)

-- Forecast Accuracy % (FA %)
Forecast Accuracy % = 
MAX(0, 1 - [Absolute Error %])

-- Forecast Accuracy Last Year (FA % LY)
Forecast Accuracy % LY = 
CALCULATE(
    [Forecast Accuracy %],
    SAMEPERIODLASTYEAR(dim_date[date])
)

-- Inventory Risk Factor Classification
Risk Factor = 
SWITCH(
    TRUE(),
    [Net Error] > 0, "Excess Inventory",
    [Net Error] < 0, "Out of Stock",
    "Balanced"
)
```

### 3.6 Executive & Macro Market Share Measures
```dax
-- AtliQ Total Revenue
AtliQ Revenue = 
[Net Sales]

-- Total Market Size (AtliQ + Competitors)
Total Market Revenue = 
SUM(marketshare[total_market_revenue])

-- AtliQ Market Share %
AtliQ Market Share % = 
DIVIDE([AtliQ Revenue], [Total Market Revenue], 0)

-- Division Contribution %
Division Contribution % = 
DIVIDE(
    [Net Sales],
    CALCULATE([Net Sales], ALLSELECTED(dim_product[division])),
    0
)

-- Channel Contribution %
Channel Contribution % = 
DIVIDE(
    [Net Sales],
    CALCULATE([Net Sales], ALLSELECTED(dim_customer[channel])),
    0
)
```

### 3.7 Header & Formatting Measures
```dax
-- Last Refresh Date Display
Last Refreshed On = 
"Last Refreshed: " & FORMAT(NOW(), "DD-MMM-YYYY HH:mm") & " UTC"

-- Currency & Scaling Notice
Unit Legend = 
"All figures in USD ($) Millions unless otherwise stated"
```

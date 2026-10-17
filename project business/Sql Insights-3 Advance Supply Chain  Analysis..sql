-- ====================================================================================================
-- PROJECT: BUSINESS INSIGHTS 360 - ATLIQ HARDWARE
-- MODULE 3: ADVANCED SUPPLY CHAIN ANALYTICS (VERSION 2.0)
-- Database Engine: MySQL 8.0+
-- Description: Actual vs Forecast Reconciliation, Trigger Automation, Accuracy & Inventory Risk
-- ====================================================================================================

USE gdb041;

-- ====================================================================================================
-- 1. HELPER TABLE: FACT_ACT_EST (ACTUAL SALES & FORECAST CONSOLIDATION)
-- Combines fact_sales_monthly and fact_forecast_monthly into a single table for fast analytics.
-- ====================================================================================================

DROP TABLE IF EXISTS fact_act_est;

CREATE TABLE fact_act_est AS
SELECT 
    s.date,
    s.fiscal_year,
    s.product_code,
    s.customer_code,
    s.sold_quantity,
    f.forecast_quantity
FROM fact_sales_monthly s
LEFT JOIN fact_forecast_monthly f 
    USING (product_code, customer_code, `date`)
UNION
SELECT 
    f.date,
    f.fiscal_year,
    f.product_code,
    f.customer_code,
    s.sold_quantity,
    f.forecast_quantity
FROM fact_forecast_monthly f
LEFT JOIN fact_sales_monthly s 
    USING (product_code, customer_code, `date`);

-- Add Composite Primary Key to enforce entity uniqueness
ALTER TABLE fact_act_est 
    ADD PRIMARY KEY (`date`, product_code, customer_code);

-- Null sanitation: replace NULLs with 0
UPDATE fact_act_est 
SET sold_quantity = COALESCE(sold_quantity, 0),
    forecast_quantity = COALESCE(forecast_quantity, 0);

-- Ensure fiscal_year is correctly populated
UPDATE fact_act_est 
SET fiscal_year = YEAR(DATE_ADD(`date`, INTERVAL 4 MONTH))
WHERE fiscal_year IS NULL OR fiscal_year = 0;


-- ====================================================================================================
-- 2. AUTOMATION TRIGGERS FOR REAL-TIME DATA PIPELINE
-- FIXED: Deprecated VALUES() function replaced with MySQL 8.0.20+ NEW.<col> syntax.
-- ====================================================================================================

-- Trigger 1: Real-time update when sales records are inserted
DROP TRIGGER IF EXISTS fact_sales_monthly_after_insert;

DELIMITER $$
CREATE TRIGGER fact_sales_monthly_after_insert
AFTER INSERT ON fact_sales_monthly
FOR EACH ROW
BEGIN
    INSERT INTO fact_act_est (`date`, fiscal_year, product_code, customer_code, sold_quantity, forecast_quantity) 
    VALUES (NEW.date, NEW.fiscal_year, NEW.product_code, NEW.customer_code, NEW.sold_quantity, 0)
    ON DUPLICATE KEY UPDATE 
        sold_quantity = NEW.sold_quantity,
        fiscal_year = NEW.fiscal_year;
END $$
DELIMITER ;


-- Trigger 2: Real-time update when forecast records are inserted
DROP TRIGGER IF EXISTS fact_forecast_monthly_after_insert;

DELIMITER $$
CREATE TRIGGER fact_forecast_monthly_after_insert
AFTER INSERT ON fact_forecast_monthly
FOR EACH ROW
BEGIN
    INSERT INTO fact_act_est (`date`, fiscal_year, product_code, customer_code, sold_quantity, forecast_quantity) 
    VALUES (NEW.date, NEW.fiscal_year, NEW.product_code, NEW.customer_code, 0, NEW.forecast_quantity)
    ON DUPLICATE KEY UPDATE 
        forecast_quantity = NEW.forecast_quantity,
        fiscal_year = NEW.fiscal_year;
END $$
DELIMITER ;


-- ====================================================================================================
-- PROBLEM STATEMENT 1: FORECAST ACCURACY & RISK ANALYSIS REPORT (FY 2021)
-- Core Supply Chain KPIs:
-- Net Error = Forecast Qty - Sold Qty
-- Net Error % = Net Error / Forecast Qty
-- Absolute Error = |Forecast Qty - Sold Qty|
-- Forecast Accuracy % = max(0, 100 - (Absolute Error / Forecast Qty * 100))
-- Risk Factor = Excess Inventory (Net Error > 0) vs Out of Stock (Net Error < 0)
-- ====================================================================================================

DROP PROCEDURE IF EXISTS get_forecast_accuracy_report;

DELIMITER $$
CREATE PROCEDURE get_forecast_accuracy_report(
    IN in_fiscal_year INT
)
BEGIN
    WITH customer_forecast_metrics AS (
        SELECT 
            f.customer_code,
            c.customer,
            c.market,
            SUM(f.sold_quantity) AS total_sold_qty,
            SUM(f.forecast_quantity) AS total_forecast_qty,
            SUM(f.forecast_quantity - f.sold_quantity) AS net_error,
            ROUND(SUM(f.forecast_quantity - f.sold_quantity) * 100.0 / NULLIF(SUM(f.forecast_quantity), 0), 2) AS net_error_pct,
            SUM(ABS(f.forecast_quantity - f.sold_quantity)) AS abs_error,
            ROUND(SUM(ABS(f.forecast_quantity - f.sold_quantity)) * 100.0 / NULLIF(SUM(f.forecast_quantity), 0), 2) AS abs_error_pct
        FROM fact_act_est f
        INNER JOIN dim_customer c 
            ON c.customer_code = f.customer_code
        WHERE f.fiscal_year = in_fiscal_year
        GROUP BY f.customer_code, c.customer, c.market
    )
    SELECT 
        customer_code,
        customer,
        market,
        total_sold_qty,
        total_forecast_qty,
        net_error,
        net_error_pct,
        abs_error,
        abs_error_pct,
        GREATEST(0, ROUND(100 - abs_error_pct, 2)) AS forecast_accuracy_pct,
        CASE 
            WHEN net_error > 0 THEN 'Excess Inventory'
            WHEN net_error < 0 THEN 'Out of Stock'
            ELSE 'Balanced'
        END AS risk_factor
    FROM customer_forecast_metrics
    ORDER BY forecast_accuracy_pct DESC, total_sold_qty DESC;
END $$
DELIMITER ;

-- Verification:
-- CALL get_forecast_accuracy_report(2021);


-- ====================================================================================================
-- PROBLEM STATEMENT 2: YEAR-OVER-YEAR FORECAST ACCURACY BENCHMARK (FY 2020 VS FY 2021)
-- Identifies accounts where forecast accuracy deteriorated year-over-year.
-- ====================================================================================================

WITH accuracy_summary AS (
    SELECT 
        f.fiscal_year,
        f.customer_code,
        c.customer,
        c.market,
        GREATEST(0, ROUND(100 - (SUM(ABS(f.forecast_quantity - f.sold_quantity)) * 100.0 / NULLIF(SUM(f.forecast_quantity), 0)), 2)) AS accuracy_pct
    FROM fact_act_est f
    INNER JOIN dim_customer c 
        ON c.customer_code = f.customer_code
    WHERE f.fiscal_year IN (2020, 2021)
    GROUP BY f.fiscal_year, f.customer_code, c.customer, c.market
),
fy2020_acc AS (
    SELECT customer_code, customer, market, accuracy_pct AS fa_2020
    FROM accuracy_summary
    WHERE fiscal_year = 2020
),
fy2021_acc AS (
    SELECT customer_code, customer, market, accuracy_pct AS fa_2021
    FROM accuracy_summary
    WHERE fiscal_year = 2021
)
SELECT 
    f21.customer_code,
    f21.customer,
    f21.market,
    f20.fa_2020 AS accuracy_fy2020,
    f21.fa_2021 AS accuracy_fy2021,
    ROUND(f21.fa_2021 - f20.fa_2020, 2) AS yoy_accuracy_variance
FROM fy2021_acc f21
INNER JOIN fy2020_acc f20 
    ON f20.customer_code = f21.customer_code
WHERE f21.fa_2021 < f20.fa_2020
ORDER BY yoy_accuracy_variance ASC;

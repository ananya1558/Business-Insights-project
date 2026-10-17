-- ====================================================================================================
-- PROJECT: BUSINESS INSIGHTS 360 - ATLIQ HARDWARE
-- MODULE 2: ADVANCED TOP PERFORMER ANALYTICS (VERSION 2.0)
-- Database Engine: MySQL 8.0+
-- Description: Top Markets, Customers, Products, Regional Share & Window Functions
-- ====================================================================================================

USE gdb041;

-- ====================================================================================================
-- 1. OPTIMIZATION: GENERATED FISCAL YEAR COLUMN
-- To optimize query execution time across millions of sales records, we persist fiscal_year.
-- ====================================================================================================

-- Safely add fiscal_year column if it does not already exist
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'fact_sales_monthly' 
      AND COLUMN_NAME = 'fiscal_year'
);

SET @sql_stmt = IF(@col_exists = 0,
    'ALTER TABLE fact_sales_monthly ADD COLUMN fiscal_year YEAR AFTER `date`;',
    'SELECT "fiscal_year column already exists" AS message;'
);
PREPARE stmt FROM @sql_stmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Populate / refresh fiscal_year values
SET SQL_SAFE_UPDATES = 0;
UPDATE fact_sales_monthly 
SET fiscal_year = YEAR(DATE_ADD(`date`, INTERVAL 4 MONTH))
WHERE fiscal_year IS NULL OR fiscal_year = 0;

-- Optional Index for massive query speedup
CREATE INDEX IF NOT EXISTS idx_sales_fy_cust ON fact_sales_monthly (fiscal_year, customer_code);
CREATE INDEX IF NOT EXISTS idx_sales_fy_prod ON fact_sales_monthly (fiscal_year, product_code);


-- ====================================================================================================
-- 2. REUSABLE DATA VIEWS: PRE-INVOICE, POST-INVOICE, AND NET SALES
-- Multi-tier P&L data calculation views:
-- Gross Sales -> Pre-Invoice Discount -> Net Invoice Sales -> Post-Invoice Deductions -> Net Sales
-- ====================================================================================================

-- VIEW 1: PRE_INVOICE_SALES
CREATE OR REPLACE VIEW pre_invoice_sales AS
SELECT 
    s.date,
    s.fiscal_year,
    s.product_code,
    s.customer_code,
    c.customer,
    c.market,
    c.region,
    p.product,
    p.variant,
    s.sold_quantity,
    g.gross_price,
    ROUND(g.gross_price * s.sold_quantity, 2) AS gross_total_price,
    COALESCE(pid.pre_invoice_discount_pct, 0) AS pre_invoice_discount_pct
FROM fact_sales_monthly s
INNER JOIN dim_customer c 
    ON c.customer_code = s.customer_code
INNER JOIN dim_product p 
    ON p.product_code = s.product_code
INNER JOIN fact_gross_price g 
    ON g.product_code = s.product_code 
    AND g.fiscal_year = s.fiscal_year
LEFT JOIN fact_pre_invoice_deductions pid 
    ON pid.customer_code = s.customer_code 
    AND pid.fiscal_year = s.fiscal_year;


-- VIEW 2: POST_INVOICE_SALES
CREATE OR REPLACE VIEW post_invoice_sales AS 
SELECT 
    pre.*,
    ROUND(pre.gross_total_price * (1 - pre.pre_invoice_discount_pct), 2) AS net_invoice_sales,
    COALESCE(pod.discounts_pct + pod.other_deductions_pct, 0) AS post_invoice_discount_pct
FROM pre_invoice_sales pre
LEFT JOIN fact_post_invoice_deductions pod 
    ON pod.customer_code = pre.customer_code 
   AND pod.product_code = pre.product_code 
   AND pod.date = pre.date;


-- VIEW 3: NET_SALES (FINAL P&L REVENUE FOUNDATION)
CREATE OR REPLACE VIEW net_sales AS
SELECT 
    post.*,
    ROUND(post.net_invoice_sales * (1 - post.post_invoice_discount_pct), 2) AS net_sales
FROM post_invoice_sales post;


-- ====================================================================================================
-- PROBLEM STATEMENT 1: TOP N MARKETS BY NET SALES
-- ====================================================================================================

-- Ad-hoc query for FY 2021
SELECT 
    market,
    ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
FROM net_sales
WHERE fiscal_year = 2021
GROUP BY market
ORDER BY net_sales_mln DESC
LIMIT 5;

-- Parameterized Stored Procedure
DROP PROCEDURE IF EXISTS get_top_n_markets_by_net_sales;

DELIMITER $$
CREATE PROCEDURE get_top_n_markets_by_net_sales(
    IN in_fiscal_year INT,
    IN in_top_n INT
)
BEGIN
    SELECT 
        market,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = in_fiscal_year
    GROUP BY market
    ORDER BY net_sales_mln DESC
    LIMIT in_top_n;
END $$
DELIMITER ;

-- Verification:
-- CALL get_top_n_markets_by_net_sales(2021, 5);


-- ====================================================================================================
-- PROBLEM STATEMENT 2: TOP N CUSTOMERS BY NET SALES
-- ====================================================================================================

DROP PROCEDURE IF EXISTS get_top_n_customers_by_net_sales;

DELIMITER $$
CREATE PROCEDURE get_top_n_customers_by_net_sales(
    IN in_fiscal_year INT,
    IN in_top_n INT
)
BEGIN
    SELECT 
        customer,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = in_fiscal_year
    GROUP BY customer
    ORDER BY net_sales_mln DESC
    LIMIT in_top_n;
END $$
DELIMITER ;

-- Verification:
-- CALL get_top_n_customers_by_net_sales(2021, 5);


-- ====================================================================================================
-- PROBLEM STATEMENT 3: TOP N CUSTOMERS IN A SPECIFIC MARKET
-- ====================================================================================================

DROP PROCEDURE IF EXISTS get_top_n_customers_by_market;

DELIMITER $$
CREATE PROCEDURE get_top_n_customers_by_market(
    IN in_market VARCHAR(50),
    IN in_fiscal_year INT,
    IN in_top_n INT
)
BEGIN
    SELECT 
        customer,
        market,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = in_fiscal_year 
      AND market = in_market
    GROUP BY customer, market
    ORDER BY net_sales_mln DESC
    LIMIT in_top_n;
END $$
DELIMITER ;

-- Verification:
-- CALL get_top_n_customers_by_market('India', 2021, 5);


-- ====================================================================================================
-- PROBLEM STATEMENT 4: TOP N PRODUCTS BY NET SALES
-- ====================================================================================================

DROP PROCEDURE IF EXISTS get_top_n_products_by_net_sales;

DELIMITER $$
CREATE PROCEDURE get_top_n_products_by_net_sales(
    IN in_fiscal_year INT,
    IN in_top_n INT
)
BEGIN
    SELECT 
        product,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = in_fiscal_year
    GROUP BY product
    ORDER BY net_sales_mln DESC
    LIMIT in_top_n;
END $$
DELIMITER ;

-- Verification:
-- CALL get_top_n_products_by_net_sales(2021, 5);


-- ====================================================================================================
-- PROBLEM STATEMENT 5: TOP 10 CUSTOMERS GLOBALLY BY % CONTRIBUTION TO NET SALES
-- ====================================================================================================

WITH customer_sales AS (
    SELECT 
        customer,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = 2021
    GROUP BY customer
)
SELECT 
    customer,
    net_sales_mln,
    ROUND(net_sales_mln * 100.0 / SUM(net_sales_mln) OVER (), 2) AS net_sales_pct
FROM customer_sales
ORDER BY net_sales_mln DESC
LIMIT 10;


-- ====================================================================================================
-- PROBLEM STATEMENT 6: REGION-WISE % NET SALES CONTRIBUTION BY CUSTOMERS
-- ====================================================================================================

WITH regional_cust_sales AS (
    SELECT 
        fiscal_year,
        region,
        customer,
        ROUND(SUM(net_sales) / 1000000, 2) AS net_sales_mln
    FROM net_sales
    WHERE fiscal_year = 2021
    GROUP BY fiscal_year, region, customer
)
SELECT 
    fiscal_year,
    region,
    customer,
    net_sales_mln,
    ROUND(net_sales_mln * 100.0 / SUM(net_sales_mln) OVER (PARTITION BY fiscal_year, region), 2) AS regional_net_sales_pct
FROM regional_cust_sales
ORDER BY region, net_sales_mln DESC;


-- ====================================================================================================
-- PROBLEM STATEMENT 7: TOP N PRODUCTS IN EACH DIVISION BY QUANTITY SOLD
-- FIXED: Corrected nested CTE syntax to modern chained CTE compliant with MySQL 8.0+.
-- ====================================================================================================

DROP PROCEDURE IF EXISTS get_top_n_products_per_division_by_qty;

DELIMITER $$
CREATE PROCEDURE get_top_n_products_per_division_by_qty(
    IN in_fiscal_year INT,
    IN in_top_n INT
)
BEGIN
    WITH division_product_qty AS (
        SELECT 
            p.division,
            p.product,
            SUM(s.sold_quantity) AS total_sold_qty
        FROM fact_sales_monthly s
        INNER JOIN dim_product p 
            ON p.product_code = s.product_code
        WHERE s.fiscal_year = in_fiscal_year
        GROUP BY p.division, p.product
    ),
    ranked_products AS (
        SELECT 
            division,
            product,
            total_sold_qty,
            DENSE_RANK() OVER (PARTITION BY division ORDER BY total_sold_qty DESC) AS product_rank
        FROM division_product_qty
    )
    SELECT 
        division,
        product,
        total_sold_qty,
        product_rank
    FROM ranked_products
    WHERE product_rank <= in_top_n
    ORDER BY division, product_rank ASC;
END $$
DELIMITER ;

-- Verification:
-- CALL get_top_n_products_per_division_by_qty(2021, 3);


-- ====================================================================================================
-- PROBLEM STATEMENT 8: TOP 2 MARKETS IN EVERY REGION BY GROSS SALES
-- FIXED: Corrected nested CTE syntax to chained CTE compliant with MySQL 8.0+.
-- ====================================================================================================

WITH market_regional_gross AS (
    SELECT 
        c.region,
        c.market,
        ROUND(SUM(s.sold_quantity * g.gross_price) / 1000000, 2) AS gross_sales_mln
    FROM fact_sales_monthly s
    INNER JOIN dim_customer c 
        ON c.customer_code = s.customer_code
    INNER JOIN fact_gross_price g 
        ON g.product_code = s.product_code 
       AND g.fiscal_year = s.fiscal_year
    WHERE s.fiscal_year = 2021
    GROUP BY c.region, c.market
),
ranked_markets AS (
    SELECT 
        region,
        market,
        gross_sales_mln,
        DENSE_RANK() OVER (PARTITION BY region ORDER BY gross_sales_mln DESC) AS market_rank
    FROM market_regional_gross
)
SELECT 
    region,
    market,
    gross_sales_mln,
    market_rank
FROM ranked_markets
WHERE market_rank <= 2
ORDER BY region, market_rank ASC;
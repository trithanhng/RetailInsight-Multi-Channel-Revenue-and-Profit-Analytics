# RetailInsight: Multi-Channel Revenue and Profit Analytics

## Overview
RetailInsight is a data analytics project that explores retail revenue, estimated gross profit, and sales performance across multiple channels. Using Microsoft's **AdventureWorks Data Warehouse** dataset, the project aims to turn sales data into useful business insights through data processing, SQL analysis, and interactive dashboards.

## Dataset
- **Source:** [Microsoft AdventureWorks Data Warehouse](https://github.com/microsoft/sql-server-samples/tree/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script)
- **Sales channels:** Internet sales and reseller sales
- **Analysis dimensions:** Time, product, customer/reseller, and geography

## Objectives
1. Integrate and prepare sales data from different channels.
2. Analyze revenue and estimated gross profit by channel, product, region, and time.
3. Build a data pipeline and run analytical queries using Apache Spark and Spark SQL.
4. Compare query performance against a traditional Python/Pandas or SQL baseline under comparable conditions.
5. Present key performance indicators (KPIs) in an interactive dashboard.

## Proposed Technology Stack
- **Data processing:** Python, Pandas, Apache Spark
- **Analytics:** Spark SQL
- **Environment:** Docker / Docker Compose
- **Dashboard:** Streamlit

## Expected Outcomes
- A reproducible retail analytics pipeline
- SQL queries and performance benchmark results
- Revenue and estimated gross-profit reports by sales channel
- An interactive dashboard for exploring business KPIs

> **Note:** Gross profit will be estimated as sales revenue minus available product costs. This is not the same as net profit, which would require additional operating expenses and other financial data.

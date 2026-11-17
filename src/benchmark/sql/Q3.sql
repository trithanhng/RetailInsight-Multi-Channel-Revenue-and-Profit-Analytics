WITH sales AS (
    SELECT ProductKey, channel, order_id, revenue_units, cost_units, profit_units FROM FactInternetSales
    UNION ALL
    SELECT ProductKey, channel, order_id, revenue_units, cost_units, profit_units FROM FactResellerSales
)
SELECT f.channel, c.ProductCategoryKey, c.EnglishProductCategoryName,
       SUM(f.revenue_units) AS revenue_units, SUM(f.cost_units) AS cost_units,
       SUM(f.profit_units) AS profit_units, COUNT(DISTINCT f.order_id) AS orders
FROM sales f JOIN DimProduct p ON f.ProductKey = p.ProductKey
LEFT JOIN DimProductSubcategory s ON p.ProductSubcategoryKey = s.ProductSubcategoryKey
LEFT JOIN DimProductCategory c ON s.ProductCategoryKey = c.ProductCategoryKey
GROUP BY f.channel, c.ProductCategoryKey, c.EnglishProductCategoryName
ORDER BY f.channel, c.ProductCategoryKey NULLS LAST

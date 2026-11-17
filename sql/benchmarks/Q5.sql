WITH sales AS (
    SELECT OrderDateKey, channel, order_id, revenue_units, cost_units, profit_units FROM FactInternetSales
    UNION ALL
    SELECT OrderDateKey, channel, order_id, revenue_units, cost_units, profit_units FROM FactResellerSales
)
SELECT DATE_FORMAT(d.FullDateAlternateKey, 'yyyy-MM') AS purchase_month, f.channel,
       SUM(f.revenue_units) AS revenue_units, SUM(f.cost_units) AS cost_units,
       SUM(f.profit_units) AS profit_units, COUNT(DISTINCT f.order_id) AS orders
FROM sales f JOIN DimDate d ON f.OrderDateKey = d.DateKey
GROUP BY DATE_FORMAT(d.FullDateAlternateKey, 'yyyy-MM'), f.channel
ORDER BY purchase_month, f.channel

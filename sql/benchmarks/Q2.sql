SELECT f.ResellerKey, r.ResellerName, SUM(f.revenue_units) AS revenue_units,
       COUNT(DISTINCT f.order_id) AS orders
FROM FactResellerSales f JOIN DimReseller r ON f.ResellerKey = r.ResellerKey
GROUP BY f.ResellerKey, r.ResellerName ORDER BY f.ResellerKey

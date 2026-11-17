SELECT r.BusinessType, SUM(f.revenue_units) AS revenue_units,
       SUM(f.cost_units) AS cost_units, SUM(f.profit_units) AS profit_units,
       COUNT(DISTINCT f.order_id) AS orders
FROM FactResellerSales f JOIN DimReseller r ON f.ResellerKey = r.ResellerKey
GROUP BY r.BusinessType ORDER BY r.BusinessType NULLS LAST

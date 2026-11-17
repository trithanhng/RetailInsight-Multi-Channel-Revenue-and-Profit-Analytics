SELECT f.CustomerKey, SUM(f.revenue_units) AS revenue_units,
       COUNT(DISTINCT f.order_id) AS orders
FROM FactInternetSales f JOIN DimCustomer c ON f.CustomerKey = c.CustomerKey
GROUP BY f.CustomerKey ORDER BY revenue_units DESC, f.CustomerKey ASC LIMIT 10

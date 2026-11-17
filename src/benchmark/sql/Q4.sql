SELECT g.CountryRegionCode, g.StateProvinceCode, SUM(f.revenue_units) AS revenue_units,
       COUNT(DISTINCT f.order_id) AS orders
FROM FactResellerSales f JOIN DimReseller r ON f.ResellerKey = r.ResellerKey
LEFT JOIN DimGeography g ON r.GeographyKey = g.GeographyKey
GROUP BY g.CountryRegionCode, g.StateProvinceCode
ORDER BY g.CountryRegionCode NULLS LAST, g.StateProvinceCode NULLS LAST

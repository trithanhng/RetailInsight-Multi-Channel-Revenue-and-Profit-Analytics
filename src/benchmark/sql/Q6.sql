WITH totals AS (
    SELECT g.CountryRegionCode, g.StateProvinceCode, f.ResellerKey, r.ResellerName,
           SUM(f.revenue_units) AS revenue_units
    FROM FactResellerSales f JOIN DimReseller r ON f.ResellerKey = r.ResellerKey
    LEFT JOIN DimGeography g ON r.GeographyKey = g.GeographyKey
    GROUP BY g.CountryRegionCode, g.StateProvinceCode, f.ResellerKey, r.ResellerName
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY CountryRegionCode, StateProvinceCode
        ORDER BY revenue_units DESC, ResellerKey ASC
    ) AS rank FROM totals
)
SELECT CountryRegionCode, StateProvinceCode, ResellerKey, ResellerName, revenue_units, rank
FROM ranked WHERE rank <= 3
ORDER BY CountryRegionCode NULLS LAST, StateProvinceCode NULLS LAST, rank

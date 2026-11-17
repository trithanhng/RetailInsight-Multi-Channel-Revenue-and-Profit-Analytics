SELECT ProductKey, EnglishProductName, list_price_units
FROM DimProduct WHERE list_price_units >= 1000000
ORDER BY ProductKey

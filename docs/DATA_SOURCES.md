# Nguồn dữ liệu AdventureWorksDW

Nguồn duy nhất của bản triển khai là **Microsoft SQL Server Samples / AdventureWorksDW**. Dữ liệu doanh nghiệp giả lập, giấy phép MIT; được dùng đúng tính chất dữ liệu mẫu cho bài tập CO4033.

- [Thư mục dataset đầy đủ](https://github.com/microsoft/sql-server-samples/tree/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script)
- [Giới thiệu và cách Microsoft phân phối AdventureWorks](https://github.com/microsoft/sql-server-samples/blob/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/README.md)
- Commit: `b47eadc85277f72843647223cde53aa1b85ffcb8`.

## Link tải trực tiếp

| File | Số dòng | Vai trò |
|---|---:|---|
| [FactInternetSales.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/FactInternetSales.csv) | 60.398 | Bán qua Internet |
| [FactResellerSales.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/FactResellerSales.csv) | 60.855 | Bán qua đại lý |
| [DimProduct.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimProduct.csv) | 606 | Sản phẩm và phiên bản sản phẩm |
| [DimProductSubcategory.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimProductSubcategory.csv) | 37 | Nhóm sản phẩm |
| [DimProductCategory.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimProductCategory.csv) | 4 | Danh mục |
| [DimSalesTerritory.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimSalesTerritory.csv) | 11 | Vùng và quốc gia |
| [DimCurrency.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimCurrency.csv) | 105 | Mã tiền tệ nguồn |
| [DimReseller.csv](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/DimReseller.csv) | 701 | Mã/tên đại lý, loại hình cửa hàng; 635 đại lý có giao dịch trong fact |
| [instawdbdw.sql](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/samples/databases/adventure-works/data-warehouse-install-script/instawdbdw.sql) | — | DDL để đọc schema |
| [license.txt](https://raw.githubusercontent.com/microsoft/sql-server-samples/b47eadc85277f72843647223cde53aa1b85ffcb8/license.txt) | — | Giấy phép Microsoft |

Lệnh tải tự động: `python -m retail_bi.pipeline --download`. CSV dùng UTF-8, phân cách `|`, không có header. Chương trình chỉ **đọc schema**, không thực thi DDL tạo/xóa database. Không cần SQL Server hoặc file backup `.bak`.

## Ý nghĩa trường và phạm vi

`SalesAmount` là số tiền sau chiết khấu; `TotalProductCost` là giá vốn của dòng. `ExtendedAmount` và `DiscountAmount` phục vụ đối soát. Khóa giao dịch dùng `SalesOrderNumber`, `SalesOrderLineNumber`, thêm kênh để tránh đụng số đơn giữa hai nguồn.

Số tiền cơ sở sử dụng USD theo [mô hình AdventureWorks của Microsoft Analysis Services](https://github.com/microsoft/Analysis-Services/blob/master/AsPartitionProcessing/AsPartitionProcessing.AdventureWorks/Model.bim). `CurrencyAlternateKey` được giữ để truy vết; không chuyển tỷ giá lần thứ hai.

Internet: 29/12/2010–28/01/2014. Reseller: 29/12/2010–29/11/2013. So sánh kênh cần lưu ý khác phạm vi ghi nhận; shortcut kỳ chung dùng 01/01/2011–31/10/2013. Không có bảng hoàn trả hoặc chi phí vận hành đầy đủ để suy ra lợi nhuận ròng.

Schema từng bảng, SHA-256, URL và dung lượng được lưu trong `manifest.json`; schema sau làm sạch và số ô thiếu nằm trong `data_quality.json`. Xem bản minh chứng đã xuất tại [output/evidence](../output/evidence).

## Tái sử dụng dữ liệu trong repository

Pipeline đọc các CSV có sẵn tại `data/raw`, tải bổ sung khi thiếu. Các bảng còn lại trong raw là nguồn Microsoft gốc của nhóm nhưng không phải mọi bảng đều tham gia mart. Mã/tên đại lý lấy từ DimReseller, không suy ra cửa hàng từ phương thức thanh toán hoặc vùng. Internet không có cửa hàng vật lý trong dữ liệu này.

SHA-256 trong manifest ghi nhận byte thực tế trên máy; Git có thể đổi LF/CRLF khi checkout. Kiểm tra nguồn của lượt rà soát đã xác nhận nội dung trùng bản Microsoft được ghim sau khi chuẩn hóa xuống dòng. Pipeline ghi nhận hash thực tế nhưng chưa tự đối chiếu hash chuẩn; nếu thay CSV, cần kiểm tra lại nguồn. Không coi SHA khác do xuống dòng là một thay đổi giao dịch.

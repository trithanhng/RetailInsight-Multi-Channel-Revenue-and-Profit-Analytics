# Q1–Q8: pandas và Spark SQL

Trạng thái: **passed**.

Run: `20261117T212533081321Z`; số mẫu đã ghi: 80.

CPU: Intel64 Family 6 Model 154 Stepping 3, GenuineIntel; RAM: None byte; CPU logic: 12.

OS: Windows-11-10.0.26300-SP0; Python: 3.12.10; pandas: 2.2.3; Spark: 4.0.1.

Spark startup: 18.335524099995382 giây. Chi tiết cấu hình và giới hạn bộ nhớ: [environment.json](environment.json).

| Q | pandas median (s) | Spark median (s) | Spark/pandas | Dòng kết quả | Khớp |
|---|---:|---:|---:|---:|---|
| Q1 | 0.002452 | 0.126758 | 51.70× | 282 | 100% |
| Q2 | 0.081340 | 0.902953 | 11.10× | 635 | 100% |
| Q3 | 0.376352 | 1.701700 | 4.52× | 7 | 100% |
| Q4 | 0.128798 | 0.850669 | 6.60× | 64 | 100% |
| Q5 | 1.439184 | 1.573696 | 1.09× | 71 | 100% |
| Q6 | 0.115578 | 0.981144 | 8.49× | 169 | 100% |
| Q7 | 0.077116 | 0.764661 | 9.92× | 3 | 100% |
| Q8 | 0.076994 | 0.937534 | 12.18× | 10 | 100% |

Tỷ số >1 nghĩa là pandas nhanh hơn. Chỉ so sánh hai engine trong cùng Q.

Mốc đo: truy vấn bảng pandas trong bộ nhớ / temporary view Spark → JOIN/filter/group/window/sort → materialize về pandas. Không đọc Parquet. Không tính chuẩn bị nguồn, nạp bảng vào Spark, khởi động JVM, hash, đối chiếu, ghi CSV hoặc lấy execution plan.

Nạp bảng vào Spark: 4.816018500016071 giây. Không persist/cache dữ liệu ứng dụng; không xóa cache OS. Giữ lượt đầu, không bỏ warm-up. Thứ tự Q xáo bằng seed cố định; luân phiên engine.

Các truy vấn chẩn đoán EXPLAIN chạy sau các lượt đo để tránh làm nóng optimizer trước phép đo. Mỗi Q lưu formatted plan trước action và executed plan sau action.

Số tiền là số nguyên 1/10.000 USD; so khớp tuyệt đối từng ô sau sắp thứ tự. Q7 phân tích loại hình đại lý, không giả lập phương thức thanh toán.

Không đo peak memory, tải nền hoặc tốc độ ổ đĩa. Local[2] không chứng minh hiệu năng cụm phân tán.

Minh chứng: [measurements.csv](measurements.csv), [summary.csv](summary.csv), [input_manifest.json](input_manifest.json), [environment.json](environment.json), [benchmark.log](benchmark.log), thư mục `results/` và `plans/`. SQL và SHA-256 được lưu trong environment.json.

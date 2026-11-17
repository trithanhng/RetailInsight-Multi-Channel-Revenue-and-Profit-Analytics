# Q1–Q8: pandas và Spark SQL

Trạng thái: **passed**.

Run: `20261117T125908401490Z`; số mẫu đã ghi: 80.

CPU: 12th Gen Intel(R) Core(TM) i5-12450H; RAM: 16852574208 byte; CPU logic: 12.

OS: Windows-11-10.0.26300-SP0; Python: 3.12.10; pandas: 2.2.3; Spark: 4.0.1.

Spark startup: 6.053992600063793 giây. Chi tiết cấu hình và giới hạn bộ nhớ: [environment.json](environment.json).

| Q | pandas median (s) | Spark median (s) | Spark/pandas | Dòng kết quả | Khớp |
|---|---:|---:|---:|---:|---|
| Q1 | 0.003708 | 0.220070 | 59.34× | 282 | 100% |
| Q2 | 0.069195 | 0.599833 | 8.67× | 635 | 100% |
| Q3 | 0.231495 | 1.384858 | 5.98× | 7 | 100% |
| Q4 | 0.100401 | 0.750434 | 7.47× | 64 | 100% |
| Q5 | 1.182847 | 1.003958 | 0.85× | 71 | 100% |
| Q6 | 0.088226 | 0.697414 | 7.90× | 169 | 100% |
| Q7 | 0.062766 | 0.532090 | 8.48× | 3 | 100% |
| Q8 | 0.071441 | 0.633955 | 8.87× | 10 | 100% |

Tỷ số >1 nghĩa là pandas nhanh hơn. Chỉ so sánh hai engine trong cùng Q.

Mốc đo: đọc Parquet và cột cần thiết → JOIN/filter/group/window/sort → materialize về pandas. Không tính chuẩn bị nguồn, khởi động JVM, hash, đối chiếu, ghi CSV hoặc lấy execution plan.

Không persist/cache dữ liệu ứng dụng; không xóa cache OS; tính hash đầu vào có thể làm nóng cache. Giữ lượt đầu, không bỏ warm-up. Thứ tự Q xáo bằng seed cố định; luân phiên engine.

Các truy vấn chẩn đoán EXPLAIN chạy sau các lượt đo để tránh làm nóng optimizer trước phép đo. Mỗi Q lưu formatted plan trước action và executed plan sau action.

Số tiền là số nguyên 1/10.000 USD; so khớp tuyệt đối từng ô sau sắp thứ tự. Q7 phân tích loại hình đại lý, không giả lập phương thức thanh toán.

Không đo peak memory, tải nền hoặc tốc độ ổ đĩa. Local[2] không chứng minh hiệu năng cụm phân tán.

Minh chứng: [measurements.csv](measurements.csv), [summary.csv](summary.csv), [input_manifest.json](input_manifest.json), [environment.json](environment.json), [benchmark.log](benchmark.log), thư mục `results/`, `plans/` và `queries/`.

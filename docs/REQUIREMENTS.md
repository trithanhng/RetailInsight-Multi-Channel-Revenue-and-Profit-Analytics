# Đối chiếu yêu cầu đề tài 01

Căn cứ mục II và phần ĐỀ TÀI 01 trong tài liệu giao bài CO4033. Bản kỹ thuật không gán tên hoặc tỷ lệ đóng góp cá nhân.

| Yêu cầu | Minh chứng |
|---|---|
| Hai câu hỏi kiểm chứng và người dùng cuối | README; báo cáo PDF và Markdown |
| Nguồn, giấy phép, schema, thời gian, số dòng | DATA_SOURCES.md; manifest.json; MICROSOFT_LICENSE.txt |
| Cửa hàng/đại lý và chi phí | DimReseller; store_id/store/store_type trong mart; TotalProductCost làm giá vốn; Internet không có mã cửa hàng vật lý |
| Thiếu/trùng, thời gian, ngoại lệ và trước–sau | clean_source; quality_summary.csv; data_quality.json; mẫu before/after |
| Pipeline thu thập → làm sạch → lưu → phân tích → BI | pipeline.py; benchmark.py; dashboard.py |
| Spark SQL tổng hợp và phân khúc | sql/retail; spark_monthly/region/category/customer_segments.csv |
| Dashboard kênh, vùng, sản phẩm và bộ lọc | Bốn trang, lựa chọn Tất cả, kỳ chung, bộ lọc liên kết và reset |
| Doanh thu thuần, biên lợi nhuận, tăng trưởng tháng | analytics.py; KPI dashboard; công thức và giá trị trong báo cáo |
| Ít nhất 3 kiểm thử | tests/test_retail.py, test_analytics.py, test_dashboard.py, test_benchmark.py |
| Baseline pandas so Spark SQL; thời gian và độ khớp | benchmark.csv, summary, environment; kiểm tra từng nhóm |
| Cấu hình, cùng dữ liệu và giới hạn hệ thống | Phương pháp đo trong báo cáo; môi trường benchmark; tải 5× riêng |
| Ít nhất 3 nhận xét và quyết định có điều kiện | Trang Tổng quan; báo cáo kết quả; bảng chi phí/rủi ro/điều kiện |
| Mã, README, dữ liệu mẫu hoặc script tải | Gói GitHub whitelist; pipeline --download; output/evidence |
| Báo cáo PDF/DOCX, kiến trúc, thực nghiệm, sai số | PDF và docs/BAO_CAO.md; sơ đồ pipeline; dung sai tiền; kỳ biên |
| Slide/demo | docs/DEMO.md; ứng dụng Streamlit chạy local |
| Log và mẫu đầu ra | output/evidence; --verify lưu mã thoát và stdout thực |
| Hình minh chứng | Biểu đồ kết quả sinh từ mart; giao diện Tổng quan đã quan sát trực tiếp. Ảnh chụp UI chưa lưu do giới hạn công cụ trình duyệt; không thay bằng ảnh giả |
| Liên kết repository | [RetailInsight](https://github.com/winter-1402/RetailInsight-Multi-Channel-Revenue-and-Profit-Analytics); nhánh feat/assignment-completion-20261116 |
| Ghi công cụ AI và giới hạn học thuật | docs/AI_USAGE.md; phần phương pháp trong báo cáo |

Không khẳng định hệ thống đã đạt quy mô Big Data hoặc mọi điều kiện nộp lớp đã hoàn tất khi ảnh giao diện và đóng góp học thuật chưa được xác nhận. Bản mã nguồn, dashboard, báo cáo và phép đo được kiểm chứng riêng với các phần phụ thuộc hình thức nộp.


Rà soát ngày 16/11/2026 và trạng thái các minh chứng: [COMPLIANCE_REVIEW.md](COMPLIANCE_REVIEW.md).

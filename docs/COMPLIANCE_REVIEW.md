# Rà soát yêu cầu CO4033 đề tài 01

Ngày rà soát: 16/11/2026. Căn cứ mục II và phần ĐỀ TÀI 01 của hai tài liệu giao bài đã cung cấp. Repository gốc tại thời điểm kiểm tra chỉ có README, CSV nguồn và thư mục dự kiến; nhánh `feat/assignment-completion-20261116` bổ sung bản triển khai hoàn chỉnh để nhóm xem và merge.

## Kết quả đối chiếu

| Yêu cầu | Kết quả và minh chứng |
|---|---|
| Hai câu hỏi kinh doanh, người dùng cuối | README; báo cáo PDF/Markdown xác định quản lý bán hàng và tài chính, so sánh hiệu quả kênh và ưu tiên danh mục/vùng |
| Giao dịch, sản phẩm, cửa hàng/đại lý, kênh và chi phí | Hai fact và 6 chiều, gồm DimReseller. Mart có store_id/store/store_type; 701 đại lý trong chiều, 635 có giao dịch. Internet được ghi rõ không có mã cửa hàng vật lý, không tạo dữ liệu giả bổ sung |
| Nguồn, giấy phép, schema, thời gian, số dòng | DATA_SOURCES.md; manifest URL/SHA-256/kiểu cột; 121.253 dòng, 31.455 đơn; MIT license Microsoft |
| Làm sạch thiếu/trùng, ngày và ngoại lệ, trước–sau | clean_source; quality JSON/CSV; mẫu trước–sau hai fact; cách ly và kiểm tra khóa. Không loại giao dịch lỗ |
| Spark SQL tổng hợp và phân khúc | Bốn SQL trong sql/retail; đầu ra spark_monthly/region/category/customer_segments |
| Ít nhất ba ca kiểm thử | Kiểm thử tiền, discount, FK/grain, dòng trùng, tháng thiếu, nguồn cửa hàng, bộ lọc, CSV, Spark thực, PDF và đóng gói |
| Baseline pandas so Spark SQL cùng dữ liệu | Ba truy vấn, cùng Parquet và cột, 3 lượt/công cụ; kiểm tra chính xác từng nhóm, log môi trường và JVM startup riêng |
| Giới hạn hệ thống và quy mô | Báo cáo đúng quy mô local; thử tải 5× ghi rõ là bản sao; không gọi đây là chứng minh xử lý Big Data phân tán |
| KPI doanh thu thuần, biên lợi nhuận, tăng trưởng tháng | Công thức/đơn vị/phạm vi/giá trị thực trong README, báo cáo và dashboard. Không trừ discount hai lần, không lấy trung bình margin dòng |
| Dashboard có bộ lọc kênh, vùng, sản phẩm | Bốn trang; bộ lọc ngày/kỳ chung/kênh/vùng/danh mục/đại lý/sản phẩm và reset; các chỉ số/bảng/CSV cùng scope |
| Ba nhận xét theo số liệu và quyết định có điều kiện | Dashboard Tổng quan; báo cáo bảng hành động/chi phí/rủi ro/điều kiện; không suy ra lợi nhuận ròng từ lợi nhuận gộp |
| Mã, README tái lập, mẫu dữ liệu, PDF, demo | Được đưa vào nhánh và ZIP; dữ liệu raw có sẵn trong repo được tái sử dụng; mẫu mart thể hiện cả hai kênh |
| Log chạy pipeline và minh chứng chất lượng | Mỗi run có pipeline.log thực thi; output/evidence chứa pipeline.log, test_status, log kiểm thử, CSV và manifest |
| URL repository | https://github.com/winter-1402/RetailInsight-Multi-Channel-Revenue-and-Profit-Analytics |

## Các điểm chưa thể tự xác nhận thay sinh viên

1. **Ảnh dashboard:** cần ảnh chụp giao diện thật theo yêu cầu minh chứng. Công cụ điều khiển trình duyệt trên Windows dừng do không xác định chắc URL; hồ sơ không dùng biểu đồ dữ liệu hoặc ảnh dựng để giả làm ảnh dashboard. Các kiểm thử AppTest đã thực thi ứng dụng và biểu đồ. Bổ sung ảnh khi demo trực tiếp nếu công cụ chưa lưu được.
2. **Phân công/đóng góp cá nhân:** chưa ghi tên và tỷ lệ vì người dùng đã yêu cầu bỏ qua khâu này; không tự suy đoán. Nếu giảng viên yêu cầu trong bản nộp cuối, nhóm tự xác nhận đóng góp thực tế.
3. **Liêm chính học thuật:** đã khai báo AI. Điều kiện đề bài “không nộp sản phẩm được AI tạo toàn bộ hoặc phần lớn” cần sinh viên tự đáp ứng qua việc hiểu, chỉnh sửa và đóng góp; số test đạt không chứng minh điều kiện này.
4. **CI trên GitHub:** chỉ kết luận sau khi workflow chạy thực tế cho đúng commit được push. Không ghi CI đạt trước khi có kết quả.

Các yêu cầu kỹ thuật đã có mã và bằng chứng tái lập. Chưa khẳng định hồ sơ đáp ứng 100% điều kiện nộp bài khi các mục cần xác nhận trực tiếp ở trên chưa hoàn thành.

# Phương pháp kiểm chứng

## Dữ liệu và công thức

- Nguồn Microsoft được ghim commit; từng CSV có URL, SHA-256, schema và số byte trong manifest.
- Hai fact có tổng 121.253 dòng; kiểm tra `line_id` duy nhất và ghép chiều nhiều-một.
- Doanh thu/giá vốn/lợi nhuận dùng số nguyên 1/10.000 USD; đối chiếu nguồn bằng số thập phân.
- SalesAmount đã trừ DiscountAmount. DiscountAmount là FLOAT trong nguồn; kiểm tra gross−discount−net cho phép sai số 0,0001 USD/dòng.
- Tiền âm, ngày lỗi, số lượng sai được cách ly; trùng khóa xung đột hoặc FK thiếu làm dừng nạp. Không loại lợi nhuận âm.

## Kiểm thử tự động

`python -m pytest -q` chạy toàn bộ test. `python -m retail_bi.delivery --verify` lưu stdout/stderr thực và mã thoát vào `output/evidence/tests.log` và `test_status.json`.

| File | Phạm vi |
|---|---|
| test_retail.py | Độ chính xác tiền, chiết khấu, chất lượng, margin, calendar, grain, FK và công bố run |
| test_analytics.py | Cặp tháng đủ phạm vi, tháng trống, mẫu số 0, lọc bao gồm cuối ngày, tổng hợp, CSV và định dạng Việt |
| test_dashboard.py | Giá trị toàn kỳ, chọn kênh, kỳ tăng trưởng từng kênh, sản phẩm liên kết, reset, rỗng, ngày đảo, giao dịch lỗ |
| test_benchmark.py | Spark SQL thực khớp fixture tính tay cho cả ba workload |
| test_report.py | PDF/Markdown chứa số liệu thực, tính chất giả lập và kỳ so sánh đúng |
| test_delivery.py | ZIP có entrypoint/theme/CI/PDF, không chứa dữ liệu thô, bytecode, môi trường hoặc mã cũ |

AppTest thực thi ứng dụng và các biểu đồ/bảng nhưng không thay thế kiểm tra bằng mắt. Trang Tổng quan đã được quan sát trực tiếp trên Chrome ở khung rộng; thao tác trình duyệt tự động sau đó dừng vì không xác minh chắc URL trên Windows. Không có ảnh giao diện giả được đưa vào hồ sơ. Hình README/PDF là biểu đồ tổng hợp dữ liệu được ghi nhãn rõ.

## Benchmark

Cùng Parquet, cột và phép tổng hợp; mốc đo gồm đọc, groupby/distinct, sort và collect. Ba lần cho mỗi engine/truy vấn, thứ tự luân phiên. Lần pandas đầu được đo và làm tham chiếu; không có lượt warm-up pandas bị giấu. Khởi động JVM ghi riêng, cache OS không xóa và không loại lần đầu. Kiểm tra từng nhóm với `assert_frame_equal`, không chỉ kiểm tra tổng tiền.

Tải 5× là bản sao 606.265 dòng, mã đơn/người mua có hậu tố từng bản sao. Không trộn dữ liệu này với dashboard kinh doanh. Chưa kiểm tra cụm phân tán, giới hạn bộ nhớ cực đại hoặc ngưỡng Spark vượt pandas.

## Lưu ý môi trường

Windows có thể in cảnh báo native Hadoop và `ERROR: Access denied` lúc dọn tiến trình Spark, trong khi test và mã thoát Python vẫn thành công. Giữ nguyên log và xem đồng thời mã thoát, kết quả đối chiếu và file đầu ra; không che stack trace/failure thật. Không yêu cầu tải winutils từ nguồn không chính thức.

Kiểm tra GitHub Actions trên đúng commit sau khi push. Kết quả local không thay thế kết quả CI; không dùng badge CI “đạt” trước khi workflow chạy thực tế.

## Bổ sung trong nhánh rà soát

Kiểm tra DimReseller nhiều-một, mã cửa hàng thiếu đúng nghĩa ở Internet, bộ lọc đại lý và reset. Mẫu bán hàng giữ 10 dòng mỗi kênh; mỗi run có pipeline.log thực thi. Pytest dùng `.pytest-tmp` để không phụ thuộc thư mục cache đã có trên máy.

# Quy trình phát triển và phát hành

[Repository RetailInsight](https://github.com/winter-1402/RetailInsight-Multi-Channel-Revenue-and-Profit-Analytics). Nhánh triển khai: `feat/assignment-completion-20261116`. Thay đổi được phát triển trên nhánh riêng và kiểm tra trước khi tích hợp.

## Bộ hồ sơ

`python -m retail_bi.delivery --verify --package` lưu log kiểm thử, xuất minh chứng từ run hiện hành và tạo `output/AdventureWorks_Retail_BI_GitHub.zip`.

ZIP gồm mã nguồn, SQL, test, giao diện/theme, README, tài liệu, giấy phép, workflow CI, báo cáo PDF và dữ liệu mẫu/minh chứng. ZIP loại `data/`, `.venv/`, `.cache/`, `.git/`, bytecode và tài liệu ngoài phạm vi dự án. Repository vẫn giữ CSV nguồn đã commit; nội dung ZIP tải lại bằng script.

## Kiểm tra trước khi xuất bản

1. Chạy pipeline, benchmark, kiểm thử và báo cáo. Kiểm tra `output/evidence/test_status.json` có `exit_code = 0`.
2. Xem toàn bộ báo cáo PDF; chạy dashboard và kiểm tra phạm vi số liệu. Hình trong README là biểu đồ dữ liệu; không gọi là ảnh UI.
3. Kiểm tra không có `.env`, khóa/API token, dữ liệu cá nhân, môi trường ảo hoặc tài liệu không được phép tái phát hành.
4. Đọc LICENSE, THIRD_PARTY_NOTICES và AI_USAGE; giữ thông báo nguồn và tuân thủ giấy phép khi phân phối.
5. Xem workflow **Verify pipeline and dashboard** trong tab Actions cho đúng commit sau khi push. CI chỉ dùng nguồn công khai, quyền đọc repository và không deploy. Kết quả local không thay thế kết quả CI.

## Làm việc theo nhánh

Các thay đổi tiếp theo cần có commit rõ mục đích và được review trước khi merge. Không push trực tiếp vào main hoặc ghi đè lịch sử.

```bash
git switch -c ten-nhanh-cong-viec
git status --short
git add .
git diff --cached --stat
git commit -m "Describe the change"
```

Clone repository ở trên và checkout nhánh triển khai để chạy ứng dụng. Nếu dùng ZIP, giải nén trước, tạo môi trường và tải nguồn theo README. Xem trạng thái kiểm chứng tại [COMPLIANCE_REVIEW.md](COMPLIANCE_REVIEW.md).

# Mây Mart — Website bán hàng trực tuyến (Flask + SQLite)

Mây Mart là dự án thương mại điện tử mẫu bằng Python Flask, giao diện tiếng Việt, có thể chạy trên máy tính cá nhân và hiển thị thích ứng trên điện thoại. Dữ liệu sản phẩm, tài khoản, đánh giá và đơn hàng được lưu vào cơ sở dữ liệu SQLite tự tạo trong thư mục `instance/`.

> **Phạm vi dự án:** Đây là bản MVP/đồ án học tập có luồng mua hàng hoạt động trên máy local. Dự án không thể đạt quy mô, hệ thống chống gian lận, hạ tầng tải lớn hay dịch vụ hậu cần của Shopee chỉ bằng mã nguồn mẫu này. Chưa tích hợp cổng thanh toán thật, API đơn vị vận chuyển, email/SMS, xác thực OTP, tải ảnh lên máy chủ, quản lý biến thể SKU hoặc hệ thống phân tán.

## Chức năng đã có

### Dành cho khách hàng
- Trang chủ nhiều khu vực, danh mục sản phẩm, ưu đãi và sản phẩm nổi bật.
- Tìm kiếm theo tên/mô tả/danh mục; lọc danh mục; sắp xếp theo giá, tên và sản phẩm mới.
- Trang chi tiết sản phẩm với giá, giá gốc, tồn kho, mô tả, đánh giá và sản phẩm liên quan.
- Tạo tài khoản, đăng nhập/đăng xuất, lưu hồ sơ và địa chỉ mặc định.
- Giỏ hàng: thêm/xóa/cập nhật số lượng, kiểm tra tồn kho, tính tạm tính/phí giao hàng/tổng tiền.
- Mã ưu đãi mẫu: `WELCOME10`, `FREESHIP`, `SAVE50K`.
- Đặt hàng với COD hoặc lựa chọn chuyển khoản (chỉ lưu lựa chọn trong bản demo; chưa xử lý thanh toán thật).
- Xem chi tiết đơn hàng, theo dõi trạng thái và hủy đơn khi đơn còn chờ xác nhận.
- Danh sách yêu thích.
- Đánh giá sản phẩm sau khi đơn hàng được cập nhật là “Đã giao hàng” hoặc “Hoàn thành”; mỗi tài khoản có thể cập nhật một đánh giá cho mỗi sản phẩm.

### Dành cho quản trị viên
- Bảng tổng quan sản phẩm, đơn hàng, khách hàng, doanh thu đơn đã hoàn tất và tồn kho thấp.
- Thêm/sửa/ẩn-hiện sản phẩm; cập nhật giá, giá gốc, danh mục, ảnh bằng URL và số lượng tồn kho.
- Tìm nhanh trong bảng sản phẩm.
- Xem, lọc đơn hàng theo trạng thái; xem địa chỉ và sản phẩm trong đơn; cập nhật trạng thái giao hàng.
- Khi hủy đơn từ trang quản trị, số lượng sản phẩm trong đơn được cộng lại vào tồn kho.
- Mật khẩu lưu dưới dạng hash; có kiểm tra CSRF cho biểu mẫu POST, kiểm tra quyền admin, truy vấn SQL có tham số và kiểm tra tồn kho khi tạo đơn.

## Cách chạy trên Windows (người mới bắt đầu)

**Bước 1 — Giải nén dự án**

Giải nén `OnlineShopVN.zip` vào thư mục dễ tìm, ví dụ `C:\Users\<Tên của bạn>\Downloads\OnlineShopVN`.

**Bước 2 — Mở thư mục bằng VS Code**

Mở Visual Studio Code → chọn **File → Open Folder...** → chọn thư mục `OnlineShopVN` (thư mục có file `app.py`).

**Bước 3 — Mở Terminal**

Trong VS Code chọn **Terminal → New Terminal**. Terminal cần đang ở thư mục dự án. Kiểm tra bằng lệnh:

```powershell
 dir
```

Trong kết quả cần thấy `app.py`, `requirements.txt`, `templates` và `static`.

**Bước 4 — Tạo môi trường Python riêng**

```powershell
py -m venv .venv
```

Nếu lệnh `py` không có, thử `python -m venv .venv`.

**Bước 5 — Cài thư viện**

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Máy cần Internet ở bước này để tải Flask. Nếu có lỗi `No module named flask`, hãy chạy lại lệnh cài thư viện bằng đúng Python trong thư mục `.venv` như trên.

**Bước 6 — Chạy website**

```powershell
.\.venv\Scripts\python.exe app.py
```

Mở trình duyệt tại **http://127.0.0.1:5000**. Để dừng máy chủ, quay về Terminal và nhấn `Ctrl + C`.

> Có thể chạy `start_windows.bat` bằng cách nhấp đúp; file sẽ tạo môi trường `.venv`, cài thư viện nếu chưa có và khởi chạy website. Máy vẫn cần Internet khi cài Flask lần đầu.

## Tài khoản thử nghiệm

- **Quản trị viên**: `admin@shopdemo.vn`
- **Mật khẩu demo**: `Admin@123`
- Khách hàng: vào **Đăng ký** để tự tạo tài khoản.

Hãy đổi mật khẩu demo và `SECRET_KEY` trước khi triển khai ra Internet. Tài khoản quản trị mặc định chỉ nhằm giúp bạn dễ kiểm thử dự án local.

## Đường dẫn chính

- `/` — Trang chủ
- `/san-pham` — Danh mục và tìm kiếm
- `/gio-hang` — Giỏ hàng
- `/thanh-toan` — Thanh toán / tạo đơn
- `/dang-ky`, `/dang-nhap` — Tài khoản
- `/don-hang` — Đơn hàng của khách
- `/yeu-thich` — Danh sách yêu thích
- `/quan-tri` — Bảng điều khiển admin
- `/quan-tri/san-pham` — Quản lý sản phẩm
- `/quan-tri/don-hang` — Quản lý đơn hàng

## Tùy chỉnh nội dung

- **Sản phẩm mẫu**: sửa danh sách `PRODUCT_SEEDS` trong `app.py`.
- **Danh mục**: sửa `CATEGORIES` trong `app.py`.
- **Mã giảm giá/phí vận chuyển**: sửa `COUPONS`, `SHIPPING_FEE` và `FREE_SHIP_THRESHOLD` trong `app.py`.
- **Màu sắc và bố cục**: sửa `static/css/style.css`.
- **Trang chủ**: sửa `templates/index.html`.
- **Ảnh sản phẩm**: dùng URL ảnh hợp pháp, tốt nhất là HTTPS; trang quản trị có trường URL ảnh.

## Bảo mật và đưa lên Internet

Đừng dùng cấu hình phát triển mặc định cho website công khai. Trước khi triển khai thực tế, cần đặt `SECRET_KEY` ngẫu nhiên, tắt debug (`FLASK_DEBUG=0`), dùng HTTPS, có quy trình sao lưu/khôi phục CSDL, giới hạn đăng nhập và theo dõi lỗi, kiểm tra bảo mật, chính sách quyền riêng tư/đổi trả, tích hợp cổng thanh toán hợp pháp và API vận chuyển. SQLite phù hợp cho demo/website nhỏ; cần đánh giá lại CSDL, máy chủ WSGI và kiến trúc trước khi tăng tải. Không lưu thông tin thẻ thanh toán trong ứng dụng.

## Cấu trúc thư mục

```text
OnlineShopVN/
├── app.py
├── requirements.txt
├── start_windows.bat
├── README.md
├── .env.example
├── .gitignore
├── instance/             # shop.db được tự tạo khi chạy
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── index.html
    ├── catalog.html
    ├── product_detail.html
    ├── cart.html
    ├── checkout.html
    ├── auth.html
    ├── account.html
    ├── wishlist.html
    ├── orders.html
    ├── order_detail.html
    └── admin/
```

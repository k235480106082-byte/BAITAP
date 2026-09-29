# BÁO CÁO — MÔN LẬP TRÌNH WEB

| Thông tin | Nội dung |
|---|---|
| **Sinh viên** | Nguyễn Văn Mạnh — MSSV K235480106082 |
| **Lớp** | 59KMT |
| **Giảng viên** | Đỗ Duy Cốp |
| **Bài tập** | Bài 1 (Docker Compose, 2 website/2 domain) và Bài 2 (API Node-RED + JS) |

---

## Yêu cầu đề bài

**Bài 1:**
1. Giả lập Linux OS (Hyper-V, VirtualBox, VMware hoặc WSL).
2. Cài Docker Compose trên OS đó.
3. Cài trên Docker Compose các dịch vụ: nginx, nodered, mariadb, phpmyadmin, cloudflared (cần domain xịn).
4. Cấu hình Nginx chạy được 2 website với 2 domain khác nhau.

**Bài 2:**
1. Dùng Node-RED với node `http_in` + `http_response` để tạo API đơn giản.
2. Cấu hình Nginx để web dùng JS gọi được API trên Node-RED; thuật toán cho API tự nghĩ.
3. Code JS vào trang HTML để gọi được API.

---

## BÀI 1 — Docker Compose & 2 website / 2 domain

### Môi trường thực hiện

Phần mềm giả lập Linux được chọn là **WSL2** (Windows Subsystem for Linux 2) trên Windows 11,
với Ubuntu 26.04 LTS chạy trong WSL2 kernel 6.18. Đây là lựa chọn gọn nhất vì Docker Desktop
sẵn sàng dùng WSL2 làm backend, không cần tạo máy ảo riêng. Docker Engine 29.8.0 và
Docker Compose v5.5.1 được cài và hoạt động bình thường.

### Các dịch vụ trong docker-compose.yml

Toàn bộ 5 dịch vụ nằm trong một file `docker-compose.yml`, giao tiếp qua network bridge
`web-bt1-network`, dữ liệu bền vững qua named volume:

| Dịch vụ | Image | Vai trò | Port |
|---|---|---|---|
| nginx | `nginx:alpine` | Reverse proxy, serve static 2 website | 80 → 80 |
| nodered | `nodered/node-red:latest` | Flow engine | 1880 → 1880 |
| mariadb | `mariadb:11` | Database `web_lab` | nội bộ (không expose) |
| phpmyadmin | `phpmyadmin/phpmyadmin:latest` | Web UI quản lý DB | nội bộ (qua proxy) |
| cloudflared | `cloudflare/cloudflared:latest` | Cloudflare Tunnel ra Internet | không cần port |

Điểm chú ý về cấu hình bảo mật: MariaDB chỉ mở port 3306 trong network nội bộ, phpMyAdmin
không expose port ra host mà chỉ truy cập qua Nginx proxy. Mật khẩu database và Cloudflare
Tunnel Token nằm trong file `.env` (đã khai báo trong `.gitignore`, không được đẩy lên Git).

### Cấu hình Nginx chạy 2 website với 2 domain khác nhau

Nginx phân luồng request theo header `Host` thông qua nhiều `server block` trong file
`nginx/conf.d/default.conf`. Hai website chính được khai báo:

- `web1.nguyenmanh05.id.vn` → thư mục gốc `/var/www/website1` (Student Portal)
- `web2.nguyenmanh05.id.vn` → thư mục gốc `/var/www/website2` (Technology Hub)

Ngoài ra còn có các block cho `phpmyadmin.local` (proxy tới service phpmyadmin),
`nodered.local` (proxy websocket tới Node-RED) và một `default_server` để truy cập
trực tiếp qua IP không rơi vào trạng thái 404.

Khi request đến, Nginx đọc `Host` header, tìm `server_name` khớp và trả về file tĩnh
trong thư mục tương ứng hoặc chuyển tiếp tới service qua `proxy_pass`. Kiểm thử bằng lệnh
`curl -H "Host: web1.nguyenmanh05.id.vn" http://localhost` trả về HTML Student Portal,
tương tự web2 trả về Technology Hub, cả hai đều HTTP 200.

### Domain thật và Cloudflare Tunnel (không cần mở port router)

Yêu cầu đề bài ghi "cần domain xịn" nên hệ thống dùng domain thật
`nguyenmanh05.id.vn` quản lý trên Cloudflare. Máy tính cá nhân nằm sau router gia đình
không mở được port forwarding, vì vậy thay vì trỏ DNS thẳng về IP nhà, hai subdomain
được cấu hình làm **Public Hostname** của Cloudflare Tunnel:

- Cloudflare tạo record DNS cho `web1` và `web2` trỏ về hệ thống tunnel của Cloudflare.
- Container `cloudflared` kết nối Cloudflare bằng Tunnel Token (lưu trong `.env`) qua giao thức QUIC, chủ động ra ngoài nên không cần mở bất kỳ port nào trên router.
- Traffic từ Internet đi: trình duyệt → Cloudflare edge → tunnel → container `nginx:80` → website tương ứng theo `Host`.

Hai container cloudflared chạy song song, mỗi container một tunnel token cho một domain.
Kết quả kiểm thử: cả hai URL trả HTTP 200 qua HTTPS (chứng chỉ miễn phí tự động của
Cloudflare), kiểm thử từ nhiều node quốc tế (Áo, Brazil, Ấn Độ, Nga, Mỹ, Bồ Đào Nha...)
đều thành công với thời gian phản hồi dưới 2 giây.

### Kiểm thử hệ thống

Tất cả container khởi động ổn định với `restart: unless-stopped`:

- `docker compose config` validate cấu hình thành công.
- `nginx -t` xác nhận file cấu hình hợp lệ.
- `curl` với `Host: web1...` và `Host: web2...` trả HTTP 200 kèm đúng nội dung từng website.
- phpMyAdmin kết nối MariaDB thành công qua `webuser`.
- Node-RED khởi động healthy với flow demo.
- Docker Desktop được bật tự khởi động cùng Windows, toàn bộ stack tự chạy lại sau khi reboot.

---

## BÀI 2 — API Node-RED + Nginx reverse proxy + JS

### Kiến trúc

```text
Trình duyệt (HTML/CSS/JS)
        │  fetch("/api/...")
        ▼
Nginx :8080  ── location /api/ ──►  Node-RED :1880  (http in → function → http response)
        │
        └── location /  ──►  file tĩnh (index.html, style.css, script.js)
```

### Bước 1 — Tạo API bằng node HTTP In + HTTP Response

Trong Node-RED có tab "API Students & Rank" với 2 flow, mỗi flow đúng cấu trúc
`http in` → `function` → `http response` theo yêu cầu đề bài:

**API 1 — `GET /api/students`**: node `http in` nhận request, node function trả về
JSON danh sách sinh viên, node `http response` gửi đi với mã 200 và header
`Content-Type: application/json; charset=utf-8`. Kết quả trả về:

```json
{"ok":1,"msg":"Thành công","students":[{"id":1,"name":"Nguyễn Văn An","class":"K59 KMT.K01","score":8.5}]}
```

**API 2 — `GET /api/rank?score=X`** — đây là phần "thuật toán tự nghĩ" theo đề bài:
xếp loại điểm của sinh viên trên thang điểm 10.

- Thuật toán: điểm ≥ 8.5 → "Giỏi", ≥ 7.0 → "Khá", ≥ 5.0 → "Trung bình", < 5.0 → "Yếu".
- Validate đầy đủ trong node function, lỗi trả HTTP 400 kèm mã lỗi:
  thiếu `score` → `MISSING_SCORE`, không phải số → `INVALID_SCORE`,
  nhỏ hơn 0 → `SCORE_TOO_LOW`, lớn hơn 10 → `SCORE_TOO_HIGH`.
- Thành công trả `{"ok":1,"msg":"Thành công","score":6.5,"rank":"Trung bình"}`.

Kiểm thử thực tế: `score=8.5` → "Giỏi", `score=6.5` → "Trung bình", `score=11` →
400 `SCORE_TOO_HIGH`, `score=abc` → 400 `INVALID_SCORE` — tất cả đúng như thiết kế.

### Bước 2 — Cấu hình Nginx reverse proxy

File `nginx/conf.d/default.conf` khai báo:

- `location /` phục vụ file tĩnh từ `/var/www/web` (frontend).
- `location /api/` chuyển tiếp qua `proxy_pass http://nodered:1880`, kèm các header
  `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

Nhờ vậy trình duyệt chỉ gọi cùng origin `localhost:8080/api/...` nên không phát sinh
lỗi CORS, request đi qua Nginx đến Node-RED và quay lại minh bạch.

### Bước 3 — Code JS vào trang HTML gọi API

File `web/index.html` nhúng `script.js`, trong đó:

- Khai báo `const API_BASE = '/api'`.
- Hàm `fetchStudents()` dùng `fetch(API_BASE + '/students')`, xử lý response JSON,
  render bảng danh sách sinh viên và hiển thị JSON thô; có trạng thái loading và xử lý lỗi.
- Hàm `fetchRank()` dùng `fetch(API_BASE + '/rank?score=' + ...)`, nhận kết quả xếp loại
  và hiển thị card màu theo loại; hiển thị thông báo lỗi từ API khi validate thất bại.
- Tự động gọi `fetchStudents()` ngay khi trang tải xong, có nút bấm và phím Enter để gọi API rank.

### Kiểm thử Bài 2

- `docker compose config` hợp lệ, container nginx và nodered chạy ổn định (nodered healthy).
- `GET http://localhost:8080/api/students` trả JSON đúng cấu trúc.
- `GET http://localhost:8080/api/rank?score=8.5` trả `rank: "Giỏi"`.
- Các trường hợp lỗi trả đúng mã 400 và mã lỗi tương ứng.
- Trang frontend tải tại `http://localhost:8080`, JS gọi API và hiển thị dữ liệu thành công.

---

## Kết luận

Cả 2 bài tập đều đáp ứng yêu cầu đề bài: hệ thống Docker Compose đủ 5 dịch vụ với
Nginx phục vụ 2 website trên 2 domain thật khác nhau qua Cloudflare Tunnel
(không cần mở port router), và API Node-RED đúng chuẩn `http in` + `http response`
được truy cập qua Nginx reverse proxy từ JavaScript trong trang HTML.

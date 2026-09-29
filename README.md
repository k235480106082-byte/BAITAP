# BÁO CÁO BÀI TẬP VỀ NHÀ — TỔNG HỢP 2 MÔN

| Thông tin | Nội dung |
|---|---|
| **Môn học** | Lập trình Web **+** An toàn và Bảo mật Thông tin |
| **Lớp** | 59KMT |
| **Giảng viên hướng dẫn** | Đỗ Duy Cốp |
| **Sinh viên thực hiện** | Nguyễn Văn Mạnh |
| **MSSV** | K235480106082 |
| **Deadline** | 23h59 ngày 28/9/2026 |
| **Hình thức** | Push lên GitHub (public) |

---

## 1. Giới thiệu

Repository này tổng hợp bài tập về nhà của 2 môn: **Lập trình Web** và **An toàn và Bảo mật Thông tin**.
Mỗi môn nằm trong một thư mục riêng, có báo cáo README đầy đủ mô tả yêu cầu, cách thực hiện,
cấu hình và kết quả kiểm thử — viết hoàn toàn bằng lời, không dùng ảnh chụp màn hình.

## 2. Mục lục

| Thư mục | Môn học | Nội dung chính | Báo cáo |
|---|---|---|---|
| [`BAITAP_LTW/`](BAITAP_LTW/) | Lập trình Web | Docker Compose 5 dịch vụ, 2 website / 2 domain thật qua Cloudflare Tunnel, API Node-RED + JS | [README](BAITAP_LTW/README.md) |
| [`BAITAP_ATTT/`](BAITAP_ATTT/) | An toàn và Bảo mật Thông tin | DES/AES (cài đặt AES bằng Python), RSA (sinh khóa), 3 mô hình xác thực, so sánh RSA–AES, kết hợp RSA+AES | [README](BAITAP_ATTT/README.md) |

## 3. Cấu trúc thư mục

```text
BAITAP/
├── README.md                     # báo cáo tổng hợp (file này)
├── BAITAP_LTW/                   # Môn Lập trình Web
│   ├── README.md                 # báo cáo chi tiết môn LTW
│   ├── bt01_docker-compose/      # Bài 1: Docker Compose + 2 website / 2 domain
│   │   ├── docker-compose.yml
│   │   ├── nginx/conf.d/
│   │   ├── website1/  website2/
│   │   ├── nodered/  cloudflared/
│   │   └── README.md
│   └── bt02_nodered-api/         # Bài 2: API Node-RED + JS gọi API
│       ├── docker-compose.yml
│       ├── nginx/conf.d/
│       ├── nodered/flows.json
│       ├── web/                  # frontend HTML/CSS/JS
│       └── README.md
└── BAITAP_ATTT/                  # Môn An toàn và Bảo mật Thông tin
    ├── README.md                 # báo cáo chi tiết môn ATTT
    ├── docs/                     # DES, AES, RSA, AUTHENTICATION, BENCHMARK, HYBRID
    ├── src/                      # code Python (aes, rsa, auth, benchmark, hybrid)
    ├── tests/                    # 49 unit tests
    └── requirements.txt
```

## 4. Cách chạy (tóm tắt)

**Môn Lập trình Web — dựng hệ thống Docker (yêu cầu Docker Desktop + WSL2):**

```bash
cd BAITAP_LTW/bt01_docker-compose
cp .env.example .env              # điền mật khẩu DB + Cloudflare Tunnel Token
docker compose --profile tunnel up -d
# Web 1: https://web1.nguyenmanh05.id.vn
# Web 2: https://web2.nguyenmanh05.id.vn

cd ../bt02_nodered-api
docker compose up -d
# Frontend + API: http://localhost:8080
```

**Môn An toàn và Bảo mật — chạy các demo mã hóa:**

```bash
cd BAITAP_ATTT
pip install -r requirements.txt
python -m unittest discover -s tests -v     # 49 tests
python src/main.py                          # CLI demo toàn bộ thuật toán
```

## 5. Tiến độ

- [x] Môn Lập trình Web — Bài 1: giả lập Linux (WSL2), Docker Compose, 5 dịch vụ (nginx, Node-RED, MariaDB, phpMyAdmin, cloudflared), cấu hình Nginx chạy 2 website với 2 domain khác nhau
- [x] Môn Lập trình Web — Bài 2: API Node-RED bằng node HTTP In + HTTP Response, Nginx reverse proxy, frontend JS gọi API
- [x] Môn An toàn & Bảo mật — DES và AES: mô tả thuật toán, quy trình mã hóa/giải mã, cài đặt AES bằng Python
- [x] Môn An toàn & Bảo mật — RSA: nguyên lý sinh cặp khóa bí mật/công khai
- [x] Môn An toàn & Bảo mật — 3 mô hình xác thực RSA, so sánh thời gian RSA với AES, kết hợp RSA + AES
- [x] Báo cáo README cho từng môn (viết bằng lời, không ảnh)

## 6. Kết quả nổi bật

| Môn | Kết quả |
|---|---|
| Lập trình Web | 2 website chạy công khai tại `web1.nguyenmanh05.id.vn` và `web2.nguyenmanh05.id.vn` (HTTPS miễn phí qua Cloudflare Tunnel, không cần mở port router); API `/api/students` và `/api/rank` hoạt động, validation đầy đủ |
| An toàn & Bảo mật | 49/49 unit tests PASS; benchmark đo được AES nhanh hơn RSA khoảng 200–1000 lần tùy thao tác; hybrid RSA+AES hoạt động đúng (RSA bảo vệ khóa, AES bảo vệ dữ liệu) |

---
*Báo cáo được thực hiện bởi Nguyễn Văn Mạnh — MSSV: K235480106082 — Lớp 59KMT.*

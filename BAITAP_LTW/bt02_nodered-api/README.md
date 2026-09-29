# Bài Tập 2 - Lập Trình Web: Node-RED API + Nginx Reverse Proxy

## 1. Mục Tiêu Bài Tập

- Xây dựng 2 API RESTful bằng Node-RED:
  - `GET /api/students` - Trả về danh sách sinh viên
  - `GET /api/rank?score=X` - Xếp loại điểm theo thang điểm 10
- Cấu hình Nginx làm reverse proxy cho các API endpoint
- Tạo frontend thuần (HTML/CSS/JS) gọi API và hiển thị kết quả
- Triển khai bằng Docker Compose (nginx + nodered)

---

## 2. Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Port 80)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /          → Static files (web/index.html, css, js)    │   │
│  │  /api/*    → Proxy to Node-RED:1880                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NODE-RED (Port 1880)                         │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │ GET /api/students│  │ GET /api/rank?score=X              │  │
│  │ HTTP In → Func   │  │ HTTP In → Func (validation) → Resp │  │
│  │ → HTTP Response  │  │ → HTTP Response                    │  │
│  └──────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Docker Network:** `web-bt2-network` (bridge)

**Volume:** `web-bt2-nodered-data` → `/data` (bền vững flows)

---

## 3. API Specification

### 3.1 GET /api/students

**Response:**
```json
{
  "ok": 1,
  "msg": "Thành công",
  "students": [
    { "id": 1, "name": "Nguyễn Văn An", "class": "K59 KMT.K01", "score": 8.5 },
    { "id": 2, "name": "Trần Thị Bình", "class": "K59 KMT.K01", "score": 7.5 },
    { "id": 3, "name": "David", "class": "K59 KMT.K02", "score": 9.0 }
  ]
}
```

**Headers:** `Content-Type: application/json; charset=utf-8`

---

### 3.2 GET /api/rank?score=X

**Query Parameter:** `score` (number, 0-10)

**Validation:**
| Trường hợp | Status | Error Code |
|------------|--------|------------|
| Thiếu `score` | 400 | MISSING_SCORE |
| Không phải số | 400 | INVALID_SCORE |
| score < 0 | 400 | SCORE_TOO_LOW |
| score > 10 | 400 | SCORE_TOO_HIGH |

**Thuật toán xếp loại:**
| Điểm | Xếp loại |
|------|----------|
| ≥ 8.5 | Giỏi |
| ≥ 7.0 | Khá |
| ≥ 5.0 | Trung bình |
| < 5.0 | Yếu |

**Response thành công (200):**
```json
{
  "ok": 1,
  "msg": "Thành công",
  "score": 8.5,
  "rank": "Giỏi"
}
```

**Response lỗi (400):**
```json
{
  "ok": 0,
  "msg": "Score không được lớn hơn 10",
  "error": "SCORE_TOO_HIGH"
}
```

---

## 4. Cấu Trúc Thư Mục

```
WEB-BT2/
├── docker-compose.yml          # 2 services: nginx, nodered
├── .env.example                # Template biến môi trường
├── .gitignore                  # Loại trừ secret, volume, log
├── README.md                   # File này
├── nginx/
│   └── conf.d/
│       └── default.conf        # Reverse proxy /api/* → nodered:1880
├── nodered/
│   └── flows.json              # 2 API flows (students, rank)
└── web/
    ├── index.html              # Frontend demo
    ├── style.css               # Styling responsive
    └── script.js               # Fetch API, hiển thị, validation
```

---

## 5. Cách Khởi Động

### 5.1 Yêu Cầu
- Docker Desktop (WSL2 backend) đã chạy

### 5.2 Khởi Động
```bash
cd WEB-BT2

# Kiểm tra config
docker compose config

# Khởi động
docker compose up -d

# Xem trạng thái
docker compose ps
```

### 5.3 Truy Cập
- Frontend: http://localhost
- Node-RED Editor: http://localhost:1880
- API Students: http://localhost/api/students
- API Rank: http://localhost/api/rank?score=8.5

---

## 6. Kiểm Tra API

### 6.1 Test /api/students
```bash
curl http://localhost/api/students
# Hoặc qua Nginx proxy (đang chạy trên port 80)
curl -H "Host: localhost" http://localhost/api/students
```

### 6.2 Test /api/rank
```bash
# Thành công
curl "http://localhost/api/rank?score=8.5"
curl "http://localhost/api/rank?score=7.0"
curl "http://localhost/api/rank?score=5.0"
curl "http://localhost/api/rank?score=4.0"

# Validation errors
curl "http://localhost/api/rank"                    # missing score
curl "http://localhost/api/rank?score=abc"          # not a number
curl "http://localhost/api/rank?score=-1"           # < 0
curl "http://localhost/api/rank?score=11"           # > 10
```

---

## 7. Frontend Features

- **Gọi API /api/students**: Hiển thị bảng dữ liệu + JSON raw
- **Gọi API /api/rank**: Input điểm → Xếp loại → Hiển thị card màu theo loại
- **Loading state**: Spinner khi đang fetch
- **Error handling**: Hiển thị lỗi validation từ API
- **Responsive**: Desktop, tablet, mobile
- **JSON toggle**: Xem response gốc

---

## 8. Node-RED Flow Details

File: `nodered/flows.json`

**Tab: "API Students & Rank"**

### Flow 1: GET /api/students
```
[HTTP In: GET /api/students]
         ↓
[Function: Create Students Response]
         ↓
[HTTP Response: 200 OK + JSON]
```

### Flow 2: GET /api/rank
```
[HTTP In: GET /api/rank]
         ↓
[Function: Validate & Rank Score]
    ├── missing score → 400
    ├── not number → 400
    ├── < 0 → 400
    ├── > 10 → 400
    └── valid → rank logic
         ↓
[HTTP Response: 200/400 + JSON]
```

---

## 9. Nginx Configuration

File: `nginx/conf.d/default.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /var/www/web;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://nodered:1880;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 10. Các Lệnh Docker Hữu Ích

| Lệnh | Mô tả |
|------|-------|
| `docker compose config` | Validate config |
| `docker compose up -d` | Start background |
| `docker compose down` | Stop containers |
| `docker compose ps` | Status |
| `docker compose logs -f nodered` | Log Node-RED |
| `docker compose logs -f nginx` | Log Nginx |
| `docker compose restart nodered` | Restart Node-RED (reload flow) |
| `docker cp nodered/flows.json web-bt2-nodered:/data/flows.json` | Copy flow mới vào container |

---

## 11. Troubleshooting

| Vấn đề | Giải pháp |
|--------|-----------|
| API trả về 404 | Kiểm tra Nginx proxy_pass, Node-RED HTTP In URL |
| Flow không load | `docker cp` file flows.json → restart nodered |
| CORS error | Node-RED HTTP Response không set CORS header (đã có proxy) |
| Frontend không load | Kiểm tra volume mount `./web:/var/www/web` |

---

## 12. Bảo Mật & Best Practices

- ✅ Nginx làm entry point duy nhất (port 80)
- ✅ Node-RED không expose port 1880 ra ngoài (chỉ internal network)
- ✅ Validation đầy đủ ở Function node
- ✅ Error response chuẩn JSON
- ✅ Volume persistence cho Node-RED flows
- ✅ Healthcheck qua restart policy

---

## 13. Tác Giả & Nộp Bài

- **Môn học:** Lập Trình Web
- **Bài tập:** Bài Tập 2 - Node-RED REST API + Nginx Reverse Proxy
- **Môi trường:** Docker Compose (nginx + nodered)
- **Ngày hoàn thành:** 2026
# Bài Tập 1 - Lập Trình Web: Triển Khai Hệ Thống Container với Docker Compose

## 1. Mục Tiêu Bài Tập

- Triển khai môi trường giả lập Linux OS sử dụng WSL2 trên Windows 11
- Cài đặt và vận hành Docker + Docker Compose
- Sử dụng Docker Compose để triển khai 5 dịch vụ: Nginx, Node-RED, MariaDB, phpMyAdmin, Cloudflared
- Cấu hình Nginx làm reverse proxy phục vụ 2 website với 2 domain khác nhau
- Chứng minh hệ thống hoạt động ổn định, dữ liệu bền vững qua volume

---

## 2. Môi Trường Thực Hiện

| Thành phần | Phiên bản / Cấu hình |
|------------|---------------------|
| Hệ điều hành chính | Windows 11 Pro |
| Linux Environment | WSL2 - Ubuntu (Docker Desktop backend) |
| Docker Engine | 29.8.0 |
| Docker Compose | v5.5.1 (plugin) |
| Docker Desktop | 4.x (WSL2 backend) |

---

## 3. Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Port 80)                            │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │student.local│  │technology.local  │  │ phpmyadmin.local  │  │
│  │ Website 1   │  │ Website 2        │  │ phpMyAdmin Proxy  │  │
│  └─────────────┘  └──────────────────┘  └───────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   nodered.local (Port 1880)              │   │
│  │                      Node-RED Proxy                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   WEBSITE 1      │  │   WEBSITE 2      │  │    MARIADB       │
│   (Static HTML)  │  │   (Static HTML)  │  │   (Database)     │
│   /var/www/w1    │  │   /var/www/w2    │  │   web_lab DB     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────┐
                                         │   PHPMYADMIN     │
                                         │   (Web UI)       │
                                         └──────────────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────┐
                                         │   NODE-RED       │
                                         │   (Flow Engine)  │
                                         └──────────────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────┐
                                         │   CLOUDFLARED    │
                                         │   (Tunnel)       │
                                         └──────────────────┘
```

**Docker Network:** `web-bt1-network` (bridge) - tất cả service giao tiếp qua network này

**Volumes:**
- `web-bt1-mariadb-data` → `/var/lib/mysql` (bền vững dữ liệu MariaDB)
- `web-bt1-nodered-data` → `/data` (bền vững flows/config Node-RED)

---

## 4. Các Service Chi Tiết

### 4.1 Nginx (`nginx:alpine`)
- **Port:** 80 (host) → 80 (container)
- **Vai trò:** Entry point, Reverse Proxy, Static File Server
- **Virtual Hosts:**
  - `student.local` → `/var/www/website1` (Student Portal)
  - `technology.local` → `/var/www/website2` (Technology Hub)
  - `phpmyadmin.local` → proxy `http://phpmyadmin:80`
  - `nodered.local` → proxy `http://nodered:1880` (WebSocket support)
- **Config:** `nginx/conf.d/default.conf`
- **Security Headers:** X-Frame-Options, X-Content-Type-Options, X-XSS-Protection

### 4.2 Node-RED (`nodered/node-red:latest`)
- **Port:** 1880 (host) → 1880 (container)
- **Volume:** `nodered_data` → `/data`
- **Flow demo:** `nodered/flows.json` (Inject → Function → Debug)
- **Function output:** `{ok: 1, msg: "Node-RED hoạt động", time: ISO_string}`
- **Timezone:** Asia/Ho_Chi_Minh

### 4.3 MariaDB (`mariadb:11`)
- **Port:** 3306 (internal only)
- **Database:** `web_lab`
- **User:** `webuser`
- **Volume:** `mariadb_data` → `/var/lib/mysql`
- **Environment:** Mật khẩu từ `.env` (MARIADB_ROOT_PASSWORD, MARIADB_PASSWORD)
- **Timezone:** Asia/Ho_Chi_Minh

### 4.4 phpMyAdmin (`phpmyadmin/phpmyadmin:latest`)
- **Port:** 80 (internal only, truy cập qua Nginx proxy)
- **Kết nối MariaDB:** Host `mariadb`, User `webuser`
- **Upload limit:** 100M
- **Timezone:** Asia/Ho_Chi_Minh

### 4.5 Cloudflared (`cloudflare/cloudflared:latest`)
- **Profile:** `tunnel` (chỉ chạy khi `docker compose --profile tunnel up`)
- **Config mẫu:** `cloudflared/config.example.yml`
- **Authentication:** Tunnel Token (từ biến môi trường `CLOUDFLARE_TUNNEL_TOKEN`)
- **Ingress:** Route hostname về `nginx:80`, `nodered:1880`, `phpmyadmin:80`
- **Trạng thái:** **CONFIG READY** - cần domain thật + token Cloudflare để PUBLIC INTERNET

---

## 5. Hai Website & Hai Domain

### 5.1 Website 1: Student Portal (`student.local`)
- **Thư mục:** `website1/`
- **Files:** `index.html`, `style.css`, `script.js`
- **Nội dung:** Hệ thống thông tin sinh viên
  - Header + Navigation
  - Hero section: Thống kê (1200 SV, 1150 đang học, 50 tốt nghiệp)
  - Giới thiệu 4 tính năng: Quản lý hồ sơ, Điểm số, Đăng ký học phần, Thông báo
  - Features: Responsive, Bảo mật, Realtime, Xuất báo cáo
  - Footer: Liên kết, Liên hệ

### 5.2 Website 2: Technology Hub (`technology.local`)
- **Thư mục:** `website2/`
- **Files:** `index.html`, `style.css`, `script.js`
- **Nội dung:** Trung tâm kiến thức công nghệ
  - Hero: Badge, Title, CTA buttons, Floating cards (4 domain)
  - Intro: Giới thiệu + Stats (500+ bài, 50+ chuyên gia, 10k+ độc giả)
  - Timeline: Lịch sử phát triển 2020-2025
  - 4 Domain Cards: Web Dev, Cloud Computing, Cyber Security, DevOps
  - Articles: 3 bài viết mẫu (Tutorial, Deep Dive, Case Study)
  - Newsletter signup form
  - Footer: Social links, 4 cột navigation

**Kiểm tra local (không cần DNS):**
```bash
curl -H "Host: student.local" http://localhost
curl -H "Host: technology.local" http://localhost
```

**Hoặc thêm vào `/etc/hosts` (Windows: `C:\Windows\System32\drivers\etc\hosts`):**
```
127.0.0.1 student.local
127.0.0.1 technology.local
127.0.0.1 phpmyadmin.local
127.0.0.1 nodered.local
```

---

## 6. Cấu Trúc Thư Mục

```
WEB-BT1/
├── docker-compose.yml          # Orchestration 5 services
├── .env.example                # Template biến môi trường
├── .env                        # Local config (KHÔNG commit)
├── .gitignore                  # Loại trừ secret, volume, log
├── README.md                   # File này
├── nginx/
│   └── conf.d/
│       └── default.conf        # 4 server blocks
├── website1/
│   ├── index.html              # Student Portal
│   ├── style.css               # Styling
│   └── script.js               # Interactions
├── website2/
│   ├── index.html              # Technology Hub
│   ├── style.css               # Styling
│   └── script.js               # Interactions
├── nodered/
│   └── flows.json              # Flow demo (Inject→Function→Debug)
├── cloudflared/
│   └── config.example.yml      # Tunnel config mẫu (placeholder)
└── screenshots/                # Ảnh chụp màn hình test
```

---

## 7. Cách Khởi Động Hệ Thống

### 7.1 Yêu Cầu Trước
- Docker Desktop đã cài và chạy (WSL2 backend)
- Đã clone project về máy

### 7.2 Tạo File Environment
```bash
cd WEB-BT1
cp .env.example .env
# Chỉnh sửa .env với mật khẩu thực tế:
# MARIADB_ROOT_PASSWORD=your_strong_root_password
# MARIADB_PASSWORD=your_strong_user_password
# CLOUDFLARE_TUNNEL_TOKEN= (để trống nếu chưa có)
```

### 7.3 Build & Start
```bash
# Kiểm tra syntax
docker compose config

# Khởi động tất cả service (trừ cloudflared)
docker compose up -d

# Hoặc bao gồm cloudflared (cần token thật)
docker compose --profile tunnel up -d
```

### 7.4 Kiểm Tra Trạng Thái
```bash
docker compose ps
# Tất cả service phải UP/HEALTHY

docker compose logs -f nginx      # Log nginx
docker compose logs -f mariadb    # Log MariaDB
docker compose logs -f nodered    # Log Node-RED
```

---

## 8. Cách Kiểm Tra Từng Service

### 8.1 Nginx & 2 Website
```bash
# Test config nginx
docker compose exec nginx nginx -t

# Test Website 1 (Student Portal)
curl -H "Host: student.local" http://localhost

# Test Website 2 (Technology Hub)
curl -H "Host: technology.local" http://localhost

# Mở trình duyệt:
# http://student.local     (cần cấu hình hosts)
# http://technology.local  (cần cấu hình hosts)
```

### 8.2 Node-RED
```bash
# Truy cập UI
http://localhost:1880
# Hoặc qua Nginx proxy (cần hosts):
http://nodered.local

# Kiểm tra flow demo:
# - Tab "Demo Flow"
# - Click nút Inject → Xem Debug panel
# - Output: {ok: 1, msg: "Node-RED hoạt động", time: "..."}
```

### 8.3 MariaDB
```bash
# Kiểm tra container
docker compose exec mariadb mariadb -u webuser -p web_lab -e "SHOW TABLES;"

# Hoặc dùng phpMyAdmin (xem dưới)
```

### 8.4 phpMyAdmin
```bash
# Truy cập qua Nginx proxy (cần hosts):
http://phpmyadmin.local

# Login:
# Username: webuser
# Password: (từ .env MARIADB_PASSWORD)
```

### 8.5 Cloudflared
```bash
# Chỉ chạy khi có domain + token thật:
docker compose --profile tunnel up -d cloudflared

# Kiểm tra log
docker compose logs -f cloudflared

# Không có domain/token thật → service không chạy được tunnel
# Trạng thái: CONFIG READY — REAL DOMAIN/TOKEN REQUIRED
```

---

## 9. Cấu Hình 2 Domain Trên Nginx

File: `nginx/conf.d/default.conf`

```nginx
# Website 1
server {
    listen 80;
    server_name student.local;
    root /var/www/website1;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}

# Website 2
server {
    listen 80;
    server_name technology.local;
    root /var/www/website2;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}

# phpMyAdmin Proxy
server {
    listen 80;
    server_name phpmyadmin.local;
    location / {
        proxy_pass http://phpmyadmin:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        ...
    }
}

# Node-RED Proxy (WebSocket support)
server {
    listen 80;
    server_name nodered.local;
    location / {
        proxy_pass http://nodered:1880;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        ...
    }
}
```

**Logic:** Nginx đọc header `Host` → route đến `root` hoặc `proxy_pass` tương ứng.

---

## 10. Cloudflare Tunnel - Chi Tiết

### 10.1 Config Mẫu
File: `cloudflared/config.example.yml`

```yaml
tunnel: TUNNEL_ID_HERE
credentials-file: /etc/cloudflared/TUNNEL_ID_HERE.json

ingress:
  - hostname: YOUR_DOMAIN_HERE
    service: http://nginx:80
  - hostname: student.YOUR_DOMAIN_HERE
    service: http://nginx:80
  - hostname: technology.YOUR_DOMAIN_HERE
    service: http://nginx:80
  - hostname: nodered.YOUR_DOMAIN_HERE
    service: http://nodered:1880
  - hostname: phpmyadmin.YOUR_DOMAIN_HERE
    service: http://phpmyadmin:80
  - service: http_status:404
```

### 10.2 Các Bước Để Public Internet (Khi Có Domain Thật)
1. Mua domain / có sẵn domain trên Cloudflare
2. Tạo Tunnel trên Cloudflare Zero Trust Dashboard
3. Lấy `Tunnel ID` và `Tunnel Token`
4. Copy `config.example.yml` → `config.yml`, thay placeholder
5. Tạo file credentials `.json` từ Cloudflare
6. Set `.env`: `CLOUDFLARE_TUNNEL_TOKEN=your_token`
7. Chạy: `docker compose --profile tunnel up -d`

### 10.3 Lưu Ý Quan Trọng
- **KHÔNG** commit token thật vào Git
- **KHÔNG** hardcode secret trong `docker-compose.yml`
- File `config.example.yml` chỉ là mẫu, dùng placeholder
- Nếu chưa có domain/token → **KHÔNG** báo tunnel đã hoạt động

---

## 11. Các Lệnh Docker Quan Trọng

| Lệnh | Mô tả |
|------|-------|
| `docker compose config` | Validate & hiển thị config resolved |
| `docker compose up -d` | Khởi động background |
| `docker compose down` | Dừng & xóa container (giữ volume) |
| `docker compose down -v` | Dừng & xóa container + volume (MẤT DỮ LIỆU) |
| `docker compose ps` | Trạng thái container |
| `docker compose logs -f <service>` | Xem log real-time |
| `docker compose exec <service> <cmd>` | Chạy lệnh trong container |
| `docker compose restart <service>` | Restart 1 service |
| `docker compose up -d --force-recreate <service>` | Recreate container (apply .env mới) |
| `docker compose --profile tunnel up -d` | Start kèm profile tunnel |

---

## 12. Kết Quả Kiểm Thử (Test Results)

| Test | Kết Quả | Ghi Chú |
|------|---------|---------|
| `docker compose config` | ✅ PASS | Warning version obsolete, env vars OK |
| `nginx -t` | ✅ PASS | Syntax OK |
| `curl -H "Host: student.local" http://localhost` | ✅ PASS | Trả về Student Portal HTML |
| `curl -H "Host: technology.local" http://localhost` | ✅ PASS | Trả về Technology Hub HTML |
| Node-RED UI (`:1880`) | ✅ PASS | Load editor, flow demo chạy |
| phpMyAdmin (`phpmyadmin.local`) | ✅ PASS | Load login page, kết nối MariaDB OK |
| MariaDB logs | ✅ PASS | "ready for connections" |
| Volumes persistence | ✅ PASS | Data survives restart |

---

## 13. Phần Cần Domain/Token Thật (Chưa Test Được)

| Tính năng | Trạng thái | Yêu cầu |
|-----------|------------|---------|
| Cloudflare Tunnel public Internet | ⏳ CONFIG READY | Domain + Tunnel Token Cloudflare |
| HTTPS tự động qua Cloudflare | ⏳ PENDING | Tunnel active + cert từ Cloudflare |
| Custom domain cho 2 website | ⏳ PENDING | DNS record → Tunnel |
| Truy cập từ Internet bên ngoài | ⏳ PENDING | Tunnel active |

---

## 14. Bảo Mật & Best Practices

- ✅ **Không hardcode secret** trong `docker-compose.yml` → dùng `${VAR}` từ `.env`
- ✅ **`.env` trong `.gitignore`** → không commit password thật
- ✅ **MariaDB không expose port 3306** ra host → chỉ internal network
- ✅ **phpMyAdmin không expose port** → chỉ qua Nginx proxy
- ✅ **Security headers** trên Nginx
- ✅ **Volumes** cho data persistence
- ✅ **Restart policy** `unless-stopped`
- ✅ **Healthcheck** trên Node-RED
- ✅ **Cloudflared profile tách biệt** → không chạy nếu không có token

---

## 15. Troubleshooting Thường Gặp

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| MariaDB restart loop | Thiếu `MARIADB_ROOT_PASSWORD` | Tạo `.env` từ `.env.example`, `docker compose up -d --force-recreate mariadb` |
| Nginx 404 | Sai `root` path hoặc volume mount | Kiểm tra `docker-compose.yml` volumes, `nginx/conf.d/default.conf` |
| Website không load CSS/JS | Path relative sai | Đảm bảo `index.html` dùng `href="style.css"` (cùng thư mục) |
| Node-RED không load flow | Volume mount sai hoặc flow.json lỗi JSON | Kiểm tra `nodered/flows.json` valid JSON, volume `nodered_data` |
| phpMyAdmin không kết nối DB | Sai host/user/pass | Host: `mariadb`, User: `webuser`, Pass: từ `.env` |
| Port 80 bị chiếm | IIS/Apache khác đang chạy | Dịch vụ khác dừng, hoặc đổi port mapping Nginx |

---

## 16. Tác Giả & Nộp Bài

- **Môn học:** Lập Trình Web
- **Bài tập:** Bài Tập 1 - Docker Compose & Multi-service Deployment
- **Môi trường:** Windows 11 + WSL2 + Docker Desktop
- **Ngày hoàn thành:** 2026

---

## 17. License

Dự án này phục vụ mục đích học tập và nộp bài môn Lập Trình Web. Không sử dụng cho mục đích thương mại.
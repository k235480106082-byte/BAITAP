# Bài 2: Mã Hoá Bất Đối Xứng RSA & Chữ Ký Số

> **Môn học:** An toàn và Bảo mật Thông tin  
> **Giảng viên hướng dẫn:** ThS. Đỗ Duy Cốp  
> **Sinh viên thực hiện:** Nguyễn Văn Mạnh — **MSSV:** K235480106082 — **Lớp:** 59KMT  
> **Nền tảng:** C# (.NET 8) Windows Forms Desktop Application  
> **Thư viện:** `System.Security.Cryptography`

---

## 1. Giới thiệu & Kiến trúc ứng dụng

Ứng dụng **Windows Forms** cài đặt thuật toán mã hoá bất đối xứng **RSA-2048**, chuẩn mã hoá đệm **RSA-OAEP (SHA-256)**, hàm băm mật mã **SHA-256** và cơ chế chữ ký số bảo mật **RSA-PSS**.

Giao diện được thiết kế khoa học với 2 phần tách biệt:
- **Khung điều khiển bên trái:** Ô nhập dữ liệu và các nút bấm chức năng được đánh số theo từng mục yêu cầu đề bài.
- **Khung kết quả bên phải:** Màn hình Log dạng hộp văn bản font `Consolas` chuyên dụng hiển thị chi tiết các thông số toán học, thời gian thực thi và kết quả đối soát.

---

## 2. Bảng đối chiếu các chức năng

| Nút bấm | Chức năng đề bài | Nội dung chi tiết |
| :---: | :--- | :--- |
| **1-2** | **Sinh cặp khoá & lưu PEM** | Sinh cặp khoá RSA-2048, xuất `public.pem` (PKCS#8) và `private.pem` (PKCS#1) |
| **3-4** | **Xem PEM & Ý nghĩa byte ASN.1** | Giải mã Base64 DER, phân tích cây ASN.1 TLV, trích xuất $n, e, d, p, q, dP, dQ, qInv$ |
| **5** | **Mã hoá dữ liệu ($\le 190$ byte)** | Dùng Public Key mã hoá khoá AES 32 bytes (256 bit) bằng RSA-OAEP SHA-256 $\rightarrow$ Base64 |
| **6** | **Giải mã & So sánh nguồn** | Dùng Private Key giải mã từ file `data_mahoa.txt`, đối chiếu với dữ liệu gốc |
| **7** | **Đo tốc độ Public vs Private Key** | Đo thời gian chạy 100 lần: Public Key ($e=65537$) vs Private Key ($d \approx 2048$ bit) |
| **8** | **Băm SHA-256 & Avalanche Effect** | Tính mã băm 256-bit real-time, đo khoảng cách Hamming đánh giá hiệu ứng tuyết lở |
| **9a** | **Ký số PKCS#1 v1.5** | Ký 2 lần liên tiếp cùng nội dung $\rightarrow$ Cho ra 2 chữ ký giống nhau (tất định) |
| **9b** | **Ký số RSA-PSS (Đề xuất)** | Nhúng chuỗi Salt ngẫu nhiên $\rightarrow$ Cùng dữ liệu + cùng khoá sinh ra **chữ ký khác nhau** |

---

## 3. Cách chạy ứng dụng

```bash
# Di chuyển vào thư mục bài 2
cd bai2_rsa

# Khởi chạy Windows Forms
dotnet run
```
*Hoặc nhấp đúp trực tiếp vào file **`Chay_Bai2_Dotnet_Form.bat`** (hoặc `Chay_Bai2_Form.bat`).*

---

## 4. Minh chứng hình ảnh & Phân tích chuyên sâu

### 4.1. Sinh cặp khoá RSA-2048 & Xuất file PEM (Mục 1, 2)
Cặp khoá được sinh với chiều dài 2048 bit và xuất ra định dạng chuẩn PEM mã hoá Base64:
- `public.pem`: Header `-----BEGIN PUBLIC KEY-----`
- `private.pem`: Header `-----BEGIN RSA PRIVATE KEY-----`

![Sinh cặp khoá và xuất PEM](images/01-sinh-khoa-pem.png)

---

### 4.2. Phân tích cấu trúc ASN.1 TLV & Ý nghĩa các trường byte (Mục 3, 4)
Định dạng PEM bao bọc cấu trúc nhị phân **ASN.1 DER** theo quy tắc **Tag - Length - Value (TLV)**:
- **Tag `0x30` (`SEQUENCE`):** Khối bao bọc danh sách các trường con.
- **Tag `0x02` (`INTEGER`):** Chứa các số nguyên lớn của thuật toán RSA.
- **Tag `0x06` (`OBJECT IDENTIFIER`):** Mã định danh thuật toán `1.2.840.113549.1.1.1` (`rsaEncryption`).

#### Các tham số toán học trích xuất từ PEM:
| Tham số | Ý nghĩa toán học | Kích thước | Ghi chú |
| :---: | :--- | :---: | :--- |
| **$n$** | Modulus ($n = p \times q$) | 256 bytes (2048 bit) | Dùng chung cho cả Public và Private Key |
| **$e$** | Public Exponent | 3 bytes (17 bit) | Thường chọn $e = 65537 = 2^{16} + 1$ |
| **$d$** | Private Exponent | 256 bytes (2048 bit) | $e \cdot d \equiv 1 \pmod{\lambda(n)}$ (Khoá bí mật) |
| **$p, q$** | Hai số nguyên tố sinh khoá | 128 bytes mỗi số | $p \times q = n$ |
| **$dP, dQ$** | Khử số mũ theo modulo $p-1, q-1$ | 128 bytes mỗi số | Hỗ trợ giải mã nhanh theo định lý phần dư Trung Hoa (CRT) |
| **$qInv$** | Nghịch đảo modulo: $q^{-1} \bmod p$ | 128 bytes | Phục vụ tính toán CRT |

![Xem PEM và ý nghĩa các byte ASN.1](images/02-xem-pem.png)

---

### 4.3. Mã hoá dữ liệu $\le 190$ bytes bằng Public Key (Mục 5)
RSA-2048 với padding OAEP (SHA-256) mã hoá tối đa:
$$\text{Max Payload} = \text{KeySize} - 2 \times \text{HashLen} - 2 = 256 - 2 \times 32 - 2 = 190 \text{ bytes}$$
Chương trình mã hoá khoá đối xứng AES 32 bytes (256-bit) và ghi bản mã Base64 (256 bytes) ra file `data_mahoa.txt`:

![Mã hoá dữ liệu bằng Public Key](images/03-ma-hoa-du-lieu.png)

---

### 4.4. Giải mã bằng Private Key & Đối soát nguồn (Mục 6)
Nạp lại `data_mahoa.txt` và `private.pem` để giải mã. Dữ liệu khôi phục đối chiếu với bản gốc trùng khớp tuyệt đối 100%:

![Giải mã bằng Private Key và so sánh](images/04-giai-ma-so-sanh.png)

---

### 4.5. Benchmark tốc độ: Public Key ($e$ nhỏ) vs Private Key ($d$ lớn) (Mục 7)
Đo đạc thực nghiệm trên 100 lượt mã hoá và giải mã liên tục:

| Phép toán | Khoá sử dụng | Số mũ | Thời gian trung bình | So sánh |
| :--- | :---: | :---: | :---: | :---: |
| **Mã hoá / Verify** | Public Key ($n, e$) | $e = 65537$ ($17\text{ bit}$) | **$\approx 0.0169\text{ ms/lần}$** | Nhanh hơn **~30 lần** |
| **Giải mã / Ký** | Private Key ($n, d$) | $d \approx 2048\text{ bit}$ | **$\approx 0.5090\text{ ms/lần}$** | Chậm hơn |

#### Giải thích bản chất toán học:
Theo thuật toán **Square-and-Multiply (Bình phương và nhân)**:
- $e = 65537 = 2^{16} + 1$, biểu diễn nhị phân chỉ có **đúng hai bit 1** (`10000000000000001`$_2$). Do đó, chỉ cần **16 phép bình phương và 1 phép nhân modular**.
- $d$ là số ngẫu nhiên lớn 2048-bit, có trung bình **~1024 bit 1**. Cần tới **~2047 phép bình phương và ~1024 phép nhân các số nguyên lớn 2048-bit**.
- Vì vậy, phép tính với Private Key tốn tài nguyên và thời gian hơn Public Key xấp xỉ 20-30 lần.

![Đo tốc độ mã hoá vs giải mã](images/05-do-toc-do.png)

---

### 4.6. Băm SHA-256 & Hiệu ứng tuyết lở (Avalanche Effect) (Mục 8)
Kiểm tra tính ngẫu nhiên và an toàn của hàm băm SHA-256 khi thay đổi chỉ 1 ký tự ở dữ liệu đầu vào:
- Chuỗi 1: `"An toan thong tin"` $\rightarrow$ `E2082ED8...D514A8CD`
- Chuỗi 2: `"An toan thong tin."` (Thêm 1 dấu chấm) $\rightarrow$ `50481223...F5B481E2`
- **Khoảng cách Hamming:** Lệch **130 / 256 bit ($\approx 50.78\%$)**.
- **Đánh giá:** Đáp ứng hoàn hảo **Hiệu ứng tuyết lở (Avalanche Effect)** — chỉ cần 1 bit đầu vào thay đổi sẽ làm biến đổi ngẫu nhiên khoảng một nửa tổng số bit ở đầu ra, đảm bảo tính kháng va chạm và không thể đảo ngược.

![Băm SHA-256 và hiệu ứng tuyết lở](images/06-bam-sha256.png)

---

### 4.7. Chữ ký số: So sánh PKCS#1 v1.5 vs RSA-PSS (Mục 9)

#### A. Ký bằng PKCS#1 v1.5 (Tất định):
Cùng một nội dung và cùng một Private Key, ký nhiều lần cho ra **chữ ký giống hệt nhau 100%**:

![Chữ ký số PKCS1 v1.5 hai lần giống nhau](images/07-chu-ky-pkcs1v15.png)

#### B. ĐỀ XUẤT: Ký bằng RSA-PSS (Probabilistic Signature Scheme - RFC 3447):
Để đạt được mong muốn **cùng 1 dữ liệu + cùng 1 người ký nhưng mỗi lần ký ra một chữ ký số khác nhau**, giải pháp chuẩn mực quốc tế là sử dụng **RSA-PSS**:
- **Nguyên lý hoạt động:** Thuật toán PSS chèn thêm một chuỗi **Salt (muối) ngẫu nhiên** vào dữ liệu trước khi băm và mã hoá số mũ bí mật:
  $$M' = \text{Padding} \parallel \text{Salt} \parallel \text{Hash}(M)$$
- **Kết quả ký 2 lần:** Mỗi lần ký sinh ra một chuỗi Base64 **hoàn toàn khác nhau**.
- **Xác minh (Verification):** Public Key giải mã khối PSS, trích xuất chuỗi Salt ngẫu nhiên và đối chiếu lại với mã băm ban đầu. Cả 2 chữ ký khác nhau đều được hệ thống xác nhận **HỢP LỆ (True)**!
- **Ý nghĩa thực tế:** Ngăn chặn triệt để hình thức tấn công phát lại (**Replay Attack**) trong các giao dịch ngân hàng điện tử và hợp đồng số.

![Chữ ký số RSA-PSS mỗi lần khác nhau](images/08-chu-ky-pss.png)

---

*Sinh viên: **Nguyễn Văn Mạnh** — MSSV: **K235480106082** — Lớp: **59KMT***

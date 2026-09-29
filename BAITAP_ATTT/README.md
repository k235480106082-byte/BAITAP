# BÁO CÁO — MÔN AN TOÀN VÀ BẢO MẬT THÔNG TIN

| Thông tin | Nội dung |
|---|---|
| **Sinh viên** | Nguyễn Văn Mạnh — MSSV K235480106082 |
| **Lớp** | 59KMT |
| **Giảng viên** | Đỗ Duy Cốp |
| **Ngôn ngữ lập trình** | Python 3.11 (thư viện `cryptography`) |

---

## Yêu cầu đề bài

1. Tìm hiểu thuật toán mã hóa hiện đại DES, AES: mô tả được thuật toán, quy trình mã
   hóa/giải mã; cài đặt AES trên một ngôn ngữ lập trình.
2. Tìm hiểu thuật toán mã hóa bất đối xứng RSA: nguyên lý sinh cặp khóa bí mật, công khai.
3. Trình bày các mô hình áp dụng thuật toán RSA (xác thực người gửi, xác thực người nhận,
   cả hai); so sánh thời gian mã hóa/giải mã của RSA với AES; đưa ra cách kết hợp sức mạnh
   của RSA và AES.

---

## BÀI 1 — DES và AES

### DES (Data Encryption Standard)

DES là thuật toán mã hóa đối xứng dạng khối (block cipher), khối 64-bit, khóa 56-bit,
cấu trúc 16 vòng Feistel. Quy trình mã hóa gồm: hoán vị ban đầu (IP), 16 vòng lặp
F-expansion + Substitution (S-box) + Permutation dưới sự dẫn xuất của khóa con (key
schedule sinh 16 khóa con 48-bit từ khóa 56-bit), và hoán vị cuối (FP = IP⁻¹).
Giải mã chạy ngược quy trình với thứ tự khóa con đảo lại.

Điểm yếu của DES: khóa chỉ 56-bit nên bị bẻ khóa bằng brute-force từ những năm 1990
(DES Break 1999 chỉ mất chưa đầy 1 ngày). 3DES (Triple DES) kéo dài bằng cách áp DES
3 lần nhưng chậm. DES bị thay thế hoàn toàn bởi AES — bảng so sánh chi tiết nằm ở
`docs/DES.md`.

### AES (Advanced Encryption Standard) — cài đặt trên Python

AES khác DES ở cấu trúc: thay vì Feistel, AES dùng mạng thay thế – hoán vị
(Substitution-Permutation Network) trên khối 128-bit, hỗ trợ khóa 128/192/256-bit.
Mỗi vòng của AES gồm 4 bước: SubBytes (thay thế qua S-box 16×16), ShiftRows
(dời hàng), MixColumns (trộn cột, trừ vòng cuối), AddRoundKey (XOR với khóa con).
Số vòng: 10 (AES-128), 12 (AES-192), 14 (AES-256).

**Phần cài đặt**: project cài đặt và chạy AES bằng Python 3.11 qua thư viện
`cryptography` ở chế độ **AES-128-GCM** (Galois/Counter Mode) tại
`src/aes/aes_demo.py`. Đây là chế độ AEAD — vừa mã hóa vừa xác thực tính toàn vẹn
dữ liệu, kèm nonce ngẫu nhiên 12-byte chống tái sử dụng. Việc dùng thư viện chuẩn
được kiểm định thay vì tự viết S-box từ đầu là chủ đích về mặt bảo mật (tự viết极易
sai sót và tạo lỗ hổng), đồng thời thuật toán AES bên dưới vẫn được trình bày đầy đủ
trong `docs/AES.md`.

Hàm demo bao gồm: sinh khóa AES-128 ngẫu nhiên, mã hóa plaintext → ciphertext +
tag, giải mã và kiểm tra tag đúng/sai (tampered ciphertext bị từ chối). Unit test
`tests/test_aes.py` xác nhận encrypt/decrypt đảo đúng, sai tag thì fail.

### So sánh DES với AES

| Tiêu chí | DES | AES |
|---|---|---|
| Khối | 64-bit | 128-bit |
| Khóa | 56-bit | 128/192/256-bit |
| Cấu trúc | Feistel 16 vòng | SPN 10–14 vòng |
| Bảo mật | Đã bẻ khóa | Chưa có tấn công thực tế |
| Tốc độ | Chậm | Nhanh, song song hóa tốt |

---

## BÀI 2 — RSA: nguyên lý sinh cặp khóa

RSA dựa trên bài toán nhân thừa số: rất dễ nhân hai số nguyên tố lớn nhưng rất khó
phân rã tích của chúng. Quy trình sinh cặp khóa bí mật/công khai gồm 6 bước
(trình bày chi tiết trong `docs/RSA.md`, code tại `src/rsa/rsa_demo.py`):

1. **Chọn hai số nguyên tố lớn p, q** (ngẫu nhiên, mỗi số hàng trăm bit).
2. **Tính modulus** `n = p × q` — đây là một nửa của cả hai khóa.
3. **Tính hàm Carmichael** `λ(n) = (p−1)(q−1)/gcd(p−1, q−1)`.
4. **Chọn khóa công khai e**: `1 < e < λ(n)` và `gcd(e, λ(n)) = 1` (thường e = 65537).
5. **Tính khóa bí mật d**: `d ≡ e⁻¹ (mod λ(n))`, tức `d × e ≡ 1 (mod λ(n))`.
6. Tùy chọn pre-compute các tham số CRT (p, q, dP, dQ, qInv) để tăng tốc giải mã.

**Khóa công khai** `(n, e)` dùng để mã hóa và verify chữ ký — được chia sẻ tự do.
**Khóa bí mật** `(n, d)` dùng để giải mã và ký — tuyệt đối không chia sẻ.
Nguyên lý: mã hóa `c = m^e mod n`, giải mã `m = c^d mod n`; tính chất Euler đảm bảo
`m^(ed) ≡ m (mod n)` nên giải mã trả lại đúng plaintext.

Trong project, mã hóa dùng padding **OAEP (SHA-256)** và chữ ký dùng **PSS (SHA-256)**
— các padding hiện đại an toàn, thay cho PKCS#1 v1.5 đã có padding oracle attack.
Khóa tiêu chuẩn RSA-2048 (bắt buộc ≥ 2048-bit vì 1024-bit đã bị coi là hỏng).

---

## BÀI 3 — Các mô hình áp dụng RSA

### Mô hình 1 — Xác thực người gửi (Sender Authentication)

Người gửi ký thông điệp bằng **khóa bí mật** của mình (RSA-PSS), người nhận xác minh
bằng **khóa công khai** của người gửi. Vì chỉ người giữ khóa bí mật mới ký được nên
nhận tin có thể tin rằng "chỉ người này mới gửi được" — chống giả mạo người gửi.
Đồng thời chữ ký cũng đảm bảo nội dung không bị sửa đổi trên đường đi.
Triển khai tại `src/auth/auth_demo.py` (chế độ sender).

### Mô hình 2 — Xác thực người nhận (Receiver Authentication)

Người gửi yêu cầu người nhận chứng minh danh tính bằng **challenge–response**:
người nhận mã hóa một thách thức ngẫu nhiên (nonce) bằng **khóa bí mật của người nhận**
và trả lại; người gửi verify bằng khóa công khai của người nhận. Người gửi tin rằng
"người nắm khóa bí mật thật sự đang ở phía bên kia" — xác thực người nhận trước khi
gửi dữ liệu nhạy cảm.

### Mô hình 3 — Xác thực hai chiều (Mutual Authentication)

Kết hợp cả hai mô hình trên trong cùng phiên: hai bên lần lượt ký challenge của nhau
và verify bằng khóa công khai của đối phương. Sau khi hoàn tất, cả hai bên đều chắc
chắn đối phương sở hữu đúng khóa bí mật — đây là mô hình đạt được cả xác thực người
gửi lẫn người nhận, tương tự nguyên tắc trong TLS handshake.
Chi tiết luồng và code: `docs/AUTHENTICATION.md`, `src/auth/auth_demo.py`.

### So sánh thời gian mã hóa/giải mã RSA với AES

Benchmark chạy bằng `src/benchmark/benchmark.py` trên máy thực, đo throughput theo
kích thước dữ liệu. Kết quả tiêu biểu (64 byte):

| Thao tác | Tốc độ đo được |
|---|---|
| AES mã hóa | ~16,8 MB/s (256 byte: ~113 MB/s) |
| AES giải mã | ~32,5 MB/s (256 byte: ~140 MB/s) |
| RSA mã hóa | ~1,0 MB/s |
| RSA giải mã | ~0,08 MB/s |

Kết luận thực nghiệm: **RSA chậm hơn AES hàng chục đến hàng trăm lần**, càng rõ rệt
với dữ liệu lớn — do RSA phải thực hiện phép mod exponentiation trên số lớn, trong
khi AES chỉ là các phép thao tác bảng/XOR trên khối 128-bit. Ngoài ra RSA giới hạn
dữ liệu mỗi lần mã hóa (RSA-2048 OAEP chỉ mã hóa được ~190 byte), trong khi AES
mã hóa dữ liệu không giới hạn (streaming). Vì vậy thực tế không bao giờ dùng RSA
mã hóa trực tiếp dữ liệu lớn.

### Kết hợp sức mạnh RSA và AES (Hybrid Encryption)

Giải pháp lai khai thác điểm mạnh của cả hai (`src/hybrid/hybrid_demo.py`,
`docs/HYBRID.md`):

1. Người gửi sinh một **session key AES ngẫu nhiên** (128-bit).
2. Mã hóa dữ liệu lớn bằng **AES** bằng session key đó (nhanh, không giới hạn kích thước).
3. Mã hóa session key bằng **RSA** bằng khóa công khai của người nhận (chỉ ~190 byte,
   RSA gánh đúng việc phân phối khóa).
4. Người nhận giải mã session key bằng khóa bí mật RSA, rồi dùng AES giải mã dữ liệu.

Đây chính là cách HTTPS/TLS, PGP, WhatsApp... đang làm: RSA (hoặc ECC) bảo vệ khóa,
AES bảo vệ dữ liệu. Ưu điểm: tốc độ gần như thuần AES, đồng thời có được tính bất đối
xứng — không cần trao đổi khóa trước. Bảo mật của chế độ lai cũng được trình bày
trong `docs/HYBRID.md` (xử lý replay bằng nonce/timestamp, chống MITM bằng xác minh
chỉ số khóa công khai...).

---

## Kiểm thử

Toàn bộ hệ thống có 49 unit tests chia vào 5 file test (AES, RSA, Authentication,
Hybrid, Benchmark). Chạy bằng:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

**Kết quả: 49/49 PASS** (Ran 49 tests, OK) — bao gồm test encrypt/decrypt đảo đúng,
sai tag/padding bị từ chối, 3 mô hình xác thực thành công/từ chối đúng, hybrid
round-trip đúng, benchmark trả số dương hợp lệ.

## Cấu trúc thư mục

```text
BAITAP_ATTT/
├── README.md              # báo cáo này
├── requirements.txt       # cryptography >= 42.0.0
├── docs/                  # tài liệu lý thuyết: DES, AES, RSA, AUTHENTICATION, BENCHMARK, HYBRID
├── src/
│   ├── main.py            # CLI chọn demo
│   ├── aes/aes_demo.py    # AES-128-GCM
│   ├── rsa/rsa_demo.py    # RSA-2048 (OAEP + PSS)
│   ├── auth/auth_demo.py  # 3 mô hình xác thực
│   ├── hybrid/hybrid_demo.py  # RSA + AES lai
│   └── benchmark/benchmark.py  # so sánh hiệu năng
└── tests/                 # 49 unit tests
```

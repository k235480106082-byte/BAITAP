# DES (Data Encryption Standard)

## DES là gì?
DES (Data Encryption Standard) là thuật toán mã hóa khối (block cipher) đối xứng được phát triển bởi IBM và chuẩn hóa bởi NIST năm 1977 (FIPS 46). Là tiêu chuẩn mã hóa đầu tiên được chính phủ Mỹ công bố cho sử dụng dân sự.

## Tham số chính
- **Block size**: 64-bit (8 bytes)
- **Key size**: 56-bit hiệu lực (64-bit với 8 bit parity)
- **Số vòng (rounds)**: 16 vòng Feistel
- **Cấu trúc**: Feistel network

## Quá trình mã hóa (mức khái niệm)

### 1. Initial Permutation (IP)
Hoán vị 64-bit input theo bảng cố định.

### 2. 16 vòng Feistel
Mỗi vòng:
- Chia block thành 2 nửa: L (32-bit), R (32-bit)
- Hàm F(R, Kᵢ):
  - **Expansion (E)**: Mở rộng R từ 32-bit → 48-bit
  - **Key mixing**: XOR với subkey Kᵢ (48-bit)
  - **Substitution (S-boxes)**: 8 S-box, mỗi box 6-bit → 4-bit (tổng 32-bit)
  - **Permutation (P)**: Hoán vị 32-bit output
- Lᵢ = Rᵢ₋₁
- Rᵢ = Lᵢ₋₁ ⊕ F(Rᵢ₋₁, Kᵢ)

### 3. Final Permutation (FP = IP⁻¹)
Hoán vị ngược của IP.

## Key Schedule
- 56-bit key → chia làm 2 nửa 28-bit (C₀, D₀)
- Mỗi vòng: xoay trái (left shift) 1 hoặc 2 bit
- Compression permutation (PC-2): 56-bit → 48-bit subkey Kᵢ

## Hạn chế của DES
1. **Key size quá nhỏ (56-bit)**: Có thể brute-force trong thời gian ngắn (1997: EFF Deep Crack < 3 ngày; hiện nay < 1 giờ)
2. **Block size 64-bit**: Dễ bị birthday attack trong mode ECB/CBC với dữ liệu lớn
3. **Weak keys / Semi-weak keys**: Một số key tạo ra subkey lặp lại
4. **Chậm trong software**: Thiết kế cho hardware, S-boxes không cache-friendly

## 3DES (Triple DES)
- Áp dụng DES 3 lần: Encrypt-Decrypt-Encrypt (EDE)
- Keying options:
  - Option 1: 3 key độc lập (168-bit effective)
  - Option 2: K1=K3, K2 khác (112-bit effective)
  - Option 3: K1=K2=K3 (tương đương DES đơn)
- Vẫn dùng block size 64-bit → birthday bound
- Chậm (3 lần DES)

## Vì sao AES thay thế DES?
| Tiêu chí | DES | AES |
|----------|-----|-----|
| Key size | 56-bit | 128/192/256-bit |
| Block size | 64-bit | 128-bit |
| Structure | Feistel | Substitution-Permutation Network |
| Speed (software) | Chậm | Nhanh (lookup table, parallelizable) |
| Security | Broken (brute-force) | An toàn (chưa có tấn công thực tế) |
| Flexibility | Cứng nhắc | Hỗ trợ nhiều key size |

AES được chọn qua cuộc thi công khai (1997-2000), Rijndael thắng nhờ: bảo mật, hiệu năng, đơn giản, linh hoạt.

## Kết luận
DES đã lỗi thời và **không nên dùng** cho ứng dụng mới. NIST đã rút tiêu chuẩn DES (FIPS 46-3 withdrawn 2005). 3DES cũng bị deprecated (NIST SP 800-131A: disallowed after 2023). Chuyển sang AES.

## Tham khảo
- FIPS 46-3 (DES), FIPS 81 (DES modes)
- NIST SP 800-67 (3DES)
- "The Design of Rijndael" - Daemen & Rijmen
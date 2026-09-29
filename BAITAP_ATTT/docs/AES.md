# AES (Advanced Encryption Standard)

## AES là gì?
AES là thuật toán mã hóa khối đối xứng được NIST chuẩn hóa năm 2001 (FIPS 197). Dựa trên thuật toán **Rijndael** của Joan Daemen và Vincent Rijmen. Thay thế DES/3DES.

## Tham số AES-128
- **Block size**: 128-bit (16 bytes) - cố định
- **Key size**: 128-bit (16 bytes) - AES-128
- **Số vòng**: 10 vòng
- **Cấu trúc**: Substitution-Permutation Network (SPN)

Các biến thể: AES-192 (12 vòng, 192-bit key), AES-256 (14 vòng, 256-bit key)

## Cấu trúc State
Dữ liệu 128-bit được biểu diễn ma trận 4×4 byte (column-major):
```
s₀,₀  s₀,₁  s₀,₂  s₀,₃
s₁,₀  s₁,₁  s₁,₂  s₁,₃
s₂,₀  s₂,₁  s₂,₂  s₂,₃
s₃,₀  s₃,₁  s₃,₂  s₃,₃
```

## Quá trình mã hóa (Encryption)

### 1. AddRoundKey (vòng 0)
State ⊕ RoundKey₀

### 2. 9 vòng chính (Round 1-9)
Mỗi vòng gồm 4 phép biến đổi:
- **SubBytes**: Thay thế từng byte bằng S-box (lookup table 256-entry, dựa trên GF(2⁸) multiplicative inverse + affine transform)
- **ShiftRows**: Dịch trái các hàng:
  - Hàng 0: không dịch
  - Hàng 1: dịch 1 byte
  - Hàng 2: dịch 2 byte
  - Hàng 3: dịch 3 byte
- **MixColumns**: Nhân ma trận cố định trong GF(2⁸) (diffusion)
- **AddRoundKey**: State ⊕ RoundKeyᵢ

### 3. Vòng cuối (Round 10)
- SubBytes
- ShiftRows
- AddRoundKey (không có MixColumns)

## Key Expansion (Key Schedule)
- Input: 128-bit key (4 words 32-bit)
- Output: 11 round keys (44 words = 176 bytes)
- Mỗi 4 word tạo 1 round key
- Sử dụng: RotWord, SubWord, Rcon (round constant)

## Giải mã (Decryption)
Sử dụng **Inverse Cipher** (ngược thứ tự):
1. AddRoundKey
2. 9 vòng: InvShiftRows → InvSubBytes → AddRoundKey → InvMixColumns
3. Vòng cuối: InvShiftRows → InvSubBytes → AddRoundKey

> Equivalent Inverse Cipher: Hoán đổi thứ tự InvMixColumns và AddRoundKey để dùng cùng cấu trúc với encryption (dùng InvRoundKey đã biến đổi).

## Chế độ hoạt động (Modes of Operation)

| Mode | IV/Nonce | Parallel | Padding | Authentication | Use case |
|------|----------|----------|---------|----------------|----------|
| ECB | Không | ✓ | Cần | Không | **Không dùng** |
| CBC | IV (random) | Enc: ✗ Dec: ✓ | Cần | Không | Legacy |
| CTR | Nonce+Counter | ✓ | Không | Không | Stream-like |
| **GCM** | **Nonce (96-bit)** | **✓** | **Không** | **✓ (AEAD)** | **Khuyên dùng** |
| CCM | Nonce | ✗ | Không | ✓ (AEAD) | Constrained env |

### AES-GCM (Galois/Counter Mode) - **Được dùng trong project**
- Kết hợp CTR mode + GHASH authentication
- **Nonce**: 96-bit (12 bytes), **KHÔNG ĐƯỢC REUSE** với cùng key
- Output: Ciphertext + Authentication Tag (128-bit mặc định)
- AEAD: Authenticated Encryption with Associated Data
- Hiệu năng cao (parallelizable, hardware acceleration: AES-NI, CLMUL)

## Nonce/IV Management (QUAN TRỌNG)
```
✓ ĐÚNG: nonce = os.urandom(12) mỗi lần encrypt
✓ ĐÚNG: nonce = counter (nếu đảm bảo không lặp)
✗ SAI: nonce = fixed/constant
✗ SAI: nonce reuse với cùng key (catastrophic: key recovery 가능)
```

Trong project: `nonce = os.urandom(12)` (CSPRNG), base64 encode để lưu/transfer.

## Padding
- **GCM/CCM/CTR**: Không cần padding (stream-like)
- **CBC/ECB**: Cần PKCS#7 padding (block size 16 bytes)

## Bảo mật
- Không có tấn công thực tế tốt hơn brute-force
- Best known: biclique attack giảm ~2-bit (vẫn 2¹²⁶ operations)
- Side-channel: Cần constant-time implementation (thư viện `cryptography` đã lo)
- Quantum: Grover's algorithm giảm hiệu lực key xuống 2⁶⁴ → AES-256 khuyên dùng cho post-quantum

## Project Implementation
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key = os.urandom(16)           # 128-bit key
nonce = os.urandom(12)         # 96-bit nonce
aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(nonce, plaintext, None)
decrypted = aesgcm.decrypt(nonce, ciphertext, None)
```
- Sử dụng `cryptography.hazmat.primitives.ciphers.aead.AESGCM` (binding OpenSSL/BoringSSL)
- Associated data = None (có thể dùng cho AAD nếu cần)

## Tham khảo
- FIPS 197 (AES standard)
- NIST SP 800-38A (modes), SP 800-38D (GCM)
- RFC 5116 (AEAD interface)
- "The Design of Rijndael" - Daemen & Rijmen
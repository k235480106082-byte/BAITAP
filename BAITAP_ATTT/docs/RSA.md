# RSA (Rivest-Shamir-Adleman)

## RSA là gì?
RSA là thuật toán mã hóa bất đối xứng (public-key) đầu tiên thực tế, được phát minh năm 1977 bởi Ron Rivest, Adi Shamir, Leonard Adleman (MIT). Dựa trên độ khó của bài toán phân tích thừa số nguyên lớn (Integer Factorization Problem).

## Cặp khóa Public/Private
- **Public Key (khóa công khai)**: `(n, e)` - dùng để mã hóa, xác thực chữ ký
- **Private Key (khóa bí mật)**: `(n, d)` hoặc `(p, q, d, ...)` - dùng để giải mã, ký số
- `n` (modulus) được công khai, `p, q, d` phải giữ bí mật

## Tạo cặp khóa (Key Generation)

### 1. Chọn 2 số nguyên tố lớn p, q
- Kích thước: mỗi số ~1024-bit cho RSA-2048
- `p ≠ q`, `|p - q|` đủ lớn (tránh Fermat factorization)
- Sinh bằng probabilistic primality test (Miller-Rabin)

### 2. Tính modulus n
```
n = p × q
```
- `n` có độ dài 2048-bit
- Công khai

### 3. Tính Carmichael function λ(n)
```
λ(n) = lcm(p-1, q-1) = (p-1)(q-1) / gcd(p-1, q-1)
```
- Dùng λ(n) thay φ(n) = (p-1)(q-1) cho hiệu quả (PKCS#1 v2.2)

### 4. Chọn public exponent e
- Thông thường: **e = 65537** (0x10001)
- Điều kiện: `1 < e < λ(n)` và `gcd(e, λ(n)) = 1`
- 65537 là số Fermat (2¹⁶+1), ít bit 1 → nhanh khi exponentiation

### 5. Tính private exponent d
```
d ≡ e⁻¹ (mod λ(n))
```
- Nghịch đảo modulo: `e × d ≡ 1 (mod λ(n))`
- Tính bằng Extended Euclidean Algorithm

### 6. (Tùy chọn) Pre-compute cho CRT (Chinese Remainder Theorem)
```
dP = d mod (p-1)
dQ = d mod (q-1)
qInv = q⁻¹ mod p
```
- Tăng tốc giải mã/ký số ~4x

## Mã hóa (Encryption) - RSA-OAEP
### Input: Message M (bytes), Public Key (n, e)
### Output: Ciphertext C

**RSA-OAEP (Optimal Asymmetric Encryption Padding)** - PKCS#1 v2.2:
1. **Padding**: M → EM (encoded message) bằng MGF1(SHA-256), random seed
2. **RSA primitive**: `c = mᵉ mod n` (m = OS2IP(EM))
3. **Output**: `C = I2OSP(c, k)` (k = key length in bytes)

> **Không bao giờ dùng Raw RSA (textbook RSA)** - dễ bị chosen-ciphertext attack.

## Giải mã (Decryption) - RSA-OAEP
### Input: Ciphertext C, Private Key (n, d) hoặc (p, q, dP, dQ, qInv)
### Output: Message M hoặc Error

1. **RSA primitive**: `m = cᵈ mod n` (hoặc dùng CRT)
2. **Unpadding**: OAEP decode với MGF1(SHA-256)
3. **Verify**: Kiểm tra padding structure, hash
4. **Output**: M hoặc raise error

## Chữ ký số (Digital Signature) - RSA-PSS
### Ký (Sign): Input M, Private Key → Signature S
1. **EMSA-PSS encoding**: M → EM (Probabilistic Signature Scheme)
   - Sử dụng MGF1(SHA-256), random salt
2. **RSA primitive**: `s = mᵈ mod n`
3. **Output**: `S = I2OSP(s, k)`

### Xác thực (Verify): Input M, S, Public Key → Pass/Fail
1. **RSA primitive**: `m = sᵉ mod n`
2. **EMSA-PSS verify**: So sánh EM với M
3. **Output**: True/False

> PSS (Probabilistic Signature Scheme) bảo mật hơn PKCS#1 v1.5 signature.

## Toán học cốt lõi
```
n = p × q                              (modulus)
λ(n) = lcm(p-1, q-1)                   (Carmichael function)
e × d ≡ 1 (mod λ(n))                   (key relation)
```

**Mã hóa**: `C ≡ Mᵉ (mod n)`
**Giải mã**: `M ≡ Cᵈ (mod n)`
**Chữ ký**: `S ≡ Mᵈ (mod n)`
**Xác thực**: `M ≡ Sᵉ (mod n)`

**Đúng vì**: `(Mᵉ)ᵈ ≡ Mᵉᵈ ≡ M¹⁺ᵏλ⁽ⁿ⁾ ≡ M (mod n)` (Euler's theorem generalization)

## Kích thước khóa (Key Sizes)
| Key Size | Security Level | Status |
|----------|----------------|--------|
| 1024-bit | ~80-bit | **Deprecated** (broken) |
| 2048-bit | ~112-bit | **Hiện tại OK** (NIST: OK until 2030) |
| 3072-bit | ~128-bit | **Khuyên dùng** cho mới |
| 4096-bit | ~144-bit | An toàn lâu dài, chậm hơn |

Project dùng **RSA-2048** (cân bằng bảo mật/hiệu năng).

## Padding Schemes Comparison
| Operation | Legacy (v1.5) | Modern (v2.2) | Project |
|-----------|---------------|---------------|---------|
| Encryption | PKCS#1 v1.5 | **OAEP (SHA-256)** | ✓ OAEP |
| Signature | PKCS#1 v1.5 | **PSS (SHA-256)** | ✓ PSS |

## Bảo mật & Tấn công
- **Brute-force**: Phân tích thừa số n → cần GNFS (General Number Field Sieve), 2048-bit chưa phá được
- **Side-channel**: Timing attack, power analysis → dùng constant-time, blinding
- **Fault attack**: Bellcore attack (CRT) → verify signature sau khi ký
- **Padding oracle**: Bleichenbacher (PKCS#1 v1.5) → **dùng OAEP/PSS**
- **Quantum**: Shor's algorithm phá RSA trong polynomial time → **post-quantum: lattice-based (Kyber, Dilithium)**

## Project Implementation
```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Key generation
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Encryption (OAEP)
ciphertext = public_key.encrypt(plaintext, padding.OAEP(
    mgf=padding.MGF1(hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None
))

# Decryption
plaintext = private_key.decrypt(ciphertext, padding.OAEP(...))

# Signature (PSS)
signature = private_key.sign(message, padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH
), hashes.SHA256())

# Verify
public_key.verify(signature, message, padding.PSS(...), hashes.SHA256())
```

## So sánh RSA vs AES
| Tiêu chí | RSA (Asymmetric) | AES (Symmetric) |
|----------|------------------|-----------------|
| Key type | Public/Private | Single secret |
| Speed | Chậm (~ms/op) | Nhanh (~μs/op) |
| Key size | 2048-4096-bit | 128-256-bit |
| Data size | Limited (≤ key size) | Unlimited (streaming) |
| Use case | Key exchange, Signature | Bulk encryption |
| Quantum | Broken (Shor) | Weakened (Grover → 256-bit OK) |

## Hybrid Encryption (RSA + AES)
```
Sender:
1. K_aes = random 128-bit
2. C_data = AES-GCM(K_aes, data)
3. C_key = RSA-OAEP(K_pub, K_aes)
4. Send: C_key || C_data || nonce

Receiver:
1. K_aes = RSA-OAEP(K_priv, C_key)
2. data = AES-GCM(K_aes, C_data, nonce)
```
Ưu điểm: Tốc độ AES + Key management RSA.

## Tham khảo
- RFC 8017 (PKCS#1 v2.2)
- FIPS 186-4 (Digital Signature Standard)
- NIST SP 800-56B (RSA key establishment)
- "Handbook of Applied Cryptography" - Menezes et al.
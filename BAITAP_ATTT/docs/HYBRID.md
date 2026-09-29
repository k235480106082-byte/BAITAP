# Hybrid Encryption: RSA + AES

## Tổng quan

Hybrid encryption kết hợp ưu điểm của cả hai:
- **AES**: Nhanh, phù hợp cho dữ liệu lớn (bulk encryption)
- **RSA**: Key exchange an toàn, không cần shared secret trước

## Vấn đề của từng thuật toán riêng lẻ

| Thuật toán | Vấn đề |
|------------|--------|
| **RSA đơn độc** | - Chậm (~ms/op)<br>- Giới hạn dữ liệu: ≤ key size (RSA-2048 OAEP: ~190 bytes)<br>- Không phù hợp stream/file lớn |
| **AES đơn độc** | - Cần shared secret key trước<br>- Key distribution problem<br>- Không có non-repudiation |

## Giải pháp Hybrid

```
SENDER                                          RECEIVER
------                                          --------
Plaintext                                      
    ↓                                          
Sinh AES session key (ngẫu nhiên 16 bytes)     
    ↓                                          
AES-GCM encrypt(plaintext, session_key)        
    ↓                                          ↓
Ciphertext + Nonce              ←───────────────│
    ↓                                           │
RSA-OAEP encrypt(session_key, pk_R)             │
    ↓                                           │
Encrypted_Session_Key  ←────────────────────────┘
    ↓                                          
Gửi: Encrypted_Session_Key + Ciphertext + Nonce
```

### Quy trình chi tiết

#### Sender (Encryption)
1. **Sinh session key**: `K_aes = random(16 bytes)`
2. **AES Encrypt**: 
   - `nonce = random(12 bytes)`
   - `ciphertext = AES-GCM(K_aes, nonce, plaintext)`
3. **RSA Encrypt key**:
   - `enc_key = RSA-OAEP(pk_R, K_aes)`
4. **Output**: `(enc_key, ciphertext, nonce)` (tất cả base64)

#### Receiver (Decryption)
1. **RSA Decrypt key**:
   - `K_aes = RSA-OAEP(sk_R, enc_key)`
2. **AES Decrypt**:
   - `plaintext = AES-GCM(K_aes, nonce, ciphertext)`
3. **Output**: `plaintext`

## Ưu điểm

1. **Hiệu năng**: AES mã hóa dữ liệu lớn (~GB/s), RSA chỉ mã hóa 16-byte key
2. **Bảo mật**: 
    - Session key được sinh ngẫu nhiên cho mỗi lần mã hóa (ephemeral)
    - Key không bao giờ truyền plaintext
    - AES-GCM cung cấp AEAD (authenticated encryption)
    - **Implementation hiện tại KHÔNG cung cấp Forward Secrecy** do dùng RSA key transport với RSA key cố định
3. **Linh hoạt**: Session key có thể dùng cho multiple messages
4. **Standard**: TLS 1.3, SSH, PGP, Signal Protocol đều dùng hybrid

## Bảo mật

### Yêu cầu
- Session key phải **ngẫu nhiên** mỗi lần (CSPRNG: `os.urandom()`)
- Nonce **không bao giờ reuse** với cùng AES key
- RSA key size ≥ 2048-bit (khuyên 3072-bit cho lâu dài)
- Kiểm tra padding oracle (OAEP tự chống)

### Tấn công & Phòng thủ

| Tấn công | Phòng thủ |
|----------|-----------|
| Replay attack | Nonce unique, timestamp, sequence number |
| Key compromise | Ephemeral session key (nhưng **KHÔNG** có Forward Secrecy do static RSA key) |
| Padding oracle | OAEP (thay vì PKCS#1 v1.5) |
| MITM | Verify public key fingerprint/certificate |
| Quantum | Post-quantum KEM (Kyber) + AES-256 |

## Implementation trong Project

### Module: `src/hybrid/hybrid_demo.py`

```python
from src.hybrid.hybrid_demo import hybrid_encrypt, hybrid_decrypt
from src.rsa.rsa_demo import generate_rsa_keypair

# Generate keys
private_key, public_key = generate_rsa_keypair(2048)

# Encrypt
encrypted = hybrid_encrypt("Large plaintext data...", public_key)
# Returns: {'encrypted_key': '...', 'ciphertext': '...', 'nonce': '...'}

# Decrypt
plaintext = hybrid_decrypt(encrypted, private_key)
```

### Cấu trúc Output
```json
{
  "encrypted_key": "base64(RSA-OAEP(AES_key))",
  "ciphertext": "base64(AES-GCM(plaintext))",
  "nonce": "base64(12_bytes)"
}
```

## So sánh Effectiveness

### Data size vs Method
| Data Size | RSA Only | Hybrid (RSA+AES) |
|-----------|----------|------------------|
| 16 bytes | ✓ Works | ✓ Works |
| 100 bytes | ✓ Works | ✓ Works |
| 1 KB | ✗ Too large | ✓ Works |
| 1 MB | ✗ Impossible | ✓ Works |
| 1 GB | ✗ Impossible | ✓ Works |

### Performance (từ benchmark)
| Operation | Time (64 bytes) | Throughput |
|-----------|-----------------|------------|
| AES Encrypt | ~2 μs | ~31 MB/s |
| AES Decrypt | ~1.5 μs | ~42 MB/s |
| RSA Encrypt | ~45 μs | ~1.4 MB/s |
| RSA Decrypt | ~700 μs | ~0.09 MB/s |

**→ AES nhanh hơn RSA ~23x (encrypt) đến ~480x (decrypt)**

## TLS 1.3 Hybrid Flow (Reference)

```
Client                          Server
------                          ------
ClientHello (key_share) ──────→
←──────── ServerHello (key_share)
Derive shared secret (ECDHE)
Derive traffic keys (HKDF)
AES-GCM encrypt application data
```

- TLS 1.3 dùng **(EC)DHE** cho key exchange (forward secrecy)
- Project dùng **RSA** cho đơn giản (key transport)
- Production nên dùng ECDHE thay RSA key transport

## Hạn chế Project
1. **Key transport** thay vì key agreement (không có forward secrecy)
2. **Static RSA key** - nếu sk_R bị lộ, tất cả session key bị compromize
3. **No key rotation** - session key dùng một lần nhưng master key cố định
4. **No authentication** - cần kết hợp với digital signature cho authenticated encryption

## Cải tiến cho Production
1. **Ephemeral key exchange**: ECDHE (X25519) thay RSA key transport
2. **Key derivation**: HKDF từ shared secret
3. **Key rotation**: Rekey sau N bytes/time
4. **Authenticated encryption**: Kết hợp sender auth (sign-then-encrypt)
5. **Post-quantum**: Kyber KEM + AES-256-GCM

## Tham khảo
- RFC 8446 (TLS 1.3) - Key Schedule, Key Derivation
- NIST SP 800-56A - Key Establishment (ECDHE)
- NIST SP 800-56B - Key Establishment (RSA)
- Signal Protocol Specification - Double Ratchet
- RFC 9180 (HPKE) - Hybrid Public Key Encryption
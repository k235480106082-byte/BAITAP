# Authentication Mechanisms

## 1. Sender Authentication (Digital Signature)

### Mục đích
Chứng minh danh tính người gửi (Sender) và tính toàn vẹn của tin nhắn.

### Luồng hoạt động
```
Sender                              Receiver
-----                               --------
1. Có private key (sk_S)
2. Tạo message M
3. Signature = Sign(sk_S, M)
4. Gửi: M, Signature
                                    5. Có public key (pk_S)
                                    6. Verify(pk_S, M, Signature)
                                    7. PASS → Sender authenticated
```

### Thuật toán
- **Sign**: RSA-PSS với SHA-256
- **Verify**: RSA-PSS với SHA-256
- Padding: PSS (Probabilistic Signature Scheme) - an toàn hơn PKCS#1 v1.5

### Đặc điểm bảo mật
- ✓ Chỉ Sender có private key → chỉ Sender mới tạo được signature hợp lệ
- ✓ Signature gắn liền với message → phát hiện được tampering
- ✓ Non-repudiation: Sender không thể từ chối đã gửi
- ✓ PSS có salt ngẫu nhiên → cùng message tạo signature khác nhau

### Test cases
| Test | Kết quả kỳ vọng |
|------|-----------------|
| Message đúng + Signature đúng | PASS |
| Message bị sửa | FAIL |
| Signature bị sửa | FAIL |
| Sai public key | FAIL |
| Message rỗng | PASS |
| Unicode message | PASS |

## 2. Receiver Authentication (Challenge-Response)

### Mục đích
Chứng minh người nhận (Receiver) thực sự sở hữu private key tương ứng với public key mà Sender tin tưởng.

> **Lưu ý quan trọng**: Mã hóa bằng public key KHÔNG tự động xác thực người nhận. Chỉ có challenge-response (hoặc zero-knowledge proof) mới chứng minh được quyền sở hữu private key.

### Luồng hoạt động
```
Sender                              Receiver
-----                               --------
1. Có public key (pk_R) của Receiver
2. Tạo challenge ngẫu nhiên C
3. Gửi challenge C
                                    4. Có private key (sk_R)
                                    5. Response = Sign(sk_R, C)
                                    6. Gửi Response
7. Verify(pk_R, C, Response)
8. PASS → Receiver authenticated
```

### Tại sao cần challenge ngẫu nhiên?
- **Replay attack**: Nếu challenge cố định, attacker có thể replay response cũ
- **Freshness**: Challenge mới mỗi lần đảm bảo response là fresh
- **Unpredictability**: Attacker không thể đoán trước challenge

### Thuật toán
- **Challenge**: 32 bytes random (CSPRNG)
- **Response**: RSA-PSS với SHA-256 ký challenge
- **Verify**: RSA-PSS với SHA-256

### Test cases
| Test | Kết quả kỳ vọng |
|------|-----------------|
| Challenge đúng + Response đúng | PASS |
| Challenge sai (replay) | FAIL |
| Response bị sửa | FAIL |
| Sai public key | FAIL |
| Challenge unique mỗi lần | PASS |

## 3. Mutual Authentication (Hai chiều)

### Mục đích
Cả Sender và Receiver đều chứng minh danh tính lẫn nhau trước khi thiết lập session.

### Luồng hoạt động
```
Sender                              Receiver
-----                               --------
1. Sinh key pair (sk_S, pk_S)
2. Sinh key pair (sk_R, pk_R)
                                    3. Có pk_S, pk_R (trusted)
                                    
4. Sender Auth:
   Msg = "Hello from Sender"
   Sig = Sign(sk_S, Msg)
   → Msg, Sig
                                    5. Verify(pk_S, Msg, Sig) → PASS
                                    
                                    6. Receiver Auth:
                                       Challenge = random()
                                       → Challenge
7. Response = Sign(sk_R, Challenge)
   → Response
                                    8. Verify(pk_R, Challenge, Response) → PASS
                                    
9. Cả 2 authenticated → thiết lập session key
```

### Kết quả
- Sender authentication: PASS
- Receiver authentication: PASS
- Anti-impersonation: PASS (Sender key không thể giả mạo Receiver)

### Tấn công giả mạo (Impersonation)
Attacker cố dùng sk_S để ký challenge thay vì sk_R:
```
Fake_Response = Sign(sk_S, Challenge)
Verify(pk_R, Challenge, Fake_Response) → FAIL
```
→ Bị chặn vì public key không khớp.

## So sánh

| Tiêu chí | Sender Auth | Receiver Auth |
|----------|-------------|---------------|
| Chứng minh | Identity của Sender | Possession của private key |
| Cơ chế | Digital Signature | Challenge-Response |
| Non-repudiation | Có | Không (chỉ proof of possession) |
| Replay protection | Không cần (message unique) | Cần challenge ngẫu nhiên |
| Use case | Email signing, Document signing | TLS client auth, SSH login |

## Implementation trong Project

### Module: `src/auth/auth_demo.py`

```python
# Sender Authentication
signature = sign_message(message, sender_private_key)
verified = verify_signature(message, signature, sender_public_key)

# Receiver Authentication
challenge = generate_challenge(32)
response = sign_challenge(challenge, receiver_private_key)
verified = verify_challenge_response(challenge, response, receiver_public_key)

# Mutual Authentication
run_mutual_auth_demo()  # Chạy cả hai luồng
```

### Thư viện sử dụng
- `cryptography.hazmat.primitives.asymmetric.padding.PSS`
- `cryptography.hazmat.primitives.hashes.SHA256`
- `os.urandom()` cho CSPRNG

## Hạn chế
1. **Key distribution**: Cần PKI hoặc trusted channel để exchange public keys
2. **No forward secrecy**: Nếu private key bị lộ, các session trước bị compromize
3. **No encryption**: Authentication riêng không cung cấp confidentiality
4. **Quantum vulnerable**: RSA bị phá bởi Shor's algorithm

## Tham khảo
- RFC 8017 (PKCS#1 v2.2) - RSA-PSS
- RFC 8446 (TLS 1.3) - CertificateVerify, Finished
- NIST SP 800-56B - Key establishment
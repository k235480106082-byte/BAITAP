# Performance Benchmark: AES vs RSA

## Mục đích
Đo và so sánh hiệu năng mã hóa/giải mã giữa AES-128-GCM và RSA-2048-OAEP.

## Môi trường test tham khảo
Kết quả dưới đây được đo trên một môi trường cụ thể. **Kết quả sẽ khác nhau trên CPU/OS/Python/OpenSSL khác nhau.**

- **Python**: 3.11.9
- **Platform**: Windows 10 (10.0.26200)
- **Processor**: AMD64 Family 25 Model 80
- **Thư viện**: cryptography 50.0.1 (OpenSSL backend)
- **RSA Key Size**: 2048-bit
- **AES Config**: AES-128-GCM, 96-bit nonce
- **Iterations**: 50 runs per test (quick benchmark)

> **Lưu ý quan trọng**: Các con số dưới đây chỉ mang tính chất minh họa tham khảo trên môi trường test cụ thể. Không phải là thông số kỹ thuật cố định. Thực tế hiệu năng phụ thuộc mạnh vào: CPU (AES-NI support), OS, Python version, OpenSSL version, background load, power management, v.v.

## Kết quả đo được (MÔI TRƯỜNG THAM KHẢO)

### Thời gian trung bình (Average Time)

| Data Size | AES Encrypt | AES Decrypt | RSA Encrypt | RSA Decrypt |
|-----------|-------------|-------------|-------------|-------------|
| 64 B      | ~1.6-2.0 μs | ~1.2-1.5 μs | ~42-55 μs   | ~680-770 μs |
| 256 B     | ~1.3-2.2 μs | ~1.2-1.7 μs | N/A         | N/A         |
| 1 KB      | ~1.7-2.0 μs | ~1.4-1.9 μs | N/A         | N/A         |

> **Lưu ý**: RSA-2048 OAEP/SHA-256 tối đa mã hóa được ~190 bytes. Dữ liệu lớn hơn phải dùng Hybrid.

### Speedup tham chiếu: AES vs RSA (Encryption, 64 bytes)

| Data Size | Speedup tham chiếu (RSA/AES) |
|-----------|------------------------------|
| 64 B      | ~17x - ~40x faster           |

### Throughput tham chiếu (MB/s)

| Data Size | AES Encrypt | AES Decrypt | RSA Encrypt | RSA Decrypt |
|-----------|-------------|-------------|-------------|-------------|
| 64 B      | ~16-37 MB/s | ~29-51 MB/s | ~0.4-1.4 MB/s | ~0.08-0.09 MB/s |
| 256 B     | ~83-186 MB/s | ~136-203 MB/s | N/A         | N/A         |
| 1 KB      | ~492-585 MB/s | ~521-695 MB/s | N/A         | N/A         |

## Phân tích (Dựa trên xu hướng quan sát được)

### 1. AES nhanh hơn RSA rất nhiều
- **Encryption**: AES thường nhanh hơn RSA một bậc độ lớn (thường 10x-50x tùy môi trường)
- **Decryption**: AES nhanh hơn RSA nhiều hơn (thường 100x-500x) do RSA private key operation tốn kém
- **Lý do**: AES là symmetric cipher (single operation có hardware acceleration AES-NI), RSA là asymmetric (modular exponentiation với số 2048-bit, khó tối ưu hóa phần cứng)

### 2. AES throughput scale tốt với data size
- Throughput AES tăng gần tuyến tính với kích thước dữ liệu (streaming mode)
- RSA throughput thấp và không scale (block cipher, chi phí cố định cao)

### 3. RSA giới hạn kích thước dữ liệu
```
RSA-2048 OAEP/SHA-256 max input = key_size/8 - 2*hash_len - 2
                              = 256 - 64 - 2
                              = 190 bytes
```
Dữ liệu > 190 bytes → **không thể mã hóa trực tiếp bằng RSA**.

## Kết luận từ quan sát

1. **RSA KHÔNG phù hợp** mã hóa dữ liệu lớn trực tiếp
2. **AES phù hợp** cho bulk encryption (file, stream, database)
3. **Hybrid (RSA + AES)** là giải pháp thực tế:
   - RSA bảo vệ AES session key (16 bytes)
   - AES mã hóa dữ liệu thực tế
4. **RSA decrypt chậm hơn encrypt** rất nhiều (private key operation phức tạp hơn)

## Khuyến nghị

| Use Case | Thuật toán khuyến nghị |
|----------|------------------------|
| File encryption | AES-256-GCM |
| Key exchange | RSA-2048/3072 OAEP hoặc ECDHE |
| TLS/HTTPS | ECDHE + AES-GCM (TLS 1.3) |
| Email encryption | Hybrid (RSA + AES) như PGP |
| Database encryption | AES-256-GCM |
| Digital signature | RSA-PSS hoặc Ed25519 |

## Benchmark Code

```python
from src.benchmark.benchmark import run_benchmark

# Quick benchmark
results = run_benchmark(
    data_sizes=[64, 256, 1024],
    iterations=50,
    rsa_key_size=2048
)

# Full benchmark
results = run_benchmark(
    data_sizes=[16, 64, 256, 1024, 4096, 16384],
    iterations=100,
    rsa_key_size=2048
)
```

## Hạn chế Benchmark
1. **Môi trường**: Windows, Python interpreter overhead
2. **JIT/Compiler**: Không có JIT (PyPy nhanh hơn CPython)
3. **Hardware acceleration**: AES-NI, CLMUL có thể không được bật đầy đủ
4. **Single-threaded**: Không test multi-threading
5. **Cold start**: Lần đầu chạy chậm hơn do module loading
6. **Sample size**: 50 iterations (quick), 100+ cho production benchmark
7. **Biến động**: Kết quả có thể biến động 2-5x giữa các lần chạy do OS scheduling, CPU frequency scaling

## Tham khảo
- NIST SP 800-38D (AES-GCM)
- RFC 8017 (RSA-OAEP)
- OpenSSL Speed Benchmark
- cryptography.io Performance Notes
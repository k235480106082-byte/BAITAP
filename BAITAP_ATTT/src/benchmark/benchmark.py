"""
Performance Benchmark: AES vs RSA
"""

import os
import time
import statistics
import platform
import sys
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_rsa_keypair(key_size: int = 2048):
    """Generate RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return private_key, public_key


# ============================================================
# Benchmark Functions
# ============================================================

def benchmark_aes_encrypt(data: bytes, key: bytes, iterations: int) -> list:
    """Benchmark AES-GCM encryption"""
    aesgcm = AESGCM(key)
    times = []
    for _ in range(iterations):
        nonce = os.urandom(12)
        start = time.perf_counter()
        aesgcm.encrypt(nonce, data, None)
        end = time.perf_counter()
        times.append(end - start)
    return times


def benchmark_aes_decrypt(ciphertext: bytes, nonce: bytes, key: bytes, iterations: int) -> list:
    """Benchmark AES-GCM decryption"""
    aesgcm = AESGCM(key)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        aesgcm.decrypt(nonce, ciphertext, None)
        end = time.perf_counter()
        times.append(end - start)
    return times


def benchmark_rsa_encrypt(data: bytes, public_key, iterations: int) -> list:
    """Benchmark RSA-OAEP encryption"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        end = time.perf_counter()
        times.append(end - start)
    return times


def benchmark_rsa_decrypt(ciphertext: bytes, private_key, iterations: int) -> list:
    """Benchmark RSA-OAEP decryption"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        end = time.perf_counter()
        times.append(end - start)
    return times


def format_time(seconds: float) -> str:
    """Format time in appropriate units"""
    if seconds >= 1:
        return f"{seconds:.4f} s"
    elif seconds >= 0.001:
        return f"{seconds*1000:.2f} ms"
    elif seconds >= 0.000001:
        return f"{seconds*1000000:.2f} us"
    else:
        return f"{seconds*1000000000:.2f} ns"


def run_benchmark(data_sizes: list = None, iterations: int = 100, rsa_key_size: int = 2048):
    """Run comprehensive benchmark"""
    if data_sizes is None:
        data_sizes = [16, 64, 256, 1024, 4096, 16384]  # bytes
    
    print("\n" + "="*70)
    print("           PERFORMANCE BENCHMARK: AES vs RSA")
    print("="*70)
    
    # System info
    print(f"\n[System Info]")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  RSA Key Size: {rsa_key_size}-bit")
    print(f"  AES Mode: AES-128-GCM")
    print(f"  Iterations per test: {iterations}")
    
    # Generate keys once
    print("\n[1] Generating RSA key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=rsa_key_size
    )
    public_key = private_key.public_key()
    print("    [+] Done")
    
    # AES key
    aes_key = os.urandom(16)
    
    results = []
    
    for size in data_sizes:
        print(f"\n[2] Testing with {size} bytes data...")
        data = os.urandom(size)
        
        # AES Encrypt
        aes_enc_times = benchmark_aes_encrypt(data, aes_key, iterations)
        aes_enc_avg = statistics.mean(aes_enc_times)
        
        # AES Decrypt (need ciphertext first)
        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        aes_dec_times = benchmark_aes_decrypt(ciphertext, nonce, aes_key, iterations)
        aes_dec_avg = statistics.mean(aes_dec_times)
        
        # RSA Encrypt (only if data fits)
        # RSA-2048 OAEP max: 2048/8 - 2*32 - 2 = 256 - 64 - 2 = 190 bytes
        max_rsa_size = (rsa_key_size // 8) - 2 * (256 // 8) - 2  # OAEP overhead
        if size <= max_rsa_size:
            rsa_enc_times = benchmark_rsa_encrypt(data, public_key, iterations)
            rsa_enc_avg = statistics.mean(rsa_enc_times)
            
            rsa_ciphertext = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            rsa_dec_times = benchmark_rsa_decrypt(rsa_ciphertext, private_key, iterations)
            rsa_dec_avg = statistics.mean(rsa_dec_times)
        else:
            rsa_enc_avg = None
            rsa_dec_avg = None
        
        # Store results
        results.append({
            'size': size,
            'aes_enc_avg': aes_enc_avg,
            'aes_dec_avg': aes_dec_avg,
            'rsa_enc_avg': rsa_enc_avg,
            'rsa_dec_avg': rsa_dec_avg
        })
        
        # Print row
        print(f"  AES Encrypt: {format_time(aes_enc_avg):>12} | AES Decrypt: {format_time(aes_dec_avg):>12}", end="")
        if rsa_enc_avg:
            print(f" | RSA Encrypt: {format_time(rsa_enc_avg):>12} | RSA Decrypt: {format_time(rsa_dec_avg):>12}")
        else:
            print(" | RSA: N/A (data too large)")
    
    # Summary table
    print("\n" + "="*70)
    print("                    SUMMARY (Average Time)")
    print("="*70)
    print(f"{'Data Size':>10} | {'AES Enc':>12} | {'AES Dec':>12} | {'RSA Enc':>12} | {'RSA Dec':>12}")
    print("-"*70)
    
    for r in results:
        size_str = f"{r['size']} B"
        aes_enc = format_time(r['aes_enc_avg'])
        aes_dec = format_time(r['aes_dec_avg'])
        rsa_enc = format_time(r['rsa_enc_avg']) if r['rsa_enc_avg'] else "N/A"
        rsa_dec = format_time(r['rsa_dec_avg']) if r['rsa_dec_avg'] else "N/A"
        print(f"{size_str:>10} | {aes_enc:>12} | {aes_dec:>12} | {rsa_enc:>12} | {rsa_dec:>12}")
    
    # Speedup comparison (for sizes where both work)
    print("\n" + "="*70)
    print("                    SPEEDUP: AES vs RSA (Encryption)")
    print("="*70)
    for r in results:
        if r['rsa_enc_avg'] and r['aes_enc_avg'] > 0:
            speedup = r['rsa_enc_avg'] / r['aes_enc_avg']
            print(f"  {r['size']:>6} B: AES is {speedup:.0f}x faster than RSA")
    
    # Throughput
    print("\n" + "="*70)
    print("                    THROUGHPUT (MB/s)")
    print("="*70)
    for r in results:
        aes_enc_mb = (r['size'] / r['aes_enc_avg']) / (1024*1024) if r['aes_enc_avg'] > 0 else 0
        aes_dec_mb = (r['size'] / r['aes_dec_avg']) / (1024*1024) if r['aes_dec_avg'] > 0 else 0
        print(f"  {r['size']:>6} B: AES Enc {aes_enc_mb:.1f} MB/s | AES Dec {aes_dec_mb:.1f} MB/s", end="")
        if r['rsa_enc_avg']:
            rsa_enc_mb = (r['size'] / r['rsa_enc_avg']) / (1024*1024)
            rsa_dec_mb = (r['size'] / r['rsa_dec_avg']) / (1024*1024)
            print(f" | RSA Enc {rsa_enc_mb:.3f} MB/s | RSA Dec {rsa_dec_mb:.3f} MB/s")
        else:
            print()
    
    print("\n[Note] RSA is not suitable for large data encryption.")
    print("       Use Hybrid (RSA for key, AES for data) in practice.")
    
    return results


def run_quick_benchmark():
    """Quick benchmark for demo"""
    return run_benchmark(
        data_sizes=[64, 256, 1024],
        iterations=50,
        rsa_key_size=2048
    )


if __name__ == "__main__":
    run_benchmark()
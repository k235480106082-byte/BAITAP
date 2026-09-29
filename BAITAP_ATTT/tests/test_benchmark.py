"""
Unit Tests for Benchmark Module
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.benchmark.benchmark import (
    benchmark_aes_encrypt, benchmark_aes_decrypt,
    benchmark_rsa_encrypt, benchmark_rsa_decrypt,
    generate_rsa_keypair, run_benchmark
)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TestBenchmark(unittest.TestCase):
    
    def setUp(self):
        self.private_key, self.public_key = generate_rsa_keypair(2048)
        self.aes_key = os.urandom(16)
        # Use smaller data for RSA (max ~190 bytes for RSA-2048 OAEP)
        self.rsa_data = os.urandom(100)
        self.aes_data = os.urandom(256)
        self.iterations = 10
    
    def test_aes_encrypt_returns_times(self):
        """AES encrypt benchmark returns list of times"""
        times = benchmark_aes_encrypt(self.aes_data, self.aes_key, self.iterations)
        self.assertEqual(len(times), self.iterations)
        self.assertTrue(all(t > 0 for t in times))
    
    def test_aes_decrypt_returns_times(self):
        """AES decrypt benchmark returns list of times"""
        aesgcm = AESGCM(self.aes_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, self.aes_data, None)
        times = benchmark_aes_decrypt(ciphertext, nonce, self.aes_key, self.iterations)
        self.assertEqual(len(times), self.iterations)
        self.assertTrue(all(t > 0 for t in times))
    
    def test_rsa_encrypt_returns_times(self):
        """RSA encrypt benchmark returns list of times for valid data size"""
        times = benchmark_rsa_encrypt(self.rsa_data, self.public_key, self.iterations)
        self.assertEqual(len(times), self.iterations)
        self.assertTrue(all(t > 0 for t in times))
    
    def test_rsa_decrypt_returns_times(self):
        """RSA decrypt benchmark returns list of times"""
        ciphertext = self.public_key.encrypt(
            self.rsa_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        times = benchmark_rsa_decrypt(ciphertext, self.private_key, self.iterations)
        self.assertEqual(len(times), self.iterations)
        self.assertTrue(all(t > 0 for t in times))
    
    def test_rsa_encrypt_fails_for_large_data(self):
        """RSA encrypt should fail for data larger than OAEP limit"""
        large_data = os.urandom(200)  # > 190 bytes limit
        with self.assertRaises(Exception):
            benchmark_rsa_encrypt(large_data, self.public_key, self.iterations)
    
    def test_benchmark_returns_valid_results(self):
        """run_benchmark should return valid results structure"""
        results = run_benchmark(
            data_sizes=[64, 256],
            iterations=5,
            rsa_key_size=2048
        )
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn('size', r)
            self.assertIn('aes_enc_avg', r)
            self.assertIn('aes_dec_avg', r)
            self.assertIn('rsa_enc_avg', r)
            self.assertIn('rsa_dec_avg', r)
            self.assertGreater(r['aes_enc_avg'], 0)
            self.assertGreater(r['aes_dec_avg'], 0)
            # 64 bytes should have RSA results, 256 should not
            if r['size'] <= 190:
                self.assertIsNotNone(r['rsa_enc_avg'])
                self.assertIsNotNone(r['rsa_dec_avg'])
                self.assertGreater(r['rsa_enc_avg'], 0)
                self.assertGreater(r['rsa_dec_avg'], 0)
            else:
                self.assertIsNone(r['rsa_enc_avg'])
                self.assertIsNone(r['rsa_dec_avg'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
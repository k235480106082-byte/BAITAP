"""
Unit Tests for RSA-2048
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.rsa.rsa_demo import (
    generate_rsa_keypair, 
    encrypt_rsa, 
    decrypt_rsa, 
    sign_rsa, 
    verify_rsa,
    serialize_private_key,
    serialize_public_key,
    load_private_key,
    load_public_key,
    get_key_info
)


class TestRSA(unittest.TestCase):
    
    def setUp(self):
        self.private_key, self.public_key = generate_rsa_keypair(2048)
    
    def test_key_generation(self):
        """Test tạo cặp khóa"""
        self.assertIsNotNone(self.private_key)
        self.assertIsNotNone(self.public_key)
        self.assertEqual(self.private_key.key_size, 2048)
    
    def test_key_info_math(self):
        """Test RSA math: e * d = 1 (mod lambda(n)) where lambda = lcm(p-1, q-1)"""
        import math
        info = get_key_info(self.private_key, self.public_key)
        lambda_n = (info['p'] - 1) * (info['q'] - 1) // math.gcd(info['p'] - 1, info['q'] - 1)
        self.assertEqual((info['e'] * info['d']) % lambda_n, 1)
        self.assertEqual(info['n'], info['p'] * info['q'])
    
    def test_ascii_text(self):
        """Test mã hóa/giải mã văn bản ASCII"""
        plaintext = "Hello, RSA World!"
        ciphertext = encrypt_rsa(plaintext, self.public_key)
        decrypted = decrypt_rsa(ciphertext, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_vietnamese_text(self):
        """Test mã hóa/giải mã tiếng Việt Unicode"""
        plaintext = "Xin chào Việt Nam! 🇻🇳 Tiếng Việt: àáảãạăắằẳẵặâấầẩẫậ"
        ciphertext = encrypt_rsa(plaintext, self.public_key)
        decrypted = decrypt_rsa(ciphertext, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_special_characters(self):
        """Test với ký tự đặc biệt"""
        plaintext = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        ciphertext = encrypt_rsa(plaintext, self.public_key)
        decrypted = decrypt_rsa(ciphertext, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_multiple_encryptions_different_ciphertext(self):
        """Mỗi lần mã hóa cho ciphertext khác nhau (OAEP randomness)"""
        plaintext = "Test OAEP randomness"
        ct1 = encrypt_rsa(plaintext, self.public_key)
        ct2 = encrypt_rsa(plaintext, self.public_key)
        self.assertNotEqual(ct1, ct2)
        # Nhưng giải mã cùng ra kết quả
        self.assertEqual(decrypt_rsa(ct1, self.private_key), plaintext)
        self.assertEqual(decrypt_rsa(ct2, self.private_key), plaintext)
    
    def test_wrong_key_fails(self):
        """Sai private key phải báo lỗi"""
        plaintext = "Test wrong key"
        ciphertext = encrypt_rsa(plaintext, self.public_key)
        other_private, _ = generate_rsa_keypair(2048)
        with self.assertRaises(Exception):
            decrypt_rsa(ciphertext, other_private)
    
    def test_tampered_ciphertext_fails(self):
        """Ciphertext bị sửa đổi phải báo lỗi"""
        plaintext = "Test tampering"
        ciphertext = encrypt_rsa(plaintext, self.public_key)
        # Sửa ciphertext
        import base64
        ct_bytes = bytearray(base64.b64decode(ciphertext))
        if len(ct_bytes) > 0:
            ct_bytes[0] ^= 0xFF
        tampered = base64.b64encode(ct_bytes).decode('ascii')
        with self.assertRaises(Exception):
            decrypt_rsa(tampered, self.private_key)
    
    def test_key_serialization(self):
        """Test serialize/deserialize keys"""
        private_pem = serialize_private_key(self.private_key)
        public_pem = serialize_public_key(self.public_key)
        
        loaded_private = load_private_key(private_pem)
        loaded_public = load_public_key(public_pem)
        
        # Test loaded keys work
        plaintext = "Test serialization"
        ciphertext = encrypt_rsa(plaintext, loaded_public)
        decrypted = decrypt_rsa(ciphertext, loaded_private)
        self.assertEqual(decrypted, plaintext)
    
    def test_digital_signature(self):
        """Test ký số và xác thực"""
        message = "Tài liệu cần ký số"
        signature = sign_rsa(message, self.private_key)
        
        # Xác thực chữ ký đúng
        self.assertTrue(verify_rsa(message, signature, self.public_key))
        
        # Chữ ký sai cho message khác
        self.assertFalse(verify_rsa(message + " tampered", signature, self.public_key))
        
        # Chữ ký sai cho key khác
        _, other_public = generate_rsa_keypair(2048)
        self.assertFalse(verify_rsa(message, signature, other_public))
    
    def test_signature_tampering(self):
        """Test chữ ký bị sửa đổi"""
        message = "Test signature tampering"
        signature = sign_rsa(message, self.private_key)
        import base64
        sig_bytes = bytearray(base64.b64decode(signature))
        if len(sig_bytes) > 0:
            sig_bytes[0] ^= 0xFF
        tampered = base64.b64encode(sig_bytes).decode('ascii')
        self.assertFalse(verify_rsa(message, tampered, self.public_key))
    
    def test_invalid_input_handling(self):
        """Test xử lý input không hợp lệ"""
        # Ciphertext không phải base64 hợp lệ
        with self.assertRaises(Exception):
            decrypt_rsa("not-base64!", self.private_key)
        
        # Signature không phải base64
        self.assertFalse(verify_rsa("test", "not-base64!", self.public_key))


if __name__ == '__main__':
    unittest.main(verbosity=2)
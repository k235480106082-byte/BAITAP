"""
Unit Tests for AES-128-GCM
"""

import unittest
import sys
import os
import base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.aes.aes_demo import generate_aes_key, encrypt_aes, decrypt_aes


class TestAES(unittest.TestCase):
    
    def setUp(self):
        self.key = generate_aes_key()
    
    def test_ascii_text(self):
        """Test mã hóa/giải mã văn bản ASCII"""
        plaintext = "Hello, World! This is a test."
        result = encrypt_aes(plaintext, self.key)
        decrypted = decrypt_aes(result['ciphertext'], result['nonce'], self.key)
        self.assertEqual(decrypted, plaintext)
        self.assertNotEqual(result['ciphertext'], plaintext)
    
    def test_vietnamese_text(self):
        """Test mã hóa/giải mã tiếng Việt Unicode"""
        plaintext = "Xin chào Việt Nam! 🇻🇳 Tiếng Việt có dấu: àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
        result = encrypt_aes(plaintext, self.key)
        decrypted = decrypt_aes(result['ciphertext'], result['nonce'], self.key)
        self.assertEqual(decrypted, plaintext)
        self.assertNotEqual(result['ciphertext'], plaintext)
    
    def test_empty_text(self):
        """Test với chuỗi rỗng"""
        plaintext = ""
        result = encrypt_aes(plaintext, self.key)
        decrypted = decrypt_aes(result['ciphertext'], result['nonce'], self.key)
        self.assertEqual(decrypted, plaintext)
    
    def test_special_characters(self):
        """Test với ký tự đặc biệt"""
        plaintext = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        result = encrypt_aes(plaintext, self.key)
        decrypted = decrypt_aes(result['ciphertext'], result['nonce'], self.key)
        self.assertEqual(decrypted, plaintext)
    
    def test_long_text(self):
        """Test với văn bản dài"""
        plaintext = "A" * 10000  # 10KB
        result = encrypt_aes(plaintext, self.key)
        decrypted = decrypt_aes(result['ciphertext'], result['nonce'], self.key)
        self.assertEqual(decrypted, plaintext)
    
    def test_different_keys_produce_different_ciphertext(self):
        """Khóa khác nhau phải cho ciphertext khác nhau"""
        plaintext = "Same plaintext"
        key1 = generate_aes_key()
        key2 = generate_aes_key()
        result1 = encrypt_aes(plaintext, key1)
        result2 = encrypt_aes(plaintext, key2)
        self.assertNotEqual(result1['ciphertext'], result2['ciphertext'])
    
    def test_same_key_different_nonce(self):
        """Cùng khóa, nonce khác nhau => ciphertext khác nhau"""
        plaintext = "Test nonce uniqueness"
        result1 = encrypt_aes(plaintext, self.key)
        result2 = encrypt_aes(plaintext, self.key)
        self.assertNotEqual(result1['nonce'], result2['nonce'])
        self.assertNotEqual(result1['ciphertext'], result2['ciphertext'])
    
    def test_wrong_key_fails(self):
        """Sai khóa phải báo lỗi khi giải mã"""
        plaintext = "Test wrong key"
        result = encrypt_aes(plaintext, self.key)
        wrong_key = generate_aes_key()
        with self.assertRaises(Exception):
            decrypt_aes(result['ciphertext'], result['nonce'], wrong_key)
    
    def test_tampered_ciphertext_fails(self):
        """Ciphertext bị sửa đổi phải báo lỗi"""
        plaintext = "Test tampering"
        result = encrypt_aes(plaintext, self.key)
        # Sửa 1 byte trong ciphertext
        ciphertext_bytes = bytearray(base64.b64decode(result['ciphertext']))
        if len(ciphertext_bytes) > 0:
            ciphertext_bytes[0] ^= 0xFF
        tampered = base64.b64encode(ciphertext_bytes).decode('ascii')
        with self.assertRaises(Exception):
            decrypt_aes(tampered, result['nonce'], self.key)


if __name__ == '__main__':
    import base64
    unittest.main(verbosity=2)
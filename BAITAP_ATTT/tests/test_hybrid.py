"""
Unit Tests for Hybrid Encryption
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.hybrid.hybrid_demo import hybrid_encrypt, hybrid_decrypt, generate_rsa_keypair


class TestHybridEncryption(unittest.TestCase):
    
    def setUp(self):
        self.private_key, self.public_key = generate_rsa_keypair(2048)
    
    def test_hybrid_round_trip(self):
        """Basic encrypt/decrypt round trip"""
        plaintext = "Test hybrid encryption"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        decrypted = hybrid_decrypt(encrypted, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_hybrid_unicode(self):
        """Unicode text should work"""
        plaintext = "Xin chào Việt Nam! 🇻🇳 Tiếng Việt: àáảãạ"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        decrypted = hybrid_decrypt(encrypted, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_hybrid_large_data(self):
        """Large data (10 KB) should work"""
        plaintext = "X" * 10240  # 10 KB
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        decrypted = hybrid_decrypt(encrypted, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_hybrid_empty(self):
        """Empty string should work"""
        plaintext = ""
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        decrypted = hybrid_decrypt(encrypted, self.private_key)
        self.assertEqual(decrypted, plaintext)
    
    def test_hybrid_wrong_key_fails(self):
        """Wrong private key should fail"""
        plaintext = "Test wrong key"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        other_private, _ = generate_rsa_keypair(2048)
        with self.assertRaises(Exception):
            hybrid_decrypt(encrypted, other_private)
    
    def test_hybrid_tampered_ciphertext_fails(self):
        """Tampered ciphertext should fail"""
        import base64
        plaintext = "Test tampering"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        # Tamper ciphertext
        ct_bytes = bytearray(base64.b64decode(encrypted['ciphertext']))
        if len(ct_bytes) > 0:
            ct_bytes[0] ^= 0xFF
        encrypted['ciphertext'] = base64.b64encode(ct_bytes).decode('ascii')
        with self.assertRaises(Exception):
            hybrid_decrypt(encrypted, self.private_key)
    
    def test_hybrid_tampered_encrypted_key_fails(self):
        """Tampered encrypted AES key should fail"""
        import base64
        plaintext = "Test tampering key"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        # Tamper encrypted key
        ek_bytes = bytearray(base64.b64decode(encrypted['encrypted_key']))
        if len(ek_bytes) > 0:
            ek_bytes[0] ^= 0xFF
        encrypted['encrypted_key'] = base64.b64encode(ek_bytes).decode('ascii')
        with self.assertRaises(Exception):
            hybrid_decrypt(encrypted, self.private_key)
    
    def test_hybrid_tampered_nonce_fails(self):
        """Tampered nonce should fail"""
        import base64
        plaintext = "Test tampering nonce"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        # Tamper nonce
        nonce_bytes = bytearray(base64.b64decode(encrypted['nonce']))
        if len(nonce_bytes) > 0:
            nonce_bytes[0] ^= 0xFF
        encrypted['nonce'] = base64.b64encode(nonce_bytes).decode('ascii')
        with self.assertRaises(Exception):
            hybrid_decrypt(encrypted, self.private_key)
    
    def test_hybrid_multiple_encryptions_different(self):
        """Multiple encryptions of same data should produce different ciphertexts"""
        plaintext = "Same plaintext"
        enc1 = hybrid_encrypt(plaintext, self.public_key)
        enc2 = hybrid_encrypt(plaintext, self.public_key)
        # Both encrypted key and ciphertext should differ (due to random AES key + nonce)
        self.assertNotEqual(enc1['encrypted_key'], enc2['encrypted_key'])
        self.assertNotEqual(enc1['ciphertext'], enc2['ciphertext'])
        self.assertNotEqual(enc1['nonce'], enc2['nonce'])
        # But both should decrypt to same plaintext
        self.assertEqual(hybrid_decrypt(enc1, self.private_key), plaintext)
        self.assertEqual(hybrid_decrypt(enc2, self.private_key), plaintext)
    
    def test_hybrid_special_characters(self):
        """Special characters should work"""
        plaintext = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        encrypted = hybrid_encrypt(plaintext, self.public_key)
        decrypted = hybrid_decrypt(encrypted, self.private_key)
        self.assertEqual(decrypted, plaintext)


if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
Unit Tests for Authentication Module
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.auth.auth_demo import (
    sign_message, verify_signature,
    generate_challenge, sign_challenge, verify_challenge_response,
    generate_rsa_keypair
)


class TestSenderAuthentication(unittest.TestCase):
    
    def setUp(self):
        self.private_key, self.public_key = generate_rsa_keypair(2048)
    
    def test_sign_verify_valid(self):
        """Valid message + signature should pass"""
        message = "Test message for signing"
        signature = sign_message(message, self.private_key)
        self.assertTrue(verify_signature(message, signature, self.public_key))
    
    def test_tampered_message_fails(self):
        """Tampered message should fail verification"""
        message = "Original message"
        signature = sign_message(message, self.private_key)
        tampered = message + " (modified)"
        self.assertFalse(verify_signature(tampered, signature, self.public_key))
    
    def test_tampered_signature_fails(self):
        """Tampered signature should fail verification"""
        import base64
        message = "Test message"
        signature = sign_message(message, self.private_key)
        sig_bytes = bytearray(base64.b64decode(signature))
        if len(sig_bytes) > 0:
            sig_bytes[0] ^= 0xFF
        tampered = base64.b64encode(sig_bytes).decode('ascii')
        self.assertFalse(verify_signature(message, tampered, self.public_key))
    
    def test_wrong_public_key_fails(self):
        """Signature with different public key should fail"""
        message = "Test message"
        signature = sign_message(message, self.private_key)
        _, other_public = generate_rsa_keypair(2048)
        self.assertFalse(verify_signature(message, signature, other_public))
    
    def test_empty_message(self):
        """Empty message should work"""
        message = ""
        signature = sign_message(message, self.private_key)
        self.assertTrue(verify_signature(message, signature, self.public_key))
    
    def test_unicode_message(self):
        """Unicode message should work"""
        message = "Xin chào Việt Nam! 🇻🇳"
        signature = sign_message(message, self.private_key)
        self.assertTrue(verify_signature(message, signature, self.public_key))


class TestReceiverAuthentication(unittest.TestCase):
    
    def setUp(self):
        self.private_key, self.public_key = generate_rsa_keypair(2048)
    
    def test_challenge_response_valid(self):
        """Valid challenge-response should pass"""
        challenge = generate_challenge(32)
        response = sign_challenge(challenge, self.private_key)
        self.assertTrue(verify_challenge_response(challenge, response, self.public_key))
    
    def test_wrong_challenge_fails(self):
        """Wrong challenge should fail"""
        challenge = generate_challenge(32)
        response = sign_challenge(challenge, self.private_key)
        wrong_challenge = generate_challenge(32)
        self.assertFalse(verify_challenge_response(wrong_challenge, response, self.public_key))
    
    def test_tampered_response_fails(self):
        """Tampered response should fail"""
        import base64
        challenge = generate_challenge(32)
        response = sign_challenge(challenge, self.private_key)
        resp_bytes = bytearray(base64.b64decode(response))
        if len(resp_bytes) > 0:
            resp_bytes[0] ^= 0xFF
        tampered = base64.b64encode(resp_bytes).decode('ascii')
        self.assertFalse(verify_challenge_response(challenge, tampered, self.public_key))
    
    def test_wrong_public_key_fails(self):
        """Response with different public key should fail"""
        challenge = generate_challenge(32)
        response = sign_challenge(challenge, self.private_key)
        _, other_public = generate_rsa_keypair(2048)
        self.assertFalse(verify_challenge_response(challenge, response, other_public))
    
    def test_challenge_uniqueness(self):
        """Each challenge should be unique"""
        c1 = generate_challenge(32)
        c2 = generate_challenge(32)
        self.assertNotEqual(c1, c2)


class TestMutualAuthentication(unittest.TestCase):
    
    def test_mutual_auth_flow(self):
        """Full mutual authentication should work"""
        # Generate keys for both parties
        sender_priv, sender_pub = generate_rsa_keypair(2048)
        receiver_priv, receiver_pub = generate_rsa_keypair(2048)
        
        # Sender auth
        sender_msg = "Hello from Sender"
        sender_sig = sign_message(sender_msg, sender_priv)
        sender_verified = verify_signature(sender_msg, sender_sig, sender_pub)
        self.assertTrue(sender_verified)
        
        # Receiver auth
        challenge = generate_challenge(32)
        receiver_resp = sign_challenge(challenge, receiver_priv)
        receiver_verified = verify_challenge_response(challenge, receiver_resp, receiver_pub)
        self.assertTrue(receiver_verified)
        
        # Anti-impersonation: Sender's key cannot impersonate Receiver
        fake_resp = sign_challenge(challenge, sender_priv)
        impersonation = verify_challenge_response(challenge, fake_resp, receiver_pub)
        self.assertFalse(impersonation)


if __name__ == '__main__':
    unittest.main(verbosity=2)
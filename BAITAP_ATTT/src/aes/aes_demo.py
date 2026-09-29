"""
AES-128-GCM Encryption/Decryption Demo
Using cryptography library (industry standard)
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_aes_key() -> bytes:
    """Generate secure AES-128 key (16 bytes)"""
    return os.urandom(16)


def encrypt_aes(plaintext: str, key: bytes) -> dict:
    """
    AES-128-GCM Encryption
    Returns: dict with ciphertext, nonce (base64 encoded)
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    return {
        'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii')
    }


def decrypt_aes(ciphertext_b64: str, nonce_b64: str, key: bytes) -> str:
    """
    AES-128-GCM Decryption
    """
    aesgcm = AESGCM(key)
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode('utf-8')


def run_aes_demo(plaintext: str = None):
    """Run complete AES demo"""
    print("\n" + "="*60)
    print("           AES-128-GCM ENCRYPTION DEMO")
    print("="*60)
    
    if plaintext is None:
        plaintext = input("Enter plaintext (Vietnamese supported): ").strip()
        if not plaintext:
            plaintext = "Xin chao! Day la test AES-128-GCM voi tieng Viet"
            print(f"Using default: {plaintext}")
    
    print(f"\n[1] Plaintext: {plaintext}")
    
    # Generate key
    key = generate_aes_key()
    print(f"[2] AES Key (base64): {base64.b64encode(key).decode('ascii')}")
    
    # Encrypt
    result = encrypt_aes(plaintext, key)
    print(f"[3] Ciphertext (base64): {result['ciphertext']}")
    print(f"[4] Nonce (base64):      {result['nonce']}")
    
    # Decrypt
    decrypted = decrypt_aes(result['ciphertext'], result['nonce'], key)
    print(f"[5] Decrypted:           {decrypted}")
    
    # Verify
    success = decrypted == plaintext
    print(f"\n[+] Round-trip check: {'PASS' if success else 'FAIL'}")
    
    return success, {
        'plaintext': plaintext,
        'key': base64.b64encode(key).decode('ascii'),
        'ciphertext': result['ciphertext'],
        'nonce': result['nonce'],
        'decrypted': decrypted
    }


if __name__ == "__main__":
    run_aes_demo()
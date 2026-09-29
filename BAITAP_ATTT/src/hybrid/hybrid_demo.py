"""
Hybrid Encryption: RSA + AES
RSA protects AES session key, AES encrypts data
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ============================================================
# Hybrid Encryption
# ============================================================

def hybrid_encrypt(plaintext: str, recipient_public_key) -> dict:
    """
    Hybrid encryption:
    1. Generate random AES session key
    2. Encrypt data with AES-GCM
    3. Encrypt AES key with RSA-OAEP
    Returns: dict with encrypted_key, ciphertext, nonce
    """
    # Step 1: Generate AES session key
    aes_key = os.urandom(16)  # 128-bit
    
    # Step 2: Encrypt data with AES-GCM
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    
    # Step 3: Encrypt AES key with RSA-OAEP
    encrypted_aes_key = recipient_public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return {
        'encrypted_key': base64.b64encode(encrypted_aes_key).decode('ascii'),
        'ciphertext': base64.b64encode(ciphertext).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii')
    }


def hybrid_decrypt(encrypted_data: dict, recipient_private_key) -> str:
    """
    Hybrid decryption:
    1. Decrypt AES key with RSA private key
    2. Decrypt data with AES-GCM
    """
    # Step 1: Decrypt AES key
    encrypted_aes_key = base64.b64decode(encrypted_data['encrypted_key'])
    aes_key = recipient_private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Step 2: Decrypt data with AES-GCM
    aesgcm = AESGCM(aes_key)
    ciphertext = base64.b64decode(encrypted_data['ciphertext'])
    nonce = base64.b64decode(encrypted_data['nonce'])
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    
    return plaintext_bytes.decode('utf-8')


def generate_rsa_keypair(key_size: int = 2048):
    """Generate RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return private_key, public_key


def run_hybrid_demo(plaintext: str = None):
    """Demo: RSA + AES Hybrid Encryption"""
    print("\n" + "="*60)
    print("         RSA + AES HYBRID ENCRYPTION")
    print("="*60)
    
    # Generate receiver's key pair
    print("\n[1] Generating Receiver's RSA-2048 key pair...")
    receiver_private, receiver_public = generate_rsa_keypair(2048)
    print("    [+] Keys generated")
    
    if plaintext is None:
        plaintext = input("\nEnter plaintext to encrypt: ").strip()
        if not plaintext:
            plaintext = "This is a long message that would be inefficient to encrypt directly with RSA. Hybrid encryption uses AES for the data and RSA only for the session key."
            print(f"Using default: {plaintext}")
    
    print(f"\n[2] Plaintext ({len(plaintext)} chars): {plaintext[:80]}{'...' if len(plaintext) > 80 else ''}")
    
    # Encrypt
    print("\n[3] Encrypting with Hybrid (RSA + AES)...")
    encrypted = hybrid_encrypt(plaintext, receiver_public)
    print(f"    Encrypted AES key (base64): {encrypted['encrypted_key']}")
    print(f"    Ciphertext (base64): {encrypted['ciphertext'][:80]}{'...' if len(encrypted['ciphertext']) > 80 else ''}")
    print(f"    Nonce (base64): {encrypted['nonce']}")
    
    # Decrypt
    print("\n[4] Decrypting with Hybrid...")
    decrypted = hybrid_decrypt(encrypted, receiver_private)
    print(f"    Decrypted: {decrypted[:80]}{'...' if len(decrypted) > 80 else ''}")
    
    # Verify
    success = decrypted == plaintext
    print(f"\n[+] Round-trip check: {'PASS' if success else 'FAIL'}")
    
    # Show why hybrid is needed
    print("\n[5] Why Hybrid?")
    print(f"    Plaintext size: {len(plaintext)} bytes")
    print(f"    RSA-2048 max encrypt: ~190 bytes (with OAEP/SHA-256)")
    print(f"    AES can encrypt: unlimited (streaming)")
    print(f"    RSA used only for: 16-byte AES key")
    
    # Test with large data
    print("\n[6] Testing with large data (10 KB)...")
    large_plaintext = "X" * 10240
    large_encrypted = hybrid_encrypt(large_plaintext, receiver_public)
    large_decrypted = hybrid_decrypt(large_encrypted, receiver_private)
    large_success = large_decrypted == large_plaintext
    print(f"    Large data round-trip: {'PASS' if large_success else 'FAIL'}")
    
    # Test wrong key fails
    print("\n[7] Testing with wrong private key...")
    other_private, _ = generate_rsa_keypair(2048)
    try:
        hybrid_decrypt(encrypted, other_private)
        wrong_key_fail = False
        print("    ERROR: Should have failed!")
    except Exception:
        wrong_key_fail = True
        print("    Correctly failed with wrong key")
    
    overall = success and large_success and wrong_key_fail
    print(f"\n[+] Hybrid Encryption: {'PASS' if overall else 'FAIL'}")
    
    return overall, {
        'plaintext': plaintext,
        'encrypted': encrypted,
        'decrypted': decrypted,
        'large_test': large_success,
        'wrong_key_test': wrong_key_fail
    }


if __name__ == "__main__":
    run_hybrid_demo()
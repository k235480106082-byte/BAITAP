"""
RSA-2048 Encryption/Decryption & Key Generation Demo
Using cryptography library (industry standard)
"""

import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization


def generate_rsa_keypair(key_size: int = 2048):
    """
    Generate RSA key pair
    Returns: (private_key, public_key)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return private_key, public_key


def serialize_private_key(private_key, password: bytes = None) -> str:
    """Export private key as PEM (base64)"""
    encryption = serialization.NoEncryption()
    if password:
        encryption = serialization.BestAvailableEncryption(password)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )
    return pem.decode('ascii')


def serialize_public_key(public_key) -> str:
    """Export public key as PEM (base64)"""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('ascii')


def load_private_key(pem_data: str, password: bytes = None):
    """Load private key from PEM"""
    return serialization.load_pem_private_key(pem_data.encode('ascii'), password=password)


def load_public_key(pem_data: str):
    """Load public key from PEM"""
    return serialization.load_pem_public_key(pem_data.encode('ascii'))


def encrypt_rsa(plaintext: str, public_key) -> str:
    """
    RSA-OAEP Encryption with SHA-256
    Returns: base64 ciphertext
    """
    plaintext_bytes = plaintext.encode('utf-8')
    ciphertext = public_key.encrypt(
        plaintext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode('ascii')


def decrypt_rsa(ciphertext_b64: str, private_key) -> str:
    """
    RSA-OAEP Decryption with SHA-256
    """
    ciphertext = base64.b64decode(ciphertext_b64)
    plaintext_bytes = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext_bytes.decode('utf-8')


def sign_rsa(message: str, private_key) -> str:
    """
    RSA-PSS Digital Signature with SHA-256
    Returns: base64 signature
    """
    message_bytes = message.encode('utf-8')
    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('ascii')


def verify_rsa(message: str, signature_b64: str, public_key) -> bool:
    """
    Verify RSA-PSS Digital Signature
    """
    try:
        message_bytes = message.encode('utf-8')
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def get_key_info(private_key, public_key):
    """Get detailed key info for educational purposes"""
    private_numbers = private_key.private_numbers()
    public_numbers = public_key.public_numbers()
    
    return {
        'n': public_numbers.n,           # modulus = p * q
        'e': public_numbers.e,           # public exponent (usually 65537)
        'd': private_numbers.d,          # private exponent
        'p': private_numbers.p,          # prime p
        'q': private_numbers.q,          # prime q
        'key_size': private_key.key_size
    }


def run_rsa_demo(plaintext: str = None):
    """Run complete RSA demo"""
    print("\n" + "="*60)
    print("           RSA-2048 ENCRYPTION DEMO")
    print("="*60)
    
    # Generate keypair
    print("\n[1] Generating RSA-2048 key pair...")
    private_key, public_key = generate_rsa_keypair(2048)
    print("    [+] Key pair generated")
    
    # Show key info
    info = get_key_info(private_key, public_key)
    print(f"\n[2] Key Information (educational):")
    print(f"    n (modulus) = p × q: {info['n']}")
    print(f"    e (public exp):      {info['e']}")
    print(f"    d (private exp):     {info['d']}")
    print(f"    p:                   {info['p']}")
    print(f"    q:                   {info['q']}")
    print(f"    Key size:            {info['key_size']} bits")
    print(f"\n    Check: e * d = 1 (mod phi(n))")
    print(f"    phi(n) = (p-1)(q-1) = {(info['p']-1)*(info['q']-1)}")
    print(f"    e * d mod phi(n) = {(info['e'] * info['d']) % ((info['p']-1)*(info['q']-1))}")
    
    # Serialize keys
    private_pem = serialize_private_key(private_key)
    public_pem = serialize_public_key(public_key)
    print(f"\n[3] Private Key (PEM):\n{private_pem}")
    print(f"[4] Public Key (PEM):\n{public_pem}")
    
    # Encryption/Decryption
    if plaintext is None:
        plaintext = input("\nEnter plaintext to encrypt (Vietnamese supported): ").strip()
        if not plaintext:
            plaintext = "Test RSA-2048 with Vietnamese text"
            print(f"Using default: {plaintext}")
    
    print(f"\n[5] Plaintext: {plaintext}")
    
    # Encrypt
    ciphertext = encrypt_rsa(plaintext, public_key)
    print(f"[6] Ciphertext (base64): {ciphertext[:80]}..." if len(ciphertext) > 80 else f"[6] Ciphertext: {ciphertext}")
    
    # Decrypt
    decrypted = decrypt_rsa(ciphertext, private_key)
    print(f"[7] Decrypted: {decrypted}")
    
    # Verify round-trip
    success = decrypted == plaintext
    print(f"\n[+] Round-trip check: {'PASS' if success else 'FAIL'}")
    
    # Digital signature demo
    print("\n" + "-"*60)
    print("           DIGITAL SIGNATURE DEMO (RSA-PSS)")
    print("-"*60)
    msg = "Important document to sign"
    sig = sign_rsa(msg, private_key)
    print(f"[8] Message: {msg}")
    print(f"[9] Signature (base64): {sig[:80]}..." if len(sig) > 80 else f"[9] Signature: {sig}")
    verified = verify_rsa(msg, sig, public_key)
    print(f"[+] Verify signature: {'PASS' if verified else 'FAIL'}")
    
    # Test tampering
    tampered = verify_rsa(msg + " (modified)", sig, public_key)
    print(f"[+] Verify tampered message: {'FAIL (expected)' if not tampered else 'PASS (ERROR!)'}")
    
    return success, {
        'plaintext': plaintext,
        'ciphertext': ciphertext,
        'decrypted': decrypted,
        'private_key_pem': private_pem,
        'public_key_pem': public_pem,
        'key_info': info,
        'signature': sig,
        'verify_original': verified,
        'verify_tampered': tampered
    }


if __name__ == "__main__":
    run_rsa_demo()
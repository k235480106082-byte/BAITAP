"""
Authentication Module
Sender Authentication (Digital Signature)
Receiver Authentication (Challenge-Response)
Mutual Authentication
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization


# ============================================================
# Sender Authentication: Digital Signature
# ============================================================

def sign_message(message: str, private_key) -> str:
    """
    Sender signs message with their private key.
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


def verify_signature(message: str, signature_b64: str, public_key) -> bool:
    """
    Receiver verifies signature with sender's public key.
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


def run_sender_auth_demo(message: str = None):
    """Demo: Sender Authentication"""
    print("\n" + "="*60)
    print("         SENDER AUTHENTICATION (Digital Signature)")
    print("="*60)
    
    # Generate sender's key pair
    print("\n[1] Generating Sender's RSA key pair...")
    sender_private, sender_public = generate_rsa_keypair(2048)
    print("    [+] Sender keys generated")
    
    if message is None:
        message = input("\nEnter message to sign: ").strip()
        if not message:
            message = "Important message from Sender"
            print(f"Using default: {message}")
    
    print(f"\n[2] Message: {message}")
    
    # Sender signs
    print("\n[3] Sender signs message with private key...")
    signature = sign_message(message, sender_private)
    print(f"    Signature (base64): {signature[:80]}...")
    
    # Receiver verifies
    print("\n[4] Receiver verifies with Sender's public key...")
    verified = verify_signature(message, signature, sender_public)
    print(f"    Result: {'PASS - Sender authenticated' if verified else 'FAIL'}")
    
    # Test tampered message
    print("\n[5] Testing tampered message...")
    tampered_msg = message + " (modified)"
    tampered_verified = verify_signature(tampered_msg, signature, sender_public)
    print(f"    Tampered message verify: {'FAIL (expected)' if not tampered_verified else 'PASS (ERROR!)'}")
    
    # Test tampered signature
    print("\n[6] Testing tampered signature...")
    import base64
    sig_bytes = bytearray(base64.b64decode(signature))
    if len(sig_bytes) > 0:
        sig_bytes[0] ^= 0xFF
    tampered_sig = base64.b64encode(sig_bytes).decode('ascii')
    tampered_sig_verified = verify_signature(message, tampered_sig, sender_public)
    print(f"    Tampered signature verify: {'FAIL (expected)' if not tampered_sig_verified else 'PASS (ERROR!)'}")
    
    success = verified and not tampered_verified and not tampered_sig_verified
    print(f"\n[+] Sender Authentication: {'PASS' if success else 'FAIL'}")
    
    return success, {
        'message': message,
        'signature': signature,
        'verified': verified,
        'tampered_msg_fail': not tampered_verified,
        'tampered_sig_fail': not tampered_sig_verified
    }


# ============================================================
# Receiver Authentication: Challenge-Response
# ============================================================

def generate_challenge(length: int = 32) -> str:
    """Generate random challenge"""
    return base64.b64encode(os.urandom(length)).decode('ascii')


def sign_challenge(challenge: str, private_key) -> str:
    """Receiver signs challenge with their private key"""
    challenge_bytes = challenge.encode('utf-8')
    signature = private_key.sign(
        challenge_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('ascii')


def verify_challenge_response(challenge: str, signature_b64: str, public_key) -> bool:
    """Sender verifies receiver's response"""
    try:
        challenge_bytes = challenge.encode('utf-8')
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            challenge_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def run_receiver_auth_demo():
    """Demo: Receiver Authentication (Challenge-Response)"""
    print("\n" + "="*60)
    print("       RECEIVER AUTHENTICATION (Challenge-Response)")
    print("="*60)
    
    # Generate receiver's key pair
    print("\n[1] Generating Receiver's RSA key pair...")
    receiver_private, receiver_public = generate_rsa_keypair(2048)
    print("    [+] Receiver keys generated")
    
    # Sender creates challenge
    print("\n[2] Sender generates random challenge...")
    challenge = generate_challenge(32)
    print(f"    Challenge (base64): {challenge}")
    
    # Receiver signs challenge
    print("\n[3] Receiver signs challenge with private key...")
    response = sign_challenge(challenge, receiver_private)
    print(f"    Response/Signature (base64): {response[:80]}...")
    
    # Sender verifies
    print("\n[4] Sender verifies response with Receiver's public key...")
    verified = verify_challenge_response(challenge, response, receiver_public)
    print(f"    Result: {'PASS - Receiver authenticated' if verified else 'FAIL'}")
    
    # Test wrong challenge
    print("\n[5] Testing wrong challenge...")
    wrong_challenge = generate_challenge(32)
    wrong_verified = verify_challenge_response(wrong_challenge, response, receiver_public)
    print(f"    Wrong challenge verify: {'FAIL (expected)' if not wrong_verified else 'PASS (ERROR!)'}")
    
    # Test tampered response
    print("\n[6] Testing tampered response...")
    import base64
    resp_bytes = bytearray(base64.b64decode(response))
    if len(resp_bytes) > 0:
        resp_bytes[0] ^= 0xFF
    tampered_resp = base64.b64encode(resp_bytes).decode('ascii')
    tampered_verified = verify_challenge_response(challenge, tampered_resp, receiver_public)
    print(f"    Tampered response verify: {'FAIL (expected)' if not tampered_verified else 'PASS (ERROR!)'}")
    
    success = verified and not wrong_verified and not tampered_verified
    print(f"\n[+] Receiver Authentication: {'PASS' if success else 'FAIL'}")
    
    return success, {
        'challenge': challenge,
        'response': response,
        'verified': verified,
        'wrong_challenge_fail': not wrong_verified,
        'tampered_response_fail': not tampered_verified
    }


# ============================================================
# Mutual Authentication
# ============================================================

def run_mutual_auth_demo():
    """Demo: Mutual Authentication"""
    print("\n" + "="*60)
    print("           MUTUAL AUTHENTICATION")
    print("="*60)
    
    # Generate both key pairs
    print("\n[1] Generating key pairs for both parties...")
    sender_private, sender_public = generate_rsa_keypair(2048)
    receiver_private, receiver_public = generate_rsa_keypair(2048)
    print("    [+] Both key pairs generated")
    
    # Step 1: Sender authentication (Sender proves identity)
    print("\n[2] Step 1: Sender Authentication")
    sender_msg = "Hello, I am Sender"
    sender_sig = sign_message(sender_msg, sender_private)
    sender_verified = verify_signature(sender_msg, sender_sig, sender_public)
    print(f"    Sender message: {sender_msg}")
    print(f"    Sender verified: {'PASS' if sender_verified else 'FAIL'}")
    
    # Step 2: Receiver authentication (Receiver proves identity)
    print("\n[3] Step 2: Receiver Authentication")
    challenge = generate_challenge(32)
    receiver_resp = sign_challenge(challenge, receiver_private)
    receiver_verified = verify_challenge_response(challenge, receiver_resp, receiver_public)
    print(f"    Challenge: {challenge[:40]}...")
    print(f"    Receiver verified: {'PASS' if receiver_verified else 'FAIL'}")
    
    # Step 3: Optional - Session key establishment
    print("\n[4] Step 3: Session established (both authenticated)")
    session_key = os.urandom(16)
    print(f"    Session key generated (base64): {base64.b64encode(session_key).decode('ascii')}")
    
    # Test impersonation
    print("\n[5] Testing impersonation attack...")
    # Attacker tries to use Sender's key to impersonate Receiver
    fake_receiver_resp = sign_challenge(challenge, sender_private)  # Wrong private key
    impersonation_verified = verify_challenge_response(challenge, fake_receiver_resp, receiver_public)
    print(f"    Impersonation attempt: {'BLOCKED (expected)' if not impersonation_verified else 'SUCCESS (ERROR!)'}")
    
    mutual_success = sender_verified and receiver_verified and not impersonation_verified
    print(f"\n[+] Mutual Authentication: {'PASS' if mutual_success else 'FAIL'}")
    print(f"    Sender auth: {'PASS' if sender_verified else 'FAIL'}")
    print(f"    Receiver auth: {'PASS' if receiver_verified else 'FAIL'}")
    print(f"    Anti-impersonation: {'PASS' if not impersonation_verified else 'FAIL'}")
    
    return mutual_success, {
        'sender_verified': sender_verified,
        'receiver_verified': receiver_verified,
        'anti_impersonation': not impersonation_verified,
        'mutual': mutual_success
    }


# ============================================================
# Helper: Key generation (shared with rsa_demo)
# ============================================================

def generate_rsa_keypair(key_size: int = 2048):
    """Generate RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return private_key, public_key


# ============================================================
# Main demo runner
# ============================================================

def run_all_auth_demos():
    """Run all authentication demos"""
    results = {}
    
    results['sender'] = run_sender_auth_demo()
    input("\nPress Enter for Receiver Authentication...")
    results['receiver'] = run_receiver_auth_demo()
    input("\nPress Enter for Mutual Authentication...")
    results['mutual'] = run_mutual_auth_demo()
    
    return results


if __name__ == "__main__":
    run_all_auth_demos()
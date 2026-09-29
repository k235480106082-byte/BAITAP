"""
ATBM - AES / RSA Security Demo
Main CLI Entry Point
"""

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.aes.aes_demo import run_aes_demo
from src.rsa.rsa_demo import run_rsa_demo
from src.auth.auth_demo import run_sender_auth_demo, run_receiver_auth_demo, run_mutual_auth_demo
from src.hybrid.hybrid_demo import run_hybrid_demo
from src.benchmark.benchmark import run_quick_benchmark


def print_banner():
    print("""
+----------------------------------------------+
|       ATBM - AES / RSA SECURITY DEMO         |
+----------------------------------------------+
| [1] AES Encryption / Decryption              |
| [2] RSA Key Generation & Encryption          |
| [3] Sender Authentication                    |
| [4] Receiver Authentication                  |
| [5] Mutual Authentication                    |
| [6] RSA + AES Hybrid Encryption              |
| [7] Performance Benchmark                    |
| [0] Exit                                     |
+----------------------------------------------+
""")


def main():
    while True:
        print_banner()
        try:
            choice = input("Select option (0-7): ").strip()
            
            if choice == '1':
                run_aes_demo()
            elif choice == '2':
                run_rsa_demo()
            elif choice == '3':
                run_sender_auth_demo()
            elif choice == '4':
                run_receiver_auth_demo()
            elif choice == '5':
                run_mutual_auth_demo()
            elif choice == '6':
                run_hybrid_demo()
            elif choice == '7':
                run_quick_benchmark()
            elif choice == '0':
                print("\nGoodbye!")
                break
            else:
                print("\n[ERROR] Invalid option. Please select 0-7.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
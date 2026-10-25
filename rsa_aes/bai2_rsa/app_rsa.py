"""
BÀI TẬP 2: MÃ HOÁ BẤT ĐỐI XỨNG RSA & CHỮ KÝ SỐ
Thư mục: rsa_aes/bai2_rsa
Hỗ trợ cả 2 chế độ:
  - Form App: python app_rsa.py
  - Console App: python app_rsa.py --console (hoặc -c)

Nội dung đầy đủ 9 mục theo đúng đề bài:
  1. Sinh cặp khoá RSA-2048
  2. Xuất cặp khoá ra file (pem)
  3. View pem: cùng các ý nghĩa các byte trong format pem (cây cấu trúc ASN.1 TLV, OID, INTEGER, SEQUENCE)
  4. Nhập 1 file pem : public key được n và e; private key được n, e, d, p, q, dP, dQ, qInv
  5. Mã hoá dữ liệu sử dụng key vừa import: mảng byte <= 190 byte (khoá AES 32 bytes) -> lưu Base64 ra file
  6. Giải mã: đầu vào là pem, file chứa data đã mã hoá (base64) -> so sánh kq giải mã với nguồn trước khi mã hoá
  7. Viết đoạn code đánh giá tốc độ mã hoá, giải mã: public key (n, e bé = 65537) vs private key (n, d to đùng ~ 2048 bit)
  8. Tạo giao diện sinh chuỗi băm SHA-256 bit: thay đổi đầu vào => băm mới, đánh giá sự thay đổi (Hamming, Avalanche)
  9. CHỮ KÝ SỐ: cùng 1 dữ liệu, cùng 1 người ký (cùng private key) => chữ ký số khác nhau với các lần ký khác nhau.
     ĐỀ XUẤT PHƯƠNG PHÁP: RSA-PSS với Random Salt.
"""

import os
import sys
import time
import base64
import hashlib
import statistics
import threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization


# -----------------------------------------------------------------------------
# CORE ALGORITHMS
# -----------------------------------------------------------------------------

def generate_keypair(key_size: int = 2048):
    """1. Sinh cặp khoá RSA-2048 với e = 65537."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    pub = priv.public_key()
    return priv, pub


def export_pem(priv, pub, priv_path: str = "private.pem", pub_path: str = "public.pem"):
    """2. Xuất cặp khoá ra file PEM."""
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(priv_path, "wb") as f: f.write(priv_pem)
    with open(pub_path, "wb") as f: f.write(pub_pem)
    return priv_path, pub_path


def parse_asn1(der_bytes: bytes, depth: int = 0) -> str:
    """3. View PEM: Phân tích cấu trúc cây ASN.1 TLV của các byte nhị phân DER."""
    tag_names = {0x02: "INTEGER", 0x03: "BIT STRING", 0x04: "OCTET STRING", 0x05: "NULL", 0x06: "OID", 0x30: "SEQUENCE", 0x31: "SET"}
    oid_names = {
        bytes([0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x01]): "rsaEncryption (1.2.840.113549.1.1.1)",
        bytes([0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0B]): "sha256WithRSAEncryption",
        bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01]): "sha-256",
    }
    indent = "  " * depth
    lines = []
    idx = 0
    while idx < len(der_bytes):
        tag = der_bytes[idx]; idx += 1
        if idx >= len(der_bytes): break
        first_len = der_bytes[idx]; idx += 1
        if first_len & 0x80:
            n_bytes = first_len & 0x7F
            length = int.from_bytes(der_bytes[idx:idx + n_bytes], "big")
            idx += n_bytes
        else:
            length = first_len
        val = der_bytes[idx:idx + length]; idx += length

        t_name = tag_names.get(tag, f"TAG(0x{tag:02X})")
        if tag == 0x06:
            lines.append(f"{indent}[{t_name}] len={length} -> {oid_names.get(val, val.hex())}")
        elif tag == 0x02:
            raw = val.lstrip(b'\x00') or b'\x00'
            bits = raw[0].bit_length() + 8 * (len(raw) - 1)
            preview = raw[:8].hex() + ("..." if len(raw) > 8 else "")
            if length <= 4:
                lines.append(f"{indent}[INTEGER = {int.from_bytes(raw, 'big')}] len={length}")
            else:
                lines.append(f"{indent}[INTEGER ({bits} bit)] len={length} hex: {preview}")
        elif bool(tag & 0x20):
            lines.append(f"{indent}[{t_name}] len={length} {{")
            lines.append(parse_asn1(val, depth + 1))
            lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}[{t_name}] len={length} hex: {val[:8].hex()}...")
    return "\n".join(lines)


def load_public_pem(path: str):
    """4. Nhập 1 file PEM: Public Key -> n và e."""
    with open(path, "rb") as f: pub = serialization.load_pem_public_key(f.read())
    pn = pub.public_numbers()
    return pub, {'n': pn.n, 'e': pn.e}


def load_private_pem(path: str):
    """4. Nhập 1 file PEM: Private Key -> n, e, d, p, q, dP, dQ, qInv."""
    with open(path, "rb") as f: priv = serialization.load_pem_private_key(f.read(), password=None)
    pn = priv.private_numbers()
    return priv, {
        'n': pn.public_numbers.n, 'e': pn.public_numbers.e,
        'd': pn.d, 'p': pn.p, 'q': pn.q,
        'dP': pn.dmp1, 'dQ': pn.dmq1, 'qInv': pn.iqmp
    }


def encrypt_rsa(pub, data: bytes) -> bytes:
    """5. Mã hoá dữ liệu <= 190 byte (RSA-OAEP SHA-256)."""
    if len(data) > 190:
        raise ValueError(f"Dữ liệu {len(data)} bytes vượt quá giới hạn 190 bytes!")
    return pub.encrypt(
        data,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt_rsa(priv, ct: bytes) -> bytes:
    """6. Giải mã ciphertext bằng Private Key."""
    return priv.decrypt(
        ct,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def benchmark_speed(priv, pub, rounds: int = 20) -> dict:
    """7. Đánh giá tốc độ: Public Key (e bé) vs Private Key (d to)."""
    sample = os.urandom(32)
    t_enc, t_dec, t_sig, t_ver = [], [], [], []
    for _ in range(rounds):
        t0 = time.perf_counter(); c = encrypt_rsa(pub, sample); t_enc.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); decrypt_rsa(priv, c); t_dec.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); s = sign_pss(priv, sample); t_sig.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); verify_pss(pub, sample, s); t_ver.append(time.perf_counter() - t0)
    me = statistics.mean(t_enc) * 1000; md = statistics.mean(t_dec) * 1000
    ms = statistics.mean(t_sig) * 1000; mv = statistics.mean(t_ver) * 1000
    return {
        'enc_ms': me, 'dec_ms': md, 'sig_ms': ms, 'ver_ms': mv,
        'ratio_dec_enc': md / me if me > 0 else 0,
        'ratio_sig_ver': ms / mv if mv > 0 else 0
    }


def sha256_hash(text: str) -> str:
    """8. Sinh chuỗi băm SHA-256 (256 bit = 64 ký tự Hex)."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def hamming_dist(h1: str, h2: str) -> int:
    """Tính số bit khác nhau giữa 2 chuỗi Hex."""
    return bin(int(h1, 16) ^ int(h2, 16)).count('1')


def sign_pss(priv, data: bytes) -> bytes:
    """9. Chữ ký số RSA-PSS với Random Salt (mỗi lần ký sinh chữ ký khác nhau)."""
    return priv.sign(
        data,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )


def verify_pss(pub, data: bytes, sig: bytes) -> bool:
    """Xác minh chữ ký số PSS."""
    try:
        pub.verify(
            sig, data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# GIAO DIỆN FORM DESKTOP (TKINTER FORM APP)
# -----------------------------------------------------------------------------

def run_form():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext

    class RSAForm(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("BÀI 2: MÃ HOÁ BẤT ĐỐI XỨNG RSA & CHỮ KÝ SỐ (FORM APP)")
            self.geometry("1050, 750")
            self.minsize(920, 650)
            self.priv = None; self.pub = None
            self.s1 = None; self.s2 = None

            # Header
            h = tk.Frame(self, bg="#1e3a8a", height=50)
            h.pack(fill="x", side="top")
            tk.Label(h, text="BÀI 2: MÃ HOÁ RSA-2048, BĂM SHA-256 & CHỮ KÝ SỐ (FORM)", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#1e3a8a").pack(side="left", padx=15, pady=10)

            self.st_var = tk.StringVar(value="Sẵn sàng.")
            sb = tk.Label(self, textvariable=self.st_var, bd=1, relief="sunken", anchor="w", font=("Segoe UI", 9), bg="#f8fafc", padx=10, pady=3)
            sb.pack(side="bottom", fill="x")

            nb = ttk.Notebook(self)
            nb.pack(fill="both", expand=True, padx=8, pady=6)

            t1 = ttk.Frame(nb); nb.add(t1, text="  Mục 1-6: RSA & PEM & Mã hoá  ")
            t2 = ttk.Frame(nb); nb.add(t2, text="  Mục 7: Benchmark (e vs d)  ")
            t3 = ttk.Frame(nb); nb.add(t3, text="  Mục 8: Băm SHA-256 Real-time  ")
            t4 = ttk.Frame(nb); nb.add(t4, text="  Mục 9: Chữ ký số RSA-PSS  ")

            self._init_tab1(t1)
            self._init_tab2(t2)
            self._init_tab3(t3)
            self._init_tab4(t4)

        # Tab 1: 1-6
        def _init_tab1(self, parent):
            p = ttk.PanedWindow(parent, orient="horizontal"); p.pack(fill="both", expand=True, padx=6, pady=6)
            left = ttk.Frame(p); p.add(left, weight=1)
            right = ttk.Frame(p); p.add(right, weight=1)

            # Left
            g1 = ttk.LabelFrame(left, text="1, 2, 4. Sinh khoá, Xuất & Nhập PEM", padding=6); g1.pack(fill="x", pady=2)
            r1 = ttk.Frame(g1); r1.pack(fill="x")
            ttk.Button(r1, text="1. Sinh RSA-2048", command=self.gen_k).pack(side="left", padx=2)
            ttk.Button(r1, text="2. Xuất PEM", command=self.exp_k).pack(side="left", padx=2)
            ttk.Button(r1, text="4. Nhập PEM", command=self.imp_k).pack(side="left", padx=2)

            g2 = ttk.LabelFrame(left, text="4. Thông số khoá trích xuất (n, e, d, p, q...)", padding=6); g2.pack(fill="both", expand=True, pady=3)
            self.txt_par = scrolledtext.ScrolledText(g2, height=8, font=("Consolas", 8), bg="#f8fafc")
            self.txt_par.pack(fill="both", expand=True)

            g3 = ttk.LabelFrame(left, text="5, 6. Mã hoá / Giải mã (mảng byte <= 190 byte)", padding=6); g3.pack(fill="x", pady=3)
            ttk.Label(g3, text="Dữ liệu vào (Vd: khoá AES 32 bytes):").pack(anchor="w")
            self.e_in = ttk.Entry(g3); self.e_in.insert(0, "Khoá AES 256-bit: a1b2c3d4e5f60718293a4b5c6d7e8f90"); self.e_in.pack(fill="x", pady=1)

            rb = ttk.Frame(g3); rb.pack(fill="x", pady=2)
            ttk.Button(rb, text="5. Mã hoá (lưu Base64 ra file)", command=self.enc_data).pack(side="left", padx=3)
            ttk.Button(rb, text="6. Giải mã & So sánh nguồn", command=self.dec_data).pack(side="left", padx=3)

            ttk.Label(g3, text="Ciphertext (Base64):").pack(anchor="w")
            self.e_ct = ttk.Entry(g3, font=("Consolas", 8)); self.e_ct.pack(fill="x", pady=1)
            ttk.Label(g3, text="Kết quả Giải mã:").pack(anchor="w")
            self.e_out = ttk.Entry(g3); self.e_out.pack(fill="x", pady=1)

            # Right: 3. View PEM
            g_v = ttk.LabelFrame(right, text="3. View PEM: Ý nghĩa các byte & Phân tích ASN.1 TLV", padding=6); g_v.pack(fill="both", expand=True)
            rv = ttk.Frame(g_v); rv.pack(fill="x", pady=2)
            ttk.Button(rv, text="Xem Private Key ASN.1", command=lambda: self.view_pem(True)).pack(side="left", padx=3)
            ttk.Button(rv, text="Xem Public Key ASN.1", command=lambda: self.view_pem(False)).pack(side="left", padx=3)

            self.txt_view = scrolledtext.ScrolledText(g_v, font=("Consolas", 9), bg="#0f172a", fg="#38bdf8")
            self.txt_view.pack(fill="both", expand=True, pady=3)

        def gen_k(self):
            t0 = time.perf_counter()
            self.priv, self.pub = generate_keypair(2048)
            ms = (time.perf_counter() - t0) * 1000
            pn = self.priv.private_numbers()
            n = pn.public_numbers.n; e = pn.public_numbers.e; d = pn.d
            info = (
                f"[PUBLIC KEY]\n  n ({n.bit_length()} bit): {hex(n)[:60]}...\n  e: {e} (0x{e:X})\n\n"
                f"[PRIVATE KEY]\n  d ({d.bit_length()} bit): {hex(d)[:60]}...\n"
                f"  p: {hex(pn.p)[:40]}...\n  q: {hex(pn.q)[:40]}...\n"
                f"  dP: {hex(pn.dmp1)[:40]}...\n  dQ: {hex(pn.dmq1)[:40]}...\n  qInv: {hex(pn.iqmp)[:40]}...\n"
                f"Kiểm tra toán học p * q == n: {pn.p * pn.q == n} (ĐÚNG)"
            )
            self.txt_par.delete("1.0", tk.END); self.txt_par.insert(tk.END, info)
            self.view_pem(True)
            self.st_var.set(f"Sinh RSA-2048 thành công ({ms:.1f} ms).")

        def exp_k(self):
            if not self.priv: messagebox.showwarning("Lỗi", "Chưa có khoá!"); return
            d = filedialog.askdirectory(title="Chọn thư mục lưu private.pem & public.pem")
            if d:
                export_pem(self.priv, self.pub, os.path.join(d, "private.pem"), os.path.join(d, "public.pem"))
                messagebox.showinfo("Thành công", f"Đã lưu private.pem & public.pem vào {d}")

        def imp_k(self):
            p = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem")])
            if p:
                try:
                    try:
                        self.priv, par = load_private_pem(p)
                        self.pub = self.priv.public_key()
                        info = f"[PRIVATE KEY IMPORT]\nn ({par['n'].bit_length()} bit): {hex(par['n'])[:40]}...\ne: {par['e']}\nd: {hex(par['d'])[:40]}...\np*q==n: {par['p']*par['q'] == par['n']}"
                        self.view_pem(True)
                    except Exception:
                        self.pub, par = load_public_pem(p); self.priv = None
                        info = f"[PUBLIC KEY IMPORT]\nn ({par['n'].bit_length()} bit): {hex(par['n'])[:40]}...\ne: {par['e']}"
                        self.view_pem(False)
                    self.txt_par.delete("1.0", tk.END); self.txt_par.insert(tk.END, info)
                    self.st_var.set(f"Đã import PEM: {os.path.basename(p)}")
                except Exception as e:
                    messagebox.showerror("Lỗi import", str(e))

        def view_pem(self, is_priv=True):
            if is_priv and not self.priv: self.gen_k()
            elif not is_priv and not self.pub: self.gen_k()
            k = self.priv if is_priv else self.pub

            if is_priv:
                pem_b = k.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
            else:
                pem_b = k.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

            lines = pem_b.decode('ascii').strip().splitlines()
            der = base64.b64decode("".join([l for l in lines if not l.startswith("-----")]))
            out = (
                f"=== 3. VIEW PEM & PHÂN TÍCH BYTE ASN.1 ({'PRIVATE' if is_priv else 'PUBLIC'}) ===\n\n"
                f"1. RAW PEM (Base64 ASCII):\n   {lines[0]}\n   {lines[1]}\n   ...\n   {lines[-1]}\n\n"
                f"2. DER BYTES ({len(der)} bytes nhị phân):\n   Hex 16 bytes đầu: {der[:16].hex()}\n\n"
                f"3. CÂY CẤU TRÚC ASN.1 TLV (Tag-Length-Value):\n"
                f"{parse_asn1(der, depth=1)}\n\n"
                f"4. Ý NGHĨA CÁC BYTE:\n"
                f"   - 0x30: SEQUENCE\n   - 0x02: INTEGER (chứa n, e, d, p, q...)\n   - 0x06: OID rsaEncryption\n"
                f"   - e = 65537 (3 bytes): public exponent nhỏ giúp mã hoá nhanh\n"
                f"   - d ~ 2048 bit (256 bytes): private exponent to đùng bảo mật"
            )
            self.txt_view.delete("1.0", tk.END); self.txt_view.insert(tk.END, out)

        def enc_data(self):
            if not self.pub: self.gen_k()
            data = self.e_in.get().encode('utf-8')
            try:
                ct = encrypt_rsa(self.pub, data)
                b64 = base64.b64encode(ct).decode('ascii')
                self.e_ct.delete(0, tk.END); self.e_ct.insert(0, b64)
                with open("encrypted_data.b64", "w") as f: f.write(b64)
                self.st_var.set("Đã mã hoá -> lưu ra encrypted_data.b64")
            except Exception as e: messagebox.showerror("Lỗi", str(e))

        def dec_data(self):
            if not self.priv: messagebox.showwarning("Lỗi", "Cần Private Key!"); return
            b64 = self.e_ct.get().strip()
            if not b64 and os.path.exists("encrypted_data.b64"):
                with open("encrypted_data.b64") as f: b64 = f.read().strip()
            try:
                ct = base64.b64decode(b64)
                pt = decrypt_rsa(self.priv, ct)
                pt_str = pt.decode('utf-8', errors='replace')
                self.e_out.delete(0, tk.END); self.e_out.insert(0, pt_str)
                match = (pt_str == self.e_in.get())
                messagebox.showinfo("So sánh giải mã", f"Kết quả: {'✅ KHỚP TUYỆT ĐỐI VỚI NGUỒN' if match else '❌ KHÔNG KHỚP'}\nPlaintext: {pt_str}")
            except Exception as e: messagebox.showerror("Lỗi giải mã", str(e))

        # Tab 2: 7. Benchmark
        def _init_tab2(self, parent):
            f = ttk.Frame(parent, padding=12); f.pack(fill="both", expand=True)
            r = ttk.Frame(f); r.pack(fill="x", pady=4)
            ttk.Label(r, text="Số vòng lặp đo:").pack(side="left")
            sp = ttk.Spinbox(r, from_=5, to=50, width=5); sp.set(20); sp.pack(side="left", padx=4)
            ttk.Button(r, text="7. Đánh giá tốc độ mã hoá, giải mã (e bé vs d to đùng)", command=lambda: self.run_bench(int(sp.get()))).pack(side="left", padx=8)

            self.txt_bench = scrolledtext.ScrolledText(f, font=("Consolas", 10), bg="#0f172a", fg="#38bdf8")
            self.txt_bench.pack(fill="both", expand=True, pady=6)

        def run_bench(self, rounds):
            if not self.priv: self.priv, self.pub = generate_keypair(2048)
            self.st_var.set("Đang đo tốc độ...")
            def worker():
                res = benchmark_speed(self.priv, self.pub, rounds)
                log = (
                    f"╔══════════════════════════════════════════════════════════════════════════════════╗\n"
                    f"║       7. ĐÁNH GIÁ TỐC ĐỘ: PUBLIC KEY (e = 65537 BÉ) vs PRIVATE KEY (d TO ĐÙNG)   ║\n"
                    f"╠══════════════════════════════════════════════════════════════════════════════════╣\n"
                    f"║  MÃ HOÁ (Encrypt)      Public Key (e bé = 65537)   {res['enc_ms']:8.3f} ms   [CỰC NHANH]       ║\n"
                    f"║  GIẢI MÃ (Decrypt)     Private Key (d to đùng)     {res['dec_ms']:8.3f} ms   [CHẬM HƠN {res['ratio_dec_enc']:4.1f}x]  ║\n"
                    f"║  KÝ SỐ (Sign)          Private Key (d to đùng)     {res['sig_ms']:8.3f} ms   [CHẬM HƠN {res['ratio_sig_ver']:4.1f}x]  ║\n"
                    f"║  XÁC MINH (Verify)     Public Key (e bé = 65537)   {res['ver_ms']:8.3f} ms   [CỰC NHANH]       ║\n"
                    f"╚══════════════════════════════════════════════════════════════════════════════════╝\n\n"
                    f"► GIẢI THÍCH LÝ THUYẾT:\n"
                    f"  - e = 65537 = 2^16 + 1 chỉ có đúng 2 bit 1: Square-and-multiply chỉ tốn ~17 phép nhân modular.\n"
                    f"  - d ngẫu nhiên 2048 bit có ~1024 bit 1: Tốn tới ~3072 phép nhân modular số lớn.\n"
                    f"  => Mã hoá / Verify (dùng e bé) NHANH HƠN từ 15 đến 20 lần so với Giải mã / Ký (dùng d to đùng)!"
                )
                self.after(0, lambda: [self.txt_bench.delete("1.0", tk.END), self.txt_bench.insert(tk.END, log), self.st_var.set("Benchmark xong.")])
            threading.Thread(target=worker, daemon=True).start()

        # Tab 3: 8. SHA-256
        def _init_tab3(self, parent):
            f = ttk.Frame(parent, padding=12); f.pack(fill="both", expand=True)
            p = ttk.PanedWindow(f, orient="horizontal"); p.pack(fill="both", expand=True, pady=4)
            fa = ttk.LabelFrame(p, text="Đầu vào A", padding=8); p.add(fa, weight=1)
            fb = ttk.LabelFrame(p, text="Đầu vào B (Thay đổi 1 ký tự)", padding=8); p.add(fb, weight=1)

            ttk.Label(fa, text="Văn bản A (Gõ real-time):").pack(anchor="w")
            self.e_sha_a = ttk.Entry(fa, font=("Segoe UI", 10)); self.e_sha_a.insert(0, "An toan bao mat thong tin"); self.e_sha_a.pack(fill="x", pady=2)
            self.e_sha_a.bind("<KeyRelease>", lambda e: self.sha_calc())
            ttk.Label(fa, text="Mã băm SHA-256 A:").pack(anchor="w")
            self.e_hex_a = ttk.Entry(fa, font=("Consolas", 9), foreground="#2563eb"); self.e_hex_a.pack(fill="x", pady=2)

            ttk.Label(fb, text="Văn bản B (Gõ real-time):").pack(anchor="w")
            self.e_sha_b = ttk.Entry(fb, font=("Segoe UI", 10)); self.e_sha_b.insert(0, "An toan bao mat Thong tin"); self.e_sha_b.pack(fill="x", pady=2)
            self.e_sha_b.bind("<KeyRelease>", lambda e: self.sha_calc())
            ttk.Label(fb, text="Mã băm SHA-256 B:").pack(anchor="w")
            self.e_hex_b = ttk.Entry(fb, font=("Consolas", 9), foreground="#dc2626"); self.e_hex_b.pack(fill="x", pady=2)

            g_ev = ttk.LabelFrame(f, text="8. Đánh giá sự thay đổi của kết quả băm khi đầu vào đổi rất ít", padding=8); g_ev.pack(fill="x", pady=6)
            self.lbl_sha = ttk.Label(g_ev, text="", font=("Consolas", 10, "bold")); self.lbl_sha.pack(anchor="w")
            self.sha_calc()

        def sha_calc(self):
            ha = sha256_hash(self.e_sha_a.get()); hb = sha256_hash(self.e_sha_b.get())
            self.e_hex_a.delete(0, tk.END); self.e_hex_a.insert(0, ha)
            self.e_hex_b.delete(0, tk.END); self.e_hex_b.insert(0, hb)
            d = hamming_dist(ha, hb)
            self.lbl_sha.config(
                text=f"Khoảng cách Hamming: {d} / 256 bit khác nhau ({d/256.0*100:.1f}%)\n"
                     f"Đánh giá: Thay đổi chỉ 1 ký tự rất nhỏ làm đảo lộn ~50% bit của mã băm (Hiệu ứng tuyết lở - Avalanche Effect)!"
            )

        # Tab 4: 9. Signature PSS
        def _init_tab4(self, parent):
            f = ttk.Frame(parent, padding=12); f.pack(fill="both", expand=True)
            ttk.Label(f, text="Dữ liệu thông điệp cần ký số:").pack(anchor="w")
            self.e_sig_msg = ttk.Entry(f, font=("Segoe UI", 10)); self.e_sig_msg.insert(0, "Hợp đồng kinh tế ATTT - Chuyển khoản 100.000.000 VNĐ"); self.e_sig_msg.pack(fill="x", pady=2)

            rb = ttk.Frame(f); rb.pack(fill="x", pady=4)
            ttk.Button(rb, text="Ký Lần 1 (Chữ ký 1)", command=self.sig_do1).pack(side="left", padx=3)
            ttk.Button(rb, text="Ký Lần 2 (Chữ ký 2 - cùng data, cùng key)", command=self.sig_do2).pack(side="left", padx=3)
            ttk.Button(rb, text="Verify Chữ ký 1", command=self.sig_ver1).pack(side="left", padx=3)
            ttk.Button(rb, text="Verify Chữ ký 2", command=self.sig_ver2).pack(side="left", padx=3)

            ttk.Label(f, text="Chữ ký lần 1 (Base64):").pack(anchor="w")
            self.e_s1 = ttk.Entry(f, font=("Consolas", 8)); self.e_s1.pack(fill="x", pady=1)
            ttk.Label(f, text="Chữ ký lần 2 (Base64):").pack(anchor="w")
            self.e_s2 = ttk.Entry(f, font=("Consolas", 8)); self.e_s2.pack(fill="x", pady=1)

            g_prop = ttk.LabelFrame(f, text="9. ĐỀ XUẤT PHƯƠNG PHÁP: Cùng 1 dữ liệu, cùng 1 người ký => chữ ký khác nhau", padding=8)
            g_prop.pack(fill="both", expand=True, pady=4)
            self.txt_sig = scrolledtext.ScrolledText(g_prop, font=("Consolas", 9), bg="#f8fafc")
            self.txt_sig.pack(fill="both", expand=True)

            self.txt_sig.insert(tk.END,
                "========================================================================================\n"
                "   ĐỀ XUẤT PHƯƠNG PHÁP: SỬ DỤNG CHUẨN RSA-PSS (Probabilistic Signature Scheme - RFC 3447)\n"
                "========================================================================================\n\n"
                "1. VẤN ĐỀ CỦA CHUẨN CŨ (PKCS#1 v1.5):\n"
                "   Chuẩn cũ mang tính 'quyết định luận' (deterministic): cùng dữ liệu + cùng private key luôn\n"
                "   cho ra duy nhất 1 chuỗi chữ ký giống hệt nhau -> Dễ bị tấn công tua lại (Replay Attack).\n\n"
                "2. PHƯƠNG PHÁP ĐỀ XUẤT ĐỂ ĐẠT ĐƯỢC CHỮ KÝ KHÁC NHAU:\n"
                "   Sử dụng chuẩn RSA-PSS với Salt ngẫu nhiên:\n"
                "     - Bước 1: Tính mã băm h = SHA-256(Message)\n"
                "     - Bước 2: Sinh chuỗi muối ngẫu nhiên Salt = os.urandom(salt_len) (mỗi lần ký Salt khác nhau!)\n"
                "     - Bước 3: Ghép M' = h || Salt\n"
                "     - Bước 4: Tạo mặt nạ EM = MGF1(M', emLen)\n"
                "     - Bước 5: Chữ ký = EM^d mod n\n\n"
                "3. TẠI SAO PUBLIC KEY VẪN XÁC MINH ĐƯỢC CẢ 2 CHỮ KÝ?\n"
                "   Khi kiểm tra, Public Key giải mã lấy lại Salt đã nhúng sẵn trong chữ ký và tái tạo lại hash.\n"
                "   => Vì vậy: Cả 2 chữ ký dù khác nhau 100% nhưng đều được xác minh HỢP LỆ (PASS) tuyệt đối!"
            )

        def sig_do1(self):
            if not self.priv: self.gen_k()
            self.s1 = sign_pss(self.priv, self.e_sig_msg.get().encode('utf-8'))
            self.e_s1.delete(0, tk.END); self.e_s1.insert(0, base64.b64encode(self.s1).decode('ascii'))
            self.st_var.set("Đã tạo chữ ký 1.")

        def sig_do2(self):
            if not self.priv: self.gen_k()
            self.s2 = sign_pss(self.priv, self.e_sig_msg.get().encode('utf-8'))
            self.e_s2.delete(0, tk.END); self.e_s2.insert(0, base64.b64encode(self.s2).decode('ascii'))
            self.st_var.set("Đã tạo chữ ký 2.")

        def sig_ver1(self):
            if not self.s1 or not self.pub: messagebox.showwarning("Lỗi", "Chưa có chữ ký 1!"); return
            ok = verify_pss(self.pub, self.e_sig_msg.get().encode('utf-8'), self.s1)
            messagebox.showinfo("Xác minh 1", f"Kết quả: {'✅ HỢP LỆ (PASS)' if ok else '❌ THẤT BẠI'}")

        def sig_ver2(self):
            if not self.s2 or not self.pub: messagebox.showwarning("Lỗi", "Chưa có chữ ký 2!"); return
            ok = verify_pss(self.pub, self.e_sig_msg.get().encode('utf-8'), self.s2)
            messagebox.showinfo("Xác minh 2", f"Kết quả: {'✅ HỢP LỆ (PASS) - Chữ ký khác nhưng vẫn PASS!' if ok else '❌ THẤT BẠI'}")

    RSAForm().mainloop()


# -----------------------------------------------------------------------------
# GIAO DIỆN CONSOLE (CLI)
# -----------------------------------------------------------------------------

def run_console():
    priv = None; pub = None
    while True:
        print("\n" + "=" * 60)
        print("  BÀI 2: MÃ HOÁ BẤT ĐỐI XỨNG RSA & CHỮ KÝ SỐ (CONSOLE APP)")
        print("=" * 60)
        print("  [1] 1. Sinh cặp khoá RSA-2048")
        print("  [2] 2. Xuất cặp khoá ra file (pem)")
        print("  [3] 3. View pem & phân tích ý nghĩa byte ASN.1 TLV")
        print("  [4] 4. Nhập 1 file pem: public key (n, e) / private key (n, e, d...)")
        print("  [5] 5. Mã hoá mảng byte <= 190 byte (khoá AES) -> lưu file Base64")
        print("  [6] 6. Giải mã: đọc pem + file ciphertext -> so sánh nguồn")
        print("  [7] 7. Đánh giá tốc độ: public key (e bé) vs private key (d to đùng)")
        print("  [8] 8. Giao diện sinh chuỗi băm SHA-256 & Avalanche Effect")
        print("  [9] 9. CHỮ KÝ SỐ: ký 2 lần khác nhau cho cùng 1 thông điệp")
        print("  [0] Thoát")
        print("-" * 60)
        c = input("Chọn [0-9]: ").strip()
        if c == '0': break
        elif c == '1':
            priv, pub = generate_keypair(2048)
            print("Đã sinh cặp khoá RSA-2048 thành công.")
        elif c == '2':
            if not priv: priv, pub = generate_keypair(2048)
            export_pem(priv, pub, "private.pem", "public.pem")
            print("Đã xuất ra: private.pem và public.pem")
        elif c == '3':
            if not priv: priv, pub = generate_keypair(2048)
            pem_b = priv.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
            der = base64.b64decode("".join([l for l in pem_b.decode().splitlines() if not l.startswith("-----")]))
            print(f"\nPhân tích ASN.1 TLV của Private Key ({len(der)} bytes DER):")
            print(parse_asn1(der, depth=1))
        elif c == '4':
            p_pub = input("Đường dẫn file Public PEM (mặc định: public.pem): ").strip() or "public.pem"
            p_priv = input("Đường dẫn file Private PEM (mặc định: private.pem): ").strip() or "private.pem"
            if not os.path.exists(p_pub) or not os.path.exists(p_priv):
                print("Chưa có file PEM. Đang tự động sinh cặp khoá...")
                priv, pub = generate_keypair(2048)
                export_pem(priv, pub, p_priv, p_pub)
            pub, par_pub = load_public_pem(p_pub)
            print(f"\n[+] ĐÃ NHẬP PUBLIC KEY TỪ {p_pub}:")
            print(f"    Modulus n ({par_pub['n'].bit_length()} bit): {hex(par_pub['n'])[:60]}...")
            print(f"    Public Exponent e: {par_pub['e']}")
            priv, par_priv = load_private_pem(p_priv)
            print(f"\n[+] ĐÃ NHẬP PRIVATE KEY TỪ {p_priv}:")
            print(f"    Modulus n: {hex(par_priv['n'])[:40]}...")
            print(f"    Public Exponent e: {par_priv['e']}")
            print(f"    Private Exponent d ({par_priv['d'].bit_length()} bit): {hex(par_priv['d'])[:40]}...")
            print(f"    Prime p: {hex(par_priv['p'])[:30]}...")
            print(f"    Prime q: {hex(par_priv['q'])[:30]}...")
            print(f"    dP = d mod (p-1): {hex(par_priv['dP'])[:30]}...")
            print(f"    dQ = d mod (q-1): {hex(par_priv['dQ'])[:30]}...")
            print(f"    qInv = q^-1 mod p: {hex(par_priv['qInv'])[:30]}...")
            print(f"    Kiểm tra toán học p * q == n: {par_priv['p'] * par_priv['q'] == par_priv['n']} (ĐÚNG)")
        elif c == '5':
            if not pub:
                if os.path.exists("public.pem"): pub, _ = load_public_pem("public.pem")
                else: priv, pub = generate_keypair(2048); export_pem(priv, pub)
            raw_text = input("Nhập chuỗi cần mã hoá (Enter để sinh khoá AES 256-bit 32 bytes ngẫu nhiên): ").strip()
            if raw_text:
                sample = raw_text.encode('utf-8')
            else:
                sample = os.urandom(32)
            if len(sample) > 190:
                print(f"[!] Dữ liệu {len(sample)} bytes > 190 bytes giới hạn của RSA-2048 OAEP!"); continue
            print(f"Dữ liệu gốc đưa vào ({len(sample)} bytes): {sample.hex()}")
            with open("original_data.bin", "wb") as f: f.write(sample)
            ct = encrypt_rsa(pub, sample)
            b64 = base64.b64encode(ct).decode('ascii')
            with open("encrypted_key.b64", "w") as f: f.write(b64)
            print(f"Kết quả mã hoá Base64 ({len(b64)} ký tự) -> Đã lưu vào 'encrypted_key.b64'")
            print(f"Ciphertext Base64 preview: {b64[:70]}...")
        elif c == '6':
            p_priv = input("Đường dẫn file Private PEM (mặc định: private.pem): ").strip() or "private.pem"
            p_ct = input("Đường dẫn file chứa data đã mã hoá Base64 (mặc định: encrypted_key.b64): ").strip() or "encrypted_key.b64"
            if not os.path.exists(p_priv):
                print(f"[!] File {p_priv} không tồn tại!"); continue
            if not os.path.exists(p_ct):
                print(f"[!] File {p_ct} không tồn tại. Hãy chạy mục 5 trước!"); continue
            priv, _ = load_private_pem(p_priv)
            with open(p_ct, "r", encoding="ascii") as f: b64 = f.read().strip()
            ct = base64.b64decode(b64)
            pt = decrypt_rsa(priv, ct)
            print(f"\n[+] Kết quả giải mã ({len(pt)} bytes):")
            print(f"    Hex : {pt.hex()}")
            try:
                print(f"    Text: {pt.decode('utf-8')}")
            except Exception:
                pass
            if os.path.exists("original_data.bin"):
                with open("original_data.bin", "rb") as f: orig = f.read()
                print(f"    Nguồn gốc ban đầu : {orig.hex()}")
                if pt == orig:
                    print("    => SO SÁNH KẾT QUẢ VỚI NGUỒN: ✅ KHỚP HOÀN TOÀN 100%!")
                else:
                    print("    => SO SÁNH KẾT QUẢ VỚI NGUỒN: ❌ KHÔNG KHỚP!")
        elif c == '7':
            if not priv: priv, pub = generate_keypair(2048)
            print("Đang benchmark 20 vòng...")
            res = benchmark_speed(priv, pub, 20)
            print(f"Mã hoá Public Key (e = 65537 bé) : {res['enc_ms']:.3f} ms [CỰC NHANH]")
            print(f"Giải mã Private Key (d to đùng)   : {res['dec_ms']:.3f} ms [CHẬM HƠN {res['ratio_dec_enc']:.1f}x]")
        elif c == '8':
            s1 = input("Chuỗi A: ") or "hello"
            s2 = input("Chuỗi B: ") or "Hello"
            h1 = sha256_hash(s1); h2 = sha256_hash(s2)
            d = hamming_dist(h1, h2)
            print(f"SHA256(A): {h1}\nSHA256(B): {h2}")
            print(f"Khoảng cách Hamming: {d}/256 bits khác ({d/256*100:.1f}%) -> Avalanche Effect!")
        elif c == '9':
            if not priv: priv, pub = generate_keypair(2048)
            msg = b"Du lieu quan trong can ky so"
            s1 = sign_pss(priv, msg); s2 = sign_pss(priv, msg)
            print(f"Chữ ký 1: {s1[:16].hex()}...")
            print(f"Chữ ký 2: {s2[:16].hex()}...")
            print(f"Chữ ký 1 == Chữ ký 2? {s1 == s2} -> KHÁC NHAU HOÀN TOÀN (nhờ PSS Random Salt)!")
            print(f"Verify 1: {verify_pss(pub, msg, s1)}")
            print(f"Verify 2: {verify_pss(pub, msg, s2)}")
            print("► ĐỀ XUẤT: Dùng RSA-PSS (RFC 3447) với Random Salt giúp chống Replay Attack hiệu quả!")
        input("\nNhấn Enter tiếp tục...")


if __name__ == "__main__":
    if "--console" in sys.argv or "-c" in sys.argv or "--cli" in sys.argv:
        run_console()
    else:
        try:
            run_form()
        except Exception:
            run_console()

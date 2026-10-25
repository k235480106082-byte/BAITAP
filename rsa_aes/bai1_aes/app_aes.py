"""
BÀI TẬP 1: MÃ HOÁ ĐỐI XỨNG AES-256 (MÃ HOÁ, GIẢI MÃ CÙNG DÙNG 1 KHOÁ)
Thư mục: rsa_aes/bai1_aes
Hỗ trợ cả 2 chế độ:
  - Form App: python app_aes.py
  - Console App: python app_aes.py --console (hoặc -c)

Nội dung đầy đủ:
  1. Sinh khoá AES (256-bit = 32 bytes)
  2. Lưu khoá ra file (.key nhị phân & .b64 Base64)
  3. Import khoá từ file
  4. Mã hoá 1 đoạn văn bản -> kết quả mã hoá ra màn hình (GCM có nonce & tag)
  5. Mã hoá 1 file -> lưu vào 1 file (CBC streaming chunk 64KB, hỗ trợ hàng GB)
  Yêu cầu:
    - Thử nghiệm với file kích thước lớn (hàng GB)
    - Tính thời gian mã hoá, thời gian giải mã (giây và MB/s)
    - Compare theo bytes: file nguồn và file giải mã
    => Kết luận dựa theo số liệu thu được
"""

import os
import sys
import time
import base64
import filecmp
import threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AES_KEY_BYTES = 32         # 256 bit = 32 bytes
AES_CHUNK_BYTES = 64 * 1024 # 64 KB chunk cho file lớn
AES_BLOCK_BYTES = 16


# -----------------------------------------------------------------------------
# CORE ALGORITHMS
# -----------------------------------------------------------------------------

def generate_key() -> bytes:
    """1. Sinh khoá AES-256."""
    return os.urandom(AES_KEY_BYTES)


def save_key(key: bytes, path: str) -> tuple:
    """2. Lưu khoá ra file nhị phân và file Base64."""
    bin_path = path if path.endswith('.key') else path + '.key'
    b64_path = bin_path + '.b64'
    with open(bin_path, 'wb') as f:
        f.write(key)
    with open(b64_path, 'w', encoding='ascii') as f:
        f.write(base64.b64encode(key).decode('ascii'))
    return bin_path, b64_path


def load_key(path: str) -> bytes:
    """3. Import khoá từ file."""
    if path.endswith('.b64'):
        with open(path, 'r', encoding='ascii') as f:
            key = base64.b64decode(f.read().strip())
    else:
        with open(path, 'rb') as f:
            key = f.read()
    if len(key) != AES_KEY_BYTES:
        raise ValueError(f"Khoá không hợp lệ! Cần {AES_KEY_BYTES} bytes, nhận {len(key)} bytes.")
    return key


def encrypt_text(plaintext: str, key: bytes) -> dict:
    """4. Mã hoá văn bản -> kết quả ra màn hình (GCM)."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return {
        'ciphertext_b64': base64.b64encode(ct).decode('ascii'),
        'nonce_b64': base64.b64encode(nonce).decode('ascii')
    }


def decrypt_text(ciphertext_b64: str, nonce_b64: str, key: bytes) -> str:
    """Giải mã văn bản GCM."""
    aesgcm = AESGCM(key)
    ct = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt.decode('utf-8')


def encrypt_file(src: str, dst: str, key: bytes) -> float:
    """5. Mã hoá file -> lưu file (CBC streaming chunk 64KB, file hàng GB)."""
    iv = os.urandom(AES_BLOCK_BYTES)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    enc = cipher.encryptor()
    pad = sym_padding.PKCS7(128).padder()

    t0 = time.perf_counter()
    with open(src, 'rb') as fin, open(dst, 'wb') as fout:
        fout.write(iv)
        while True:
            chunk = fin.read(AES_CHUNK_BYTES)
            if not chunk:
                break
            fout.write(enc.update(pad.update(chunk)))
        fout.write(enc.update(pad.finalize()))
        fout.write(enc.finalize())
    return time.perf_counter() - t0


def decrypt_file(src: str, dst: str, key: bytes) -> float:
    """Giải mã file CBC streaming 64KB."""
    t0 = time.perf_counter()
    with open(src, 'rb') as fin, open(dst, 'wb') as fout:
        iv = fin.read(AES_BLOCK_BYTES)
        if len(iv) < AES_BLOCK_BYTES:
            raise ValueError("File mã hoá bị hỏng!")
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        dec = cipher.decryptor()
        unpad = sym_padding.PKCS7(128).unpadder()

        while True:
            chunk = fin.read(AES_CHUNK_BYTES)
            if not chunk:
                break
            fout.write(unpad.update(dec.update(chunk)))
        fout.write(unpad.update(dec.finalize()))
        fout.write(unpad.finalize())
    return time.perf_counter() - t0


def compare_files(file_a: str, file_b: str) -> dict:
    """So sánh byte-by-byte chính xác giữa file nguồn và giải mã."""
    sz_a = os.path.getsize(file_a); sz_b = os.path.getsize(file_b)
    diff = 0
    with open(file_a, 'rb') as fa, open(file_b, 'rb') as fb:
        while True:
            ca = fa.read(AES_CHUNK_BYTES); cb = fb.read(AES_CHUNK_BYTES)
            if not ca and not cb: break
            for b1, b2 in zip(ca, cb):
                if b1 != b2: diff += 1
    diff += abs(sz_a - sz_b)
    identical = (diff == 0)
    msg = (
        "✅ KẾT LUẬN: File nguồn và file giải mã KHỚP HOÀN TOÀN 100% (0 byte sai lệch)!"
        if identical else
        f"❌ KẾT LUẬN: Hai file KHÁC NHAU! Lệch {diff:,} byte(s)."
    )
    return {'identical': identical, 'size_a': sz_a, 'size_b': sz_b, 'diff_bytes': diff, 'conclusion': msg}


def make_dummy_file(path: str, size_mb: int = 50):
    """Sinh file test ngẫu nhiên."""
    total = size_mb * 1024 * 1024
    written = 0
    chunk = 1024 * 1024
    with open(path, 'wb') as f:
        while written < total:
            w = min(chunk, total - written)
            f.write(os.urandom(w))
            written += w


# -----------------------------------------------------------------------------
# GIAO DIỆN FORM DESKTOP (TKINTER FORM APP)
# -----------------------------------------------------------------------------

def run_form():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext

    class AESForm(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("BÀI 1: MÃ HOÁ ĐỐI XỨNG AES-256 (FORM APP)")
            self.geometry("950, 700")
            self.minsize(850, 600)
            self.key = None

            # Header
            h = tk.Frame(self, bg="#1e3a8a", height=50)
            h.pack(fill="x", side="top")
            tk.Label(h, text="BÀI 1: MÃ HOÁ ĐỐI XỨNG AES-256 (FORM)", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#1e3a8a").pack(side="left", padx=15, pady=10)
            tk.Label(h, text="Mã hoá & Giải mã cùng dùng 1 khoá", font=("Segoe UI", 9, "italic"), fg="#bfdbfe", bg="#1e3a8a").pack(side="right", padx=15, pady=12)

            self.st_var = tk.StringVar(value="Sẵn sàng.")
            sb = tk.Label(self, textvariable=self.st_var, bd=1, relief="sunken", anchor="w", font=("Segoe UI", 9), bg="#f8fafc", padx=10, pady=3)
            sb.pack(side="bottom", fill="x")

            cv = tk.Canvas(self); sby = ttk.Scrollbar(self, orient="vertical", command=cv.yview)
            f = ttk.Frame(cv)
            f.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
            cv.create_window((0, 0), window=f, anchor="nw"); cv.configure(xscrollcommand=sby.set)
            cv.pack(side="left", fill="both", expand=True); sby.pack(side="right", fill="y")

            # 1, 2, 3: Key
            g1 = ttk.LabelFrame(f, text="1, 2, 3. Quản lý khoá AES-256 (32 bytes = 256 bit)", padding=8)
            g1.pack(fill="x", padx=10, pady=5)
            r1 = ttk.Frame(g1); r1.pack(fill="x", pady=2)
            ttk.Button(r1, text="1. Sinh khoá AES", command=self.gen_k).pack(side="left", padx=3)
            ttk.Button(r1, text="2. Lưu khoá ra file", command=self.save_k).pack(side="left", padx=3)
            ttk.Button(r1, text="3. Import khoá từ file", command=self.load_k).pack(side="left", padx=3)

            r2 = ttk.Frame(g1); r2.pack(fill="x", pady=2)
            ttk.Label(r2, text="Khoá (Hex):").pack(side="left")
            self.ent_hex = ttk.Entry(r2, font=("Consolas", 9)); self.ent_hex.pack(side="left", fill="x", expand=True, padx=4)

            # 4: Text
            g2 = ttk.LabelFrame(f, text="4. Mã hoá 1 đoạn văn bản -> Kết quả ra màn hình (GCM)", padding=8)
            g2.pack(fill="x", padx=10, pady=5)
            ttk.Label(g2, text="Văn bản gốc:").pack(anchor="w")
            self.ent_pt = ttk.Entry(g2, font=("Segoe UI", 9)); self.ent_pt.insert(0, "Văn bản thử nghiệm mã hoá AES-256 đối xứng tiếng Việt."); self.ent_pt.pack(fill="x", pady=2)
            rb = ttk.Frame(g2); rb.pack(fill="x", pady=2)
            ttk.Button(rb, text="Mã hoá Text", command=self.enc_t).pack(side="left", padx=3)
            ttk.Button(rb, text="Giải mã Text", command=self.dec_t).pack(side="left", padx=3)
            ttk.Label(g2, text="Ciphertext (Base64):").pack(anchor="w")
            self.ent_ct = ttk.Entry(g2, font=("Consolas", 8)); self.ent_ct.pack(fill="x", pady=1)
            ttk.Label(g2, text="Nonce (Base64 12 bytes):").pack(anchor="w")
            self.ent_nc = ttk.Entry(g2, font=("Consolas", 8)); self.ent_nc.pack(fill="x", pady=1)
            ttk.Label(g2, text="Kết quả giải mã:").pack(anchor="w")
            self.ent_dec = ttk.Entry(g2, font=("Segoe UI", 9)); self.ent_dec.pack(fill="x", pady=1)

            # 5, Y/c: File
            g3 = ttk.LabelFrame(f, text="5, Y/C. Mã hoá file lớn (hàng GB), Đo thời gian & Compare theo bytes", padding=8)
            g3.pack(fill="x", padx=10, pady=5)

            rf1 = ttk.Frame(g3); rf1.pack(fill="x", pady=2)
            ttk.Label(rf1, text="File nguồn:").pack(side="left")
            self.e_src = ttk.Entry(rf1); self.e_src.pack(side="left", fill="x", expand=True, padx=3)
            ttk.Button(rf1, text="Chọn...", command=self.br_src).pack(side="left")

            rf2 = ttk.Frame(g3); rf2.pack(fill="x", pady=2)
            ttk.Label(rf2, text="File mã hoá:").pack(side="left")
            self.e_enc = ttk.Entry(rf2); self.e_enc.pack(side="left", fill="x", expand=True, padx=3)
            ttk.Button(rf2, text="Chọn...", command=self.br_enc).pack(side="left")

            rf3 = ttk.Frame(g3); rf3.pack(fill="x", pady=2)
            ttk.Label(rf3, text="File giải mã:").pack(side="left")
            self.e_dec = ttk.Entry(rf3); self.e_dec.pack(side="left", fill="x", expand=True, padx=3)
            ttk.Button(rf3, text="Chọn...", command=self.br_dec).pack(side="left")

            rfb = ttk.Frame(g3); rfb.pack(fill="x", pady=4)
            ttk.Label(rfb, text="Dung lượng test (MB):").pack(side="left")
            self.sp_mb = ttk.Spinbox(rfb, from_=10, to=2048, width=5)
            self.sp_mb.set(100) # Mặc định 100 MB, có thể chọn 1024 MB = 1 GB
            self.sp_mb.pack(side="left", padx=3)
            ttk.Button(rfb, text="Tạo file test", command=lambda: self.gen_f(int(self.sp_mb.get()))).pack(side="left", padx=3)
            ttk.Button(rfb, text="Tạo nhanh 1 GB", command=lambda: self.gen_f(1024)).pack(side="left", padx=3)
            ttk.Button(rfb, text="Mã hoá File", command=self.enc_f).pack(side="left", padx=3)
            ttk.Button(rfb, text="Giải mã File", command=self.dec_f).pack(side="left", padx=3)
            ttk.Button(rfb, text="Compare theo Bytes", command=self.cmp_f).pack(side="left", padx=3)

            self.txt_log = scrolledtext.ScrolledText(g3, height=8, font=("Consolas", 9), bg="#f8fafc")
            self.txt_log.pack(fill="x", pady=4)

        def gen_k(self):
            self.key = generate_key()
            self.ent_hex.delete(0, tk.END); self.ent_hex.insert(0, self.key.hex())
            self.st_var.set("Đã sinh khoá AES-256 mới.")

        def save_k(self):
            if not self.key: messagebox.showwarning("Lỗi", "Chưa có khoá!"); return
            p = filedialog.asksaveasfilename(defaultextension=".key")
            if p:
                b1, b2 = save_key(self.key, p)
                messagebox.showinfo("Lưu khoá", f"Đã lưu:\n- {b1}\n- {b2}")

        def load_k(self):
            p = filedialog.askopenfilename()
            if p:
                try:
                    self.key = load_key(p)
                    self.ent_hex.delete(0, tk.END); self.ent_hex.insert(0, self.key.hex())
                    self.st_var.set(f"Đã nạp khoá: {p}")
                except Exception as e:
                    messagebox.showerror("Lỗi", str(e))

        def enc_t(self):
            if not self.key: self.gen_k()
            res = encrypt_text(self.ent_pt.get(), self.key)
            self.ent_ct.delete(0, tk.END); self.ent_ct.insert(0, res['ciphertext_b64'])
            self.ent_nc.delete(0, tk.END); self.ent_nc.insert(0, res['nonce_b64'])
            self.st_var.set("Mã hoá văn bản thành công.")

        def dec_t(self):
            if not self.key: messagebox.showwarning("Lỗi", "Thiếu khoá!"); return
            try:
                pt = decrypt_text(self.ent_ct.get().strip(), self.ent_nc.get().strip(), self.key)
                self.ent_dec.delete(0, tk.END); self.ent_dec.insert(0, pt)
                self.st_var.set("Giải mã văn bản thành công.")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

        def br_src(self):
            p = filedialog.askopenfilename()
            if p:
                self.e_src.delete(0, tk.END); self.e_src.insert(0, p)
                self.e_enc.delete(0, tk.END); self.e_enc.insert(0, p + ".enc")
                self.e_dec.delete(0, tk.END); self.e_dec.insert(0, p + ".dec")

        def br_enc(self):
            p = filedialog.asksaveasfilename()
            if p: self.e_enc.delete(0, tk.END); self.e_enc.insert(0, p)

        def br_dec(self):
            p = filedialog.asksaveasfilename()
            if p: self.e_dec.delete(0, tk.END); self.e_dec.insert(0, p)

        def gen_f(self, mb):
            p = os.path.join(os.getcwd(), f"test_{mb}mb.bin")
            self.st_var.set(f"Đang sinh file {mb} MB...")
            def worker():
                make_dummy_file(p, mb)
                self.after(0, lambda: [
                    self.e_src.delete(0, tk.END), self.e_src.insert(0, p),
                    self.e_enc.delete(0, tk.END), self.e_enc.insert(0, p + ".enc"),
                    self.e_dec.delete(0, tk.END), self.e_dec.insert(0, p + ".dec"),
                    self.txt_log.insert(tk.END, f"[✔] Đã tạo file ngẫu nhiên: {p} ({mb} MB)\n"),
                    self.st_var.set("Sinh file xong.")
                ])
            threading.Thread(target=worker, daemon=True).start()

        def enc_f(self):
            if not self.key: self.gen_k()
            s = self.e_src.get().strip(); d = self.e_enc.get().strip()
            if not os.path.isfile(s): messagebox.showwarning("Lỗi", "File nguồn không tồn tại!"); return
            sz = os.path.getsize(s) / (1024 * 1024)
            self.st_var.set("Đang mã hoá...")
            def worker():
                t = encrypt_file(s, d, self.key)
                spd = sz / t if t > 0 else 0
                msg = f"[MÃ HOÁ] {sz:.1f} MB | Thời gian: {t:.3f}s | Tốc độ: {spd:.1f} MB/s -> {os.path.basename(d)}\n"
                self.after(0, lambda: [self.txt_log.insert(tk.END, msg), self.st_var.set("Mã hoá xong.")])
            threading.Thread(target=worker, daemon=True).start()

        def dec_f(self):
            if not self.key: messagebox.showwarning("Lỗi", "Thiếu khoá!"); return
            s = self.e_enc.get().strip(); d = self.e_dec.get().strip()
            if not os.path.isfile(s): messagebox.showwarning("Lỗi", "File mã hoá không tồn tại!"); return
            sz = os.path.getsize(s) / (1024 * 1024)
            self.st_var.set("Đang giải mã...")
            def worker():
                try:
                    t = decrypt_file(s, d, self.key)
                    out_sz = os.path.getsize(d) / (1024 * 1024)
                    spd = out_sz / t if t > 0 else 0
                    msg = f"[GIẢI MÃ] {out_sz:.1f} MB | Thời gian: {t:.3f}s | Tốc độ: {spd:.1f} MB/s -> {os.path.basename(d)}\n"
                    self.after(0, lambda: [self.txt_log.insert(tk.END, msg), self.st_var.set("Giải mã xong.")])
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
            threading.Thread(target=worker, daemon=True).start()

        def cmp_f(self):
            f1 = self.e_src.get().strip(); f2 = self.e_dec.get().strip()
            if not os.path.isfile(f1) or not os.path.isfile(f2):
                messagebox.showwarning("Lỗi", "File không tồn tại!"); return
            res = compare_files(f1, f2)
            log = (
                f"── COMPARE THEO BYTES ──────────────────────────────────\n"
                f"File nguồn   : {os.path.basename(f1)} ({res['size_a']:,} bytes)\n"
                f"File giải mã : {os.path.basename(f2)} ({res['size_b']:,} bytes)\n"
                f"Bytes lệch   : {res['diff_bytes']:,} bytes\n"
                f"{res['conclusion']}\n"
                f"────────────────────────────────────────────────────────\n"
            )
            self.txt_log.insert(tk.END, log)

    AESForm().mainloop()


# -----------------------------------------------------------------------------
# GIAO DIỆN CONSOLE (CLI)
# -----------------------------------------------------------------------------

def run_console():
    k = None
    while True:
        print("\n" + "=" * 60)
        print("  BÀI 1: MÃ HOÁ ĐỐI XỨNG AES-256 (CONSOLE APP)")
        print("=" * 60)
        print("  [1] 1. Sinh khoá AES")
        print("  [2] 2. Lưu khoá ra file (.key & .key.b64)")
        print("  [3] 3. Import khoá từ file")
        print("  [4] 4. Mã hoá 1 đoạn văn bản -> in ra màn hình")
        print("  [5] 5, Y/c. Mã hoá file lớn, đo thời gian & so sánh bytes")
        print("  [0] Thoát")
        print("-" * 60)
        c = input("Chọn [0-5]: ").strip()
        if c == '0': break
        elif c == '1':
            k = generate_key()
            print(f"Khoá AES-256: {k.hex()}")
        elif c == '2':
            if not k: k = generate_key()
            p = input("Nhập tên file lưu (vd: mykey): ") or "aes256"
            b1, b2 = save_key(k, p)
            print(f"Đã lưu: {b1} và {b2}")
        elif c == '3':
            p = input("Nhập đường dẫn file khoá (.key / .b64): ")
            try:
                k = load_key(p)
                print(f"Import thành công khoá: {k.hex()}")
            except Exception as e: print(f"Lỗi: {e}")
        elif c == '4':
            if not k: k = generate_key()
            t = input("Nhập văn bản cần mã hoá: ") or "Xin chào thế giới AES!"
            res = encrypt_text(t, k)
            print(f"Plaintext  : {t}")
            print(f"Ciphertext : {res['ciphertext_b64']}")
            print(f"Nonce      : {res['nonce_b64']}")
            pt = decrypt_text(res['ciphertext_b64'], res['nonce_b64'], k)
            print(f"Giải mã    : {pt} -> {'✅ KHỚP' if pt == t else '❌'}")
        elif c == '5':
            if not k: k = generate_key()
            mb_s = input("Dung lượng file test (MB, mặc định 50): ") or "50"
            mb = int(mb_s)
            src = f"test_{mb}mb.bin"; enc_f = src + ".enc"; dec_f = src + ".dec"
            print(f"Đang sinh file {mb} MB...")
            make_dummy_file(src, mb)
            print("Đang mã hoá...")
            t_e = encrypt_file(src, enc_f, k)
            print(f"Mã hoá : {t_e:.3f}s | Tốc độ: {(mb/t_e):.1f} MB/s")
            print("Đang giải mã...")
            t_d = decrypt_file(enc_f, dec_f, k)
            print(f"Giải mã: {t_d:.3f}s | Tốc độ: {(mb/t_d):.1f} MB/s")
            res = compare_files(src, dec_f)
            print(res['conclusion'])
            for f in [src, enc_f, dec_f]:
                if os.path.exists(f): os.remove(f)
        input("\nNhấn Enter tiếp tục...")


if __name__ == "__main__":
    if "--console" in sys.argv or "-c" in sys.argv or "--cli" in sys.argv:
        run_console()
    else:
        try:
            run_form()
        except Exception:
            run_console()

using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

// =========================================================================
// BÀI 2: MÃ HOÁ BẤT ĐỐI XỨNG RSA & CHỮ KÝ SỐ
// Sinh viên thực hiện : Nguyễn Văn Mạnh
// Mã số sinh viên     : K235480106082
// Lớp                 : 59KMT
// Môn học             : An toàn và Bảo mật Thông tin (ThS. Đỗ Duy Cốp)
// =========================================================================
class MainForm : Form
{
    TextBox txtLog   = new TextBox();   // vung hien ket qua
    TextBox txtInput = new TextBox();   // o nhap du lieu

    // cac file dung chung
    string filePublic  = "public.pem";
    string filePrivate = "private.pem";
    string fileBanMa   = "data_mahoa.txt";

    byte[] duLieuGoc   = null;  // du lieu truoc khi ma hoa (de so sanh)
    string hashLanTruoc = "";   // hash lan truoc (de xem thay doi)

    public MainForm()
    {
        Text = "Bài 2 - RSA (Nguyễn Văn Mạnh - K235480106082)";
        Size = new Size(1000, 700);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 9);

        // khung ben trai chua cac nut
        Panel trai = new Panel();
        trai.AutoScroll = true;
        trai.Dock = DockStyle.Fill;
        trai.Padding = new Padding(8);

        Label lbl = new Label();
        lbl.Text = "Du lieu nhap (cho muc 5, 8, 9):";
        lbl.Left = 8; lbl.Top = 8; lbl.Width = 240;
        trai.Controls.Add(lbl);

        txtInput.Left = 8; txtInput.Top = 30; txtInput.Width = 240;
        trai.Controls.Add(txtInput);

        int y = 66;
        y = ThemNut(trai, "1-2. Sinh cap khoa + luu PEM",         y, SinhKhoa);
        y = ThemNut(trai, "3-4. Xem PEM + y nghia cac byte",      y, XemPem);
        y = ThemNut(trai, "5. Ma hoa du lieu (public key)",        y, MaHoaDuLieu);
        y = ThemNut(trai, "6. Giai ma + so sanh (private key)",   y, GiaiMaDuLieu);
        y = ThemNut(trai, "7. Do toc do: ma hoa vs giai ma",      y, DoTocDo);
        y = ThemNut(trai, "8. Bam SHA-256 + Avalanche Effect",    y, BamSha256);
        y = ThemNut(trai, "9a. Ky so PKCS#1 v1.5 (2 lan)",       y, KyV15);
        y = ThemNut(trai, "9b. Ky so PSS - moi lan khac nhau",   y, KyPss);
        y = ThemNut(trai, "Xoa man hinh",                          y, XoaLog);

        // vung log ben phai
        txtLog.Multiline = true;
        txtLog.ReadOnly = true;
        txtLog.ScrollBars = ScrollBars.Both;
        txtLog.WordWrap = false;
        txtLog.Dock = DockStyle.Fill;
        txtLog.Font = new Font("Consolas", 10);

        // dung TableLayoutPanel cho chac (1 cot trai co dinh, 1 cot log co gian)
        TableLayoutPanel bang = new TableLayoutPanel();
        bang.Dock = DockStyle.Fill;
        bang.ColumnCount = 2;
        bang.RowCount = 1;
        bang.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 270));
        bang.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        bang.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        bang.Controls.Add(trai, 0, 0);
        bang.Controls.Add(txtLog, 1, 0);
        Controls.Add(bang);

        Log("Chao ban. Bam nut 1 de sinh cap khoa truoc tien.");
    }

    // tao 1 nut va tra ve toa do y cho nut ke tiep
    static int ThemNut(Control cha, string ten, int y, EventHandler viec)
    {
        Button b = new Button();
        b.Text = ten;
        b.Left = 8; b.Top = y;
        b.Width = 240; b.Height = 32;
        b.Click += viec;
        cha.Controls.Add(b);
        return y + 38;
    }

    void Log(string s)   { txtLog.AppendText(s + "\r\n"); }
    void XoaLog(object sender, EventArgs e) { txtLog.Clear(); }

    // =====================================================================
    // 1 + 2. sinh cap khoa roi xuat ra file PEM
    // =====================================================================
    void SinhKhoa(object sender, EventArgs e)
    {
        using (RSA rsa = RSA.Create(2048))
        {
            File.WriteAllText(filePublic,  rsa.ExportSubjectPublicKeyInfoPem());
            File.WriteAllText(filePrivate, rsa.ExportRSAPrivateKeyPem());
        }

        Log("Da sinh cap khoa RSA-2048.");
        Log("Public key  -> " + filePublic  + "  (-----BEGIN PUBLIC KEY-----)");
        Log("Private key -> " + filePrivate + " (-----BEGIN RSA PRIVATE KEY-----)");
    }

    // =====================================================================
    // 3 + 4. xem noi dung PEM va giai thich y nghia cac truong ASN.1
    // =====================================================================
    void XemPem(object sender, EventArgs e)
    {
        if (!File.Exists(filePublic))
        {
            Log("Chua co file PEM. Bam nut 1 truoc da.");
            return;
        }

        Log("--- NOI DUNG " + filePublic + " ---");
        Log(File.ReadAllText(filePublic).Trim());
        Log("");

        Log("Giai thich dinh dang PEM:");
        Log("- Dong -----BEGIN/END----- chi la moc bao, khong phai du lieu.");
        Log("- Phan o giua la du lieu nhi phan (ASN.1 DER) da ma hoa Base64.");
        Log("- Giai Base64 ra, du lieu chia theo kieu Tag - Length - Value (TLV):");
        Log("    Tag 0x30 = SEQUENCE (khoi lon chua cac truong con)");
        Log("    Tag 0x02 = INTEGER  (chua cac so nguyen: n, e, d, p, q, dP, dQ, qInv)");
        Log("    Tag 0x06 = OID      (dinh danh thuat toan: 1.2.840.113549.1.1.1 = rsaEncryption)");
        Log("    Tag 0x03 = BIT STRING (chua chuoi bit)");
        Log("    Tag 0x05 = NULL     (tham so trong)");
        Log("");

        // import lai public key de lay n va e
        using (RSA k = RSA.Create())
        {
            k.ImportFromPem(File.ReadAllText(filePublic));
            RSAParameters p = k.ExportParameters(false);

            Log("Cac tham so trong PUBLIC KEY:");
            Log("  n (modulus)  = " + p.Modulus.Length + " byte (" + k.KeySize + " bit)");
            Log("  e (exponent) = " + p.Exponent.Length + " byte = " + BitConverter.ToString(p.Exponent)
                + "  (= " + DecodeBigEndianInt(p.Exponent) + " = 65537 = 2^16 + 1)");
            Log("  n (base64)   = " + Convert.ToBase64String(p.Modulus));
        }

        Log("");

        // import private key de lay n, e, d, p, q, dP, dQ, qInv
        if (File.Exists(filePrivate))
        {
            using (RSA k = RSA.Create())
            {
                k.ImportFromPem(File.ReadAllText(filePrivate));
                RSAParameters p = k.ExportParameters(true);

                Log("Cac tham so trong PRIVATE KEY:");
                Log("  n       (modulus)    = " + p.Modulus.Length   + " byte  (tich p*q)");
                Log("  e       (public exp) = " + p.Exponent.Length  + " byte  (= 65537)");
                Log("  d       (private exp)= " + p.D.Length         + " byte  (kep bi mat)");
                Log("  p       (nguyen to 1)= " + p.P.Length         + " byte");
                Log("  q       (nguyen to 2)= " + p.Q.Length         + " byte");
                Log("  dP = d mod (p-1)     = " + p.DP.Length        + " byte  (toi uu CRT)");
                Log("  dQ = d mod (q-1)     = " + p.DQ.Length        + " byte  (toi uu CRT)");
                Log("  qInv = q^-1 mod p    = " + p.InverseQ.Length  + " byte  (toi uu CRT)");
                Log("  Kiem tra: p * q = n  => " + (p.P.Length + p.Q.Length == p.Modulus.Length ? "DUNG (do dai khop)" : "can kiem tra ky hon"));
            }
        }
    }

    // giai ma so nguyen big-endian tu mang byte (cho e nho)
    static long DecodeBigEndianInt(byte[] b)
    {
        long r = 0;
        foreach (byte x in b) r = r * 256 + x;
        return r;
    }

    // =====================================================================
    // 5. ma hoa du lieu (khong qua 190 byte) bang public key RSA-OAEP
    // =====================================================================
    void MaHoaDuLieu(object sender, EventArgs e)
    {
        if (!File.Exists(filePublic))
        {
            Log("Chua co public key. Bam nut 1 truoc da.");
            return;
        }

        byte[] duLieu;
        if (txtInput.Text.Length > 0)
        {
            duLieu = Encoding.UTF8.GetBytes(txtInput.Text);
        }
        else
        {
            // khong nhap gi thi lay 32 byte ngau nhien (gia lap khoa AES-256)
            duLieu = new byte[32];
            RandomNumberGenerator.Fill(duLieu);
        }

        if (duLieu.Length > 190)
        {
            Log("Du lieu dai qua (" + duLieu.Length + " byte). RSA-2048 OAEP/SHA256 chi ma hoa toi da 190 byte.");
            return;
        }

        duLieuGoc = duLieu;

        using (RSA k = RSA.Create())
        {
            k.ImportFromPem(File.ReadAllText(filePublic));
            byte[] banMa = k.Encrypt(duLieu, RSAEncryptionPadding.OaepSHA256);

            File.WriteAllText(fileBanMa, Convert.ToBase64String(banMa));

            Log("Du lieu goc (" + duLieu.Length + " byte): " + Convert.ToBase64String(duLieu));
            Log("Ban ma      (" + banMa.Length  + " byte): " + Convert.ToBase64String(banMa));
            Log("Da luu ban ma (base64) vao " + fileBanMa);
        }
    }

    // =====================================================================
    // 6. giai ma bang private key roi so sanh voi du lieu goc
    // =====================================================================
    void GiaiMaDuLieu(object sender, EventArgs e)
    {
        if (!File.Exists(filePrivate))
        {
            Log("Chua co private key. Bam nut 1 truoc da.");
            return;
        }
        if (!File.Exists(fileBanMa))
        {
            Log("Chua co file ban ma. Bam nut 5 truoc da.");
            return;
        }

        byte[] banMa = Convert.FromBase64String(File.ReadAllText(fileBanMa));

        using (RSA k = RSA.Create())
        {
            k.ImportFromPem(File.ReadAllText(filePrivate));
            byte[] lai = k.Decrypt(banMa, RSAEncryptionPadding.OaepSHA256);

            Log("Du lieu giai ma (" + lai.Length + " byte): " + Convert.ToBase64String(lai));

            if (duLieuGoc != null)
            {
                bool giong = GiongNhau(lai, duLieuGoc);
                Log("So voi du lieu goc: " + (giong ? "GIONG HET (100%)" : "KHAC NHAU"));
            }
            else
            {
                Log("(Chua co du lieu goc trong bo nho de so sanh.)");
            }
        }
    }

    // =====================================================================
    // 7. do toc do ma hoa (public key, e nho) vs giai ma (private key, d lon)
    // =====================================================================
    void DoTocDo(object sender, EventArgs e)
    {
        if (!File.Exists(filePublic) || !File.Exists(filePrivate))
        {
            Log("Chua co khoa. Bam nut 1 truoc da.");
            return;
        }

        using (RSA pub = RSA.Create())
        using (RSA pri = RSA.Create())
        {
            pub.ImportFromPem(File.ReadAllText(filePublic));
            pri.ImportFromPem(File.ReadAllText(filePrivate));

            byte[] duLieu = new byte[32]; // 32 byte = khoa AES-256
            RandomNumberGenerator.Fill(duLieu);

            int soLan = 100;

            // ma hoa bang public key (e = 65537, chi 17 bit)
            Stopwatch sw = Stopwatch.StartNew();
            byte[] banMa = null;
            for (int i = 0; i < soLan; i++)
                banMa = pub.Encrypt(duLieu, RSAEncryptionPadding.OaepSHA256);
            sw.Stop();
            double tMa = sw.Elapsed.TotalMilliseconds / soLan;

            // giai ma bang private key (d ~ 2048 bit)
            sw.Restart();
            for (int i = 0; i < soLan; i++)
                pri.Decrypt(banMa, RSAEncryptionPadding.OaepSHA256);
            sw.Stop();
            double tGiai = sw.Elapsed.TotalMilliseconds / soLan;

            Log("Do toc do (" + soLan + " lan, RSA-2048, OAEP/SHA-256):");
            Log("  Ma hoa  (public key,  e = 65537 nho) : " + tMa.ToString("0.0000")  + " ms/lan");
            Log("  Giai ma (private key, d ~ 2048 bit)  : " + tGiai.ToString("0.0000") + " ms/lan");
            Log("  => Giai ma cham hon khoang " + (tGiai / tMa).ToString("0.0") + " lan");
            Log("");
            Log("  Giai thich:");
            Log("  e = 65537 = 2^16 + 1, bieu dien nhi phan chi co 2 bit 1.");
            Log("  => Square-and-Multiply chi can ~17 phep nhan modular.");
            Log("  d ngau nhien ~2048 bit, trung binh ~1024 bit 1.");
            Log("  => Square-and-Multiply can ~3072 phep nhan modular.");
            Log("  => d lon hon e nhieu nen giai ma cham hon nhieu.");
        }
    }

    // =====================================================================
    // 8. bam SHA-256 va Avalanche Effect
    // =====================================================================
    void BamSha256(object sender, EventArgs e)
    {
        string s = txtInput.Text;
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(s));
        string hex  = Convert.ToHexString(hash);

        Log("Du lieu : \"" + s + "\"");
        Log("SHA-256 : " + hex);

        if (hashLanTruoc != "")
        {
            int khac = DemBitKhac(hashLanTruoc, hex);
            int phan = khac * 100 / 256;
            Log("So bit khac voi lan bam truoc: " + khac + "/256 (" + phan + "%)");
            Log("=> Doi du lieu chi 1 chut ma hash doi gan mot nua so bit (Avalanche Effect).");
        }

        hashLanTruoc = hex;
    }

    // =====================================================================
    // 9a. ky so bang PKCS#1 v1.5 -> ky nhieu lan cung ra 1 ket qua
    //     (minh hoa de doi chieu voi PSS)
    // =====================================================================
    void KyV15(object sender, EventArgs e)
    {
        if (!File.Exists(filePrivate))
        {
            Log("Chua co private key. Bam nut 1 truoc da.");
            return;
        }

        string s = txtInput.Text.Length > 0 ? txtInput.Text : "Xin chao";
        byte[] duLieu = Encoding.UTF8.GetBytes(s);

        using (RSA k = RSA.Create())
        {
            k.ImportFromPem(File.ReadAllText(filePrivate));

            byte[] c1 = k.SignData(duLieu, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
            byte[] c2 = k.SignData(duLieu, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);

            Log("Ky 2 lan bang PKCS#1 v1.5 (cung du lieu, cung private key):");
            Log("  Chu ky lan 1: " + Convert.ToBase64String(c1));
            Log("  Chu ky lan 2: " + Convert.ToBase64String(c2));
            Log("  Giong nhau?  " + GiongNhau(c1, c2));
            Log("  => v1.5 la kieu ky tat dinh, ky may lan cung ra 1 ket qua.");
        }
    }

    // =====================================================================
    // 9b. ky so bang PSS -> moi lan ra 1 chu ky khac nhau (co salt ngau nhien)
    //     DE XUAT: dung PSS thay cho v1.5 de dat duoc yeu cau nay
    // =====================================================================
    void KyPss(object sender, EventArgs e)
    {
        if (!File.Exists(filePrivate) || !File.Exists(filePublic))
        {
            Log("Chua co khoa. Bam nut 1 truoc da.");
            return;
        }

        string s = txtInput.Text.Length > 0 ? txtInput.Text : "Xin chao";
        byte[] duLieu = Encoding.UTF8.GetBytes(s);

        using (RSA k = RSA.Create())
        {
            k.ImportFromPem(File.ReadAllText(filePrivate));

            byte[] c1 = k.SignData(duLieu, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);
            byte[] c2 = k.SignData(duLieu, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);

            Log("Ky 2 lan bang RSA-PSS (cung du lieu, cung private key):");
            Log("  Chu ky lan 1: " + Convert.ToBase64String(c1));
            Log("  Chu ky lan 2: " + Convert.ToBase64String(c2));
            Log("  Giong nhau?  " + GiongNhau(c1, c2));
            Log("");

            // van xac minh dung bang public key
            using (RSA pub = RSA.Create())
            {
                pub.ImportFromPem(File.ReadAllText(filePublic));
                Log("  Xac minh lai bang public key:");
                Log("    Lan 1 dung? " + pub.VerifyData(duLieu, c1, HashAlgorithmName.SHA256, RSASignaturePadding.Pss));
                Log("    Lan 2 dung? " + pub.VerifyData(duLieu, c2, HashAlgorithmName.SHA256, RSASignaturePadding.Pss));
            }

            Log("");
            Log("=> DE XUAT: dung PSS thay cho v1.5. PSS nhat them 1 chuoi salt ngau");
            Log("   nhien moi lan ky nen cung du lieu + cung nguoi ky se ra chu ky KHAC");
            Log("   nhau, nhung van xac minh dung bang cung public key.");
            Log("   Chong tan cong Replay Attack trong he thong ngan hang, chung thuc.");
        }
    }

    // ---- ham phu ----

    static bool GiongNhau(byte[] a, byte[] b)
    {
        if (a.Length != b.Length) return false;
        for (int i = 0; i < a.Length; i++)
            if (a[i] != b[i]) return false;
        return true;
    }

    // dem so bit khac nhau giua 2 chuoi hash hex (Hamming distance)
    static int DemBitKhac(string h1, string h2)
    {
        int dem = 0;
        for (int i = 0; i < Math.Min(h1.Length, h2.Length); i++)
        {
            int a = Convert.ToInt32(h1.Substring(i, 1), 16);
            int b = Convert.ToInt32(h2.Substring(i, 1), 16);
            int x = a ^ b;
            while (x > 0) { dem += x & 1; x >>= 1; }
        }
        return dem;
    }
}

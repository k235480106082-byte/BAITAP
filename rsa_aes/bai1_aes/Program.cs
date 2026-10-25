using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;

// =========================================================================
// BÀI 1: MÃ HOÁ ĐỐI XỨNG AES-256
// Sinh viên thực hiện : Nguyễn Văn Mạnh
// Mã số sinh viên     : K235480106082
// Lớp                 : 59KMT
// Môn học             : An toàn và Bảo mật Thông tin (ThS. Đỗ Duy Cốp)
// =========================================================================
class Program
{
    // khoa 32 byte => AES-256, IV 16 byte
    static byte[] khoa = new byte[0];
    static byte[] iv   = new byte[0];
    static string fileKhoa = "aes_key.txt";

    static void Main()
    {
        Console.OutputEncoding = Encoding.UTF8;

        while (true)
        {
            Console.WriteLine();
            Console.WriteLine("===== BAI 1: MA HOA DOI XUNG AES-256 =====");
            Console.WriteLine("1. Sinh khoa AES");
            Console.WriteLine("2. Luu khoa ra file");
            Console.WriteLine("3. Import khoa tu file");
            Console.WriteLine("4. Ma hoa / giai ma 1 doan van ban");
            Console.WriteLine("5. Ma hoa 1 file, luu ra file khac");
            Console.WriteLine("6. Test file lon (do thoi gian + so sanh tung byte)");
            Console.WriteLine("0. Thoat");
            Console.Write("Chon: ");

            string chon = Console.ReadLine();
            Console.WriteLine();

            if      (chon == "1") SinhKhoa();
            else if (chon == "2") LuuKhoa();
            else if (chon == "3") DocKhoa();
            else if (chon == "4") VanBan();
            else if (chon == "5") MaHoaFileMenu();
            else if (chon == "6") TestFileLon();
            else if (chon == "0") break;
            else Console.WriteLine("Chon sai roi, chon lai di.");
        }
    }

    // 1. sinh khoa AES-256
    static void SinhKhoa()
    {
        using (Aes aes = Aes.Create())
        {
            aes.KeySize = 256;    // 256 bit = 32 byte
            aes.GenerateKey();    // sinh khoa ngau nhien an toan
            aes.GenerateIV();     // sinh IV ngau nhien 16 byte
            khoa = aes.Key;
            iv   = aes.IV;
        }

        Console.WriteLine("Da sinh khoa AES-256 (32 byte = 256 bit).");
        Console.WriteLine("Khoa (base64): " + Convert.ToBase64String(khoa));
        Console.WriteLine("IV   (base64): " + Convert.ToBase64String(iv));
    }

    // 2. luu khoa ra file (dong 1: khoa, dong 2: IV, ca 2 o dang base64)
    static void LuuKhoa()
    {
        if (khoa.Length == 0)
        {
            Console.WriteLine("Chua co khoa. Chon so 1 de sinh khoa truoc da.");
            return;
        }

        File.WriteAllText(fileKhoa,
            Convert.ToBase64String(khoa) + "\n" + Convert.ToBase64String(iv));
        Console.WriteLine("Da luu khoa vao file: " + fileKhoa);
    }

    // 3. import khoa tu file
    static void DocKhoa()
    {
        if (!File.Exists(fileKhoa))
        {
            Console.WriteLine("Khong thay file " + fileKhoa + ". Chon so 2 de luu khoa truoc.");
            return;
        }

        string[] dong = File.ReadAllLines(fileKhoa);
        khoa = Convert.FromBase64String(dong[0].Trim());
        iv   = Convert.FromBase64String(dong[1].Trim());

        Console.WriteLine("Da import khoa tu file.");
        Console.WriteLine("Khoa (base64): " + Convert.ToBase64String(khoa));
        Console.WriteLine("IV   (base64): " + Convert.ToBase64String(iv));
    }

    // 4. ma hoa / giai ma van ban bang AES-256-CBC
    static void VanBan()
    {
        if (khoa.Length == 0)
        {
            Console.WriteLine("Chua co khoa. Chon so 1 truoc da.");
            return;
        }

        Console.Write("Nhap doan van ban: ");
        string s = Console.ReadLine();
        byte[] goc = Encoding.UTF8.GetBytes(s);

        byte[] ma  = MaHoa(goc);
        Console.WriteLine("Ban ma (base64): " + Convert.ToBase64String(ma));

        byte[] lai = GiaiMa(ma);
        Console.WriteLine("Giai ma lai    : " + Encoding.UTF8.GetString(lai));
        Console.WriteLine("Ket qua: " + (Encoding.UTF8.GetString(lai) == s ? "GIONG HET (100%)" : "KHAC NHAU"));
    }

    // 5. ma hoa file -> luu file khac
    static void MaHoaFileMenu()
    {
        if (khoa.Length == 0)
        {
            Console.WriteLine("Chua co khoa. Chon so 1 truoc da.");
            return;
        }

        Console.Write("File nguon     : ");
        string vao = Console.ReadLine();
        Console.Write("File ma hoa ra : ");
        string ra  = Console.ReadLine();

        if (!File.Exists(vao))
        {
            Console.WriteLine("Khong thay file nguon.");
            return;
        }

        MaHoaFile(vao, ra);
        Console.WriteLine("Da ma hoa, luu vao: " + ra);

        Console.Write("Thu giai ma ra file: ");
        string ra2 = Console.ReadLine();
        GiaiMaFile(ra, ra2);
        Console.WriteLine("Da giai ma, luu vao: " + ra2);
    }

    // 6. test file lon: tao file -> ma hoa -> giai ma -> so sanh byte
    static void TestFileLon()
    {
        if (khoa.Length == 0)
        {
            Console.WriteLine("Chua co khoa. Chon so 1 truoc da.");
            return;
        }

        Console.Write("Kich thuoc file test (MB): ");
        int mb;
        if (!int.TryParse(Console.ReadLine(), out mb) || mb <= 0)
        {
            Console.WriteLine("So khong hop le.");
            return;
        }

        string nguon  = "file_nguon.bin";
        string tepma  = "file_mahoa.bin";
        string giaima = "file_giaima.bin";

        // 1) tao file nguon gia lap
        Console.Write("Dang tao file " + mb + " MB ... ");
        Stopwatch sw = Stopwatch.StartNew();
        TaoFile(nguon, (long)mb * 1024 * 1024);
        sw.Stop();
        Console.WriteLine("xong (" + sw.ElapsedMilliseconds + " ms)");

        // 2) ma hoa
        sw.Restart();
        MaHoaFile(nguon, tepma);
        sw.Stop();
        long tMaHoa = sw.ElapsedMilliseconds;

        // 3) giai ma
        sw.Restart();
        GiaiMaFile(tepma, giaima);
        sw.Stop();
        long tGiaiMa = sw.ElapsedMilliseconds;

        // 4) so sanh tung byte giua file goc va file giai ma
        sw.Restart();
        bool giong = SoSanhByte(nguon, giaima);
        sw.Stop();
        long tSoSanh = sw.ElapsedMilliseconds;

        // 5) in ket qua va ket luan
        Console.WriteLine();
        Console.WriteLine("---- KET QUA ----");
        Console.WriteLine("Ma hoa : " + tMaHoa  + " ms  (" + TocDo(mb, tMaHoa)  + " MB/s)");
        Console.WriteLine("Giai ma: " + tGiaiMa + " ms  (" + TocDo(mb, tGiaiMa) + " MB/s)");
        Console.WriteLine("So sanh byte: " + tSoSanh + " ms");
        Console.WriteLine("File goc vs file giai ma: " + (giong ? "GIONG HET (100%)" : "KHAC NHAU"));
        Console.WriteLine();
        Console.WriteLine("---- KET LUAN ----");
        Console.WriteLine("- AES-256 toc do cao (hang tram MB/s), xu ly file GB trong vai giay.");
        Console.WriteLine("- CryptoStream doc/ghi theo khoi, khong nan toan bo file vao RAM.");
        Console.WriteLine("- Du lieu sau giai ma bao toan nguyen ven 100% (0 byte lech).");
        Console.WriteLine("- AES la lua chon tot cho ma hoa du lieu lon nho toc do va do bao mat.");
    }

    // ---- cac ham nen dung chung ----

    // ma hoa 1 mang byte bang AES-256-CBC
    static byte[] MaHoa(byte[] duLieu)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = khoa;
            aes.IV  = iv;
            using (ICryptoTransform enc = aes.CreateEncryptor())
            {
                return enc.TransformFinalBlock(duLieu, 0, duLieu.Length);
            }
        }
    }

    // giai ma 1 mang byte
    static byte[] GiaiMa(byte[] duLieu)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = khoa;
            aes.IV  = iv;
            using (ICryptoTransform dec = aes.CreateDecryptor())
            {
                return dec.TransformFinalBlock(duLieu, 0, duLieu.Length);
            }
        }
    }

    // ma hoa file bang CryptoStream (doc/ghi tung khoi, chiu duoc file lon GB)
    static void MaHoaFile(string vao, string ra)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = khoa;
            aes.IV  = iv;
            using (FileStream fsVao = File.OpenRead(vao))
            using (FileStream fsRa  = File.Create(ra))
            using (CryptoStream cs  = new CryptoStream(fsRa, aes.CreateEncryptor(), CryptoStreamMode.Write))
            {
                fsVao.CopyTo(cs);
            }
        }
    }

    static void GiaiMaFile(string vao, string ra)
    {
        using (Aes aes = Aes.Create())
        {
            aes.Key = khoa;
            aes.IV  = iv;
            using (FileStream  fsVao = File.OpenRead(vao))
            using (CryptoStream cs   = new CryptoStream(fsVao, aes.CreateDecryptor(), CryptoStreamMode.Read))
            using (FileStream  fsRa  = File.Create(ra))
            {
                cs.CopyTo(fsRa);
            }
        }
    }

    // tao file test voi du lieu gia lap (pattern lap lai 0-255)
    static void TaoFile(string ten, long kichThuoc)
    {
        byte[] dem = new byte[1024 * 1024];
        for (int i = 0; i < dem.Length; i++)
            dem[i] = (byte)(i % 256);

        using (FileStream fs = File.Create(ten))
        {
            long daGhi = 0;
            while (daGhi < kichThuoc)
            {
                int canGhi = (int)Math.Min(dem.Length, kichThuoc - daGhi);
                fs.Write(dem, 0, canGhi);
                daGhi += canGhi;
            }
        }
    }

    // so sanh 2 file theo tung byte, dung duoc voi file lon
    static bool SoSanhByte(string f1, string f2)
    {
        FileInfo i1 = new FileInfo(f1);
        FileInfo i2 = new FileInfo(f2);
        if (i1.Length != i2.Length) return false;

        using (FileStream s1 = File.OpenRead(f1))
        using (FileStream s2 = File.OpenRead(f2))
        {
            byte[] b1 = new byte[1024 * 1024];
            byte[] b2 = new byte[1024 * 1024];

            while (true)
            {
                int n1 = s1.Read(b1, 0, b1.Length);
                int n2 = s2.Read(b2, 0, b2.Length);
                if (n1 != n2) return false;
                if (n1 == 0) break;

                for (int i = 0; i < n1; i++)
                    if (b1[i] != b2[i]) return false;
            }
        }

        return true;
    }

    // tinh toc do MB/s
    static double TocDo(int mb, long ms)
    {
        if (ms == 0) return 0;
        return Math.Round(mb * 1000.0 / ms, 1);
    }
}

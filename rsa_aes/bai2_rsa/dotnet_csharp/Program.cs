using System;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Security.Cryptography;

namespace RSA_ATTT
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.OutputEncoding = Encoding.UTF8;
            Console.WriteLine("=================================================================");
            Console.WriteLine("   BÀI TẬP 2: MÃ HOÁ BẤT ĐỐI XỨNG RSA & CHỮ KÝ SỐ (.NET C#)");
            Console.WriteLine("=================================================================");

            // 1. Sinh cặp khoá RSA-2048
            Console.WriteLine("\n[1] Sinh cặp khoá RSA-2048...");
            using RSA rsa = RSA.Create(2048);
            Console.WriteLine("    [OK] Đã sinh cặp khoá RSA-2048 bit.");

            // 2. Xuất cặp khoá ra file PEM
            Console.WriteLine("\n[2] Xuất cặp khoá ra file PEM...");
            string privPem = rsa.ExportRSAPrivateKeyPem();
            string pubPem = rsa.ExportSubjectPublicKeyInfoPem();
            File.WriteAllText("private.pem", privPem);
            File.WriteAllText("public.pem", pubPem);
            Console.WriteLine("    [OK] Đã lưu private.pem và public.pem.");

            // 3. View PEM & ý nghĩa byte
            Console.WriteLine("\n[3] View PEM & Cấu trúc ASN.1 DER bytes:");
            Console.WriteLine("    Private Key PEM Header: -----BEGIN RSA PRIVATE KEY-----");
            byte[] derBytes = rsa.ExportRSAPrivateKey();
            Console.WriteLine($"    Độ dài DER nhị phân: {derBytes.Length} bytes.");
            Console.WriteLine("    Cấu trúc ASN.1: Tag 0x30 (SEQUENCE), Tag 0x02 (INTEGER chứa n, e, d, p, q, dP, dQ, qInv)");

            // 4. Nhập file PEM: trích xuất n, e, d, p, q...
            Console.WriteLine("\n[4] Nhập lại file PEM vừa xuất...");
            using RSA rsaLoaded = RSA.Create();
            rsaLoaded.ImportFromPem(File.ReadAllText("private.pem"));
            RSAParameters p = rsaLoaded.ExportParameters(true);
            Console.WriteLine($"    Modulus n ({p.Modulus!.Length * 8} bit): {Convert.ToHexString(p.Modulus)[..40]}...");
            Console.WriteLine($"    Public Exponent e: {Convert.ToHexString(p.Exponent!)} (65537)");
            Console.WriteLine($"    Private Exponent d: {Convert.ToHexString(p.D!)[..40]}...");

            // 5. Mã hoá mảng byte <= 190 byte (khoá AES 32 bytes)
            Console.WriteLine("\n[5] Mã hoá khoá AES-256 (32 bytes) bằng RSA-OAEP SHA-256...");
            byte[] aesKey = RandomNumberGenerator.GetBytes(32);
            Console.WriteLine($"    Khoá AES gốc (32 bytes): {Convert.ToHexString(aesKey)}");
            byte[] cipher = rsaLoaded.Encrypt(aesKey, RSAEncryptionPadding.OaepSHA256);
            string b64Cipher = Convert.ToBase64String(cipher);
            File.WriteAllText("encrypted_key.b64", b64Cipher);
            Console.WriteLine($"    Ciphertext Base64 ({b64Cipher.Length} ký tự) -> Lưu 'encrypted_key.b64'");

            // 6. Giải mã & so sánh kết quả
            Console.WriteLine("\n[6] Giải mã từ file Base64 và đối chiếu với nguồn...");
            byte[] readCipher = Convert.FromBase64String(File.ReadAllText("encrypted_key.b64"));
            byte[] decrypted = rsaLoaded.Decrypt(readCipher, RSAEncryptionPadding.OaepSHA256);
            Console.WriteLine($"    Kết quả giải mã: {Convert.ToHexString(decrypted)}");
            bool match = Convert.ToHexString(aesKey) == Convert.ToHexString(decrypted);
            Console.WriteLine($"    => So sánh với nguồn ban đầu: {(match ? "✅ KHỚP TUYỆT ĐỐI 100%" : "❌ SAI LỆCH")}");

            // 7. Đánh giá tốc độ e nhỏ vs d to đùng
            Console.WriteLine("\n[7] Đánh giá tốc độ: Public Key (e = 65537 bé) vs Private Key (d to đùng)...");
            Stopwatch sw = Stopwatch.StartNew();
            for (int i = 0; i < 50; i++) rsaLoaded.Encrypt(aesKey, RSAEncryptionPadding.OaepSHA256);
            sw.Stop();
            double encMs = sw.Elapsed.TotalMilliseconds / 50.0;

            sw.Restart();
            for (int i = 0; i < 50; i++) rsaLoaded.Decrypt(cipher, RSAEncryptionPadding.OaepSHA256);
            sw.Stop();
            double decMs = sw.Elapsed.TotalMilliseconds / 50.0;
            Console.WriteLine($"    Mã hoá (Public Key e bé): {encMs:F3} ms [CỰC NHANH]");
            Console.WriteLine($"    Giải mã (Private Key d to): {decMs:F3} ms [CHẬM HƠN {decMs/encMs:F1} lần]");

            // 8. Băm SHA-256 & Avalanche Effect
            Console.WriteLine("\n[8] Băm SHA-256 & Đánh giá Avalanche Effect...");
            byte[] h1 = SHA256.HashData(Encoding.UTF8.GetBytes("hello"));
            byte[] h2 = SHA256.HashData(Encoding.UTF8.GetBytes("Hello"));
            Console.WriteLine($"    SHA256('hello'): {Convert.ToHexString(h1)}");
            Console.WriteLine($"    SHA256('Hello'): {Convert.ToHexString(h2)}");
            int diffBits = 0;
            for (int i = 0; i < 32; i++)
            {
                byte x = (byte)(h1[i] ^ h2[i]);
                while (x > 0) { diffBits += (x & 1); x >>= 1; }
            }
            Console.WriteLine($"    Số bit khác nhau: {diffBits}/256 bit ({diffBits * 100.0 / 256:F1}%) -> Hiệu ứng tuyết lở!");

            // 9. Chữ ký số RSA-PSS: Ký 2 lần khác nhau
            Console.WriteLine("\n[9] Chữ ký số RSA-PSS: Cùng dữ liệu, cùng Private Key -> Chữ ký KHÁC NHAU mỗi lần ký!");
            byte[] dataToSign = Encoding.UTF8.GetBytes("Thông điệp quan trọng");
            byte[] sig1 = rsaLoaded.SignData(dataToSign, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);
            byte[] sig2 = rsaLoaded.SignData(dataToSign, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);
            Console.WriteLine($"    Chữ ký 1: {Convert.ToHexString(sig1)[..30]}...");
            Console.WriteLine($"    Chữ ký 2: {Convert.ToHexString(sig2)[..30]}...");
            Console.WriteLine($"    Chữ ký 1 == Chữ ký 2? {Convert.ToHexString(sig1) == Convert.ToHexString(sig2)} (KHÁC NHAU HOÀN TOÀN)");
            bool v1 = rsaLoaded.VerifyData(dataToSign, sig1, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);
            bool v2 = rsaLoaded.VerifyData(dataToSign, sig2, HashAlgorithmName.SHA256, RSASignaturePadding.Pss);
            Console.WriteLine($"    Verify Chữ ký 1: {(v1 ? "PASS" : "FAIL")}");
            Console.WriteLine($"    Verify Chữ ký 2: {(v2 ? "PASS" : "FAIL")}");
            Console.WriteLine("    => ĐỀ XUẤT: Dùng chuẩn RSA-PSS với Random Salt để chữ ký khác nhau mỗi lần ký, chống Replay Attack!");
            Console.WriteLine("\n=================================================================");
        }
    }
}

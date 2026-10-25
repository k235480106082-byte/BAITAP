using System;
using System.Windows.Forms;

// Bai 2: Ma hoa bat doi xung RSA
// Diem vao Windows Forms
static class Program2
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new MainForm());
    }
}

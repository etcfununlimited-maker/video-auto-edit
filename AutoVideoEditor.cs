using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows.Forms;
using System.Net;

[assembly: System.Reflection.AssemblyTitle("Auto Video Editor Studio Pro")]
[assembly: System.Reflection.AssemblyProduct("Auto Video Editor")]
[assembly: System.Reflection.AssemblyCompany("Anirban Automations")]
[assembly: System.Reflection.AssemblyVersion("2.4.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("2.4.0.0")]

namespace AutoVideoEditor
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            string appDir = AppDomain.CurrentDomain.BaseDirectory;
            string pythonExe = FindPythonExecutable(appDir);

            if (string.IsNullOrEmpty(pythonExe))
            {
                DialogResult res = MessageBox.Show(
                    "Python 3.12 was not detected on this system.\n\nWould you like to open the official Python download page?",
                    "Auto Video Editor - Dependency Missing",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Warning
                );
                if (res == DialogResult.Yes)
                {
                    Process.Start(new ProcessStartInfo("https://www.python.org/downloads/") { UseShellExecute = true });
                }
                return;
            }

            string launcherScript = Path.Combine(appDir, "launcher.py");
            if (!File.Exists(launcherScript))
            {
                MessageBox.Show(
                    "launcher.py was not found in:\n" + appDir,
                    "Auto Video Editor Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return;
            }

            // Ensure runtime directories exist
            string[] dirs = { "raw_input", "final_export", "uploads", "exports" };
            foreach (var d in dirs)
            {
                string p = Path.Combine(appDir, d);
                if (!Directory.Exists(p)) Directory.CreateDirectory(p);
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pythonExe;
            psi.Arguments = string.Format("\"{0}\"", launcherScript);
            psi.WorkingDirectory = appDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = false;

            try
            {
                Process proc = Process.Start(psi);

                // Background thread to check when server is responsive and open browser
                Thread t = new Thread(() =>
                {
                    Thread.Sleep(1200);
                    for (int i = 0; i < 20; i++)
                    {
                        try
                        {
                            HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8000/");
                            req.Timeout = 1000;
                            using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                            {
                                if (resp.StatusCode == HttpStatusCode.OK) break;
                            }
                        }
                        catch { Thread.Sleep(300); }
                    }
                    Process.Start(new ProcessStartInfo("http://localhost:8000") { UseShellExecute = true });
                });
                t.IsBackground = true;
                t.Start();

                proc.WaitForExit();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Failed to start Auto Video Editor:\n" + ex.Message, "Launch Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        static string FindPythonExecutable(string appDir)
        {
            // 1. Check local portable python inside app directory
            string localPython = Path.Combine(appDir, "python", "python.exe");
            if (File.Exists(localPython)) return localPython;

            // 2. Check user LocalAppData python
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string userPython312 = Path.Combine(localAppData, @"Programs\Python\Python312\python.exe");
            if (File.Exists(userPython312)) return userPython312;

            string userPython311 = Path.Combine(localAppData, @"Programs\Python\Python311\python.exe");
            if (File.Exists(userPython311)) return userPython311;

            // 3. Check Program Files
            string pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            string pfPython = Path.Combine(pf, @"Python312\python.exe");
            if (File.Exists(pfPython)) return pfPython;

            // 4. Check if python is in PATH
            try
            {
                Process p = new Process();
                p.StartInfo.FileName = "python.exe";
                p.StartInfo.Arguments = "--version";
                p.StartInfo.UseShellExecute = false;
                p.StartInfo.CreateNoWindow = true;
                p.Start();
                p.WaitForExit();
                if (p.ExitCode == 0) return "python.exe";
            }
            catch { }

            return null;
        }
    }
}

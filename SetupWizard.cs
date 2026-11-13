using System;
using System.Drawing;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Auto Video Editor Setup Wizard")]
[assembly: AssemblyProduct("Auto Video Editor")]
[assembly: AssemblyCompany("Anirban Automations")]
[assembly: AssemblyVersion("2.4.0.0")]
[assembly: AssemblyFileVersion("2.4.0.0")]

namespace AutoVideoEditorSetup
{
    public class SetupForm : Form
    {
        private TextBox txtInstallPath;
        private Button btnBrowse;
        private CheckBox chkDesktopShortcut;
        private CheckBox chkStartMenu;
        private CheckBox chkLaunchNow;
        private ProgressBar progressBar;
        private Label lblStatus;
        private Button btnAction;
        private Button btnCancel;
        private bool isInstalled = false;

        public SetupForm()
        {
            this.Text = "Auto Video Editor Studio - Setup Wizard";
            this.Size = new Size(580, 440);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.BackColor = Color.FromArgb(15, 23, 42); // Obsidian Slate
            this.ForeColor = Color.FromArgb(248, 250, 252);
            this.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);

            // Try load icon
            try
            {
                this.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
            }
            catch { }

            InitControls();
        }

        private void InitControls()
        {
            // Top Header Panel
            Panel pnlHeader = new Panel();
            pnlHeader.Dock = DockStyle.Top;
            pnlHeader.Height = 80;
            pnlHeader.BackColor = Color.FromArgb(30, 41, 59);

            Label lblTitle = new Label();
            lblTitle.Text = "ANIRBAN AUTOMATIONS";
            lblTitle.Font = new Font("Segoe UI", 8f, FontStyle.Bold);
            lblTitle.ForeColor = Color.FromArgb(56, 189, 248);
            lblTitle.Location = new Point(24, 14);
            lblTitle.AutoSize = true;

            Label lblHeading = new Label();
            lblHeading.Text = "Auto Video Editor Studio • Setup Wizard";
            lblHeading.Font = new Font("Segoe UI", 13f, FontStyle.Bold);
            lblHeading.ForeColor = Color.FromArgb(248, 250, 252);
            lblHeading.Location = new Point(23, 30);
            lblHeading.AutoSize = true;

            Label lblSub = new Label();
            lblSub.Text = "v2.4 Pro Edition  *  iPhone 16 HEVC/HDR  *  12-Grid Pipeline";
            lblSub.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            lblSub.ForeColor = Color.FromArgb(148, 163, 184);
            lblSub.Location = new Point(24, 55);
            lblSub.AutoSize = true;

            pnlHeader.Controls.Add(lblTitle);
            pnlHeader.Controls.Add(lblHeading);
            pnlHeader.Controls.Add(lblSub);
            this.Controls.Add(pnlHeader);

            // Destination Folder Label
            Label lblDest = new Label();
            lblDest.Text = "Installation Folder:";
            lblDest.Location = new Point(24, 105);
            lblDest.AutoSize = true;
            lblDest.ForeColor = Color.FromArgb(226, 232, 240);
            this.Controls.Add(lblDest);

            // Default Path: %LocalAppData%\Programs\AutoVideoEditor
            string defaultPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                @"Programs\AutoVideoEditor"
            );

            txtInstallPath = new TextBox();
            txtInstallPath.Text = defaultPath;
            txtInstallPath.Location = new Point(24, 130);
            txtInstallPath.Size = new Size(410, 26);
            txtInstallPath.BackColor = Color.FromArgb(30, 41, 59);
            txtInstallPath.ForeColor = Color.FromArgb(248, 250, 252);
            txtInstallPath.BorderStyle = BorderStyle.FixedSingle;
            this.Controls.Add(txtInstallPath);

            btnBrowse = new Button();
            btnBrowse.Text = "Browse...";
            btnBrowse.Location = new Point(446, 128);
            btnBrowse.Size = new Size(95, 29);
            btnBrowse.BackColor = Color.FromArgb(51, 65, 85);
            btnBrowse.ForeColor = Color.White;
            btnBrowse.FlatStyle = FlatStyle.Flat;
            btnBrowse.FlatAppearance.BorderSize = 0;
            btnBrowse.Cursor = Cursors.Hand;
            btnBrowse.Click += (s, e) =>
            {
                using (FolderBrowserDialog fbd = new FolderBrowserDialog())
                {
                    fbd.SelectedPath = txtInstallPath.Text;
                    if (fbd.ShowDialog() == DialogResult.OK)
                    {
                        txtInstallPath.Text = fbd.SelectedPath;
                    }
                }
            };
            this.Controls.Add(btnBrowse);

            // Options Checkboxes
            chkDesktopShortcut = new CheckBox();
            chkDesktopShortcut.Text = "Create Desktop Shortcut (Auto Video Editor)";
            chkDesktopShortcut.Checked = true;
            chkDesktopShortcut.Location = new Point(26, 175);
            chkDesktopShortcut.Size = new Size(450, 24);
            chkDesktopShortcut.ForeColor = Color.FromArgb(226, 232, 240);
            this.Controls.Add(chkDesktopShortcut);

            chkStartMenu = new CheckBox();
            chkStartMenu.Text = "Create Start Menu Program Shortcut";
            chkStartMenu.Checked = true;
            chkStartMenu.Location = new Point(26, 205);
            chkStartMenu.Size = new Size(450, 24);
            chkStartMenu.ForeColor = Color.FromArgb(226, 232, 240);
            this.Controls.Add(chkStartMenu);

            chkLaunchNow = new CheckBox();
            chkLaunchNow.Text = "Launch Auto Video Editor Studio when finished";
            chkLaunchNow.Checked = true;
            chkLaunchNow.Location = new Point(26, 235);
            chkLaunchNow.Size = new Size(450, 24);
            chkLaunchNow.ForeColor = Color.FromArgb(226, 232, 240);
            this.Controls.Add(chkLaunchNow);

            // Status label & progress bar
            lblStatus = new Label();
            lblStatus.Text = "Ready to install. Click 'Install' to begin.";
            lblStatus.Location = new Point(24, 280);
            lblStatus.Size = new Size(515, 20);
            lblStatus.ForeColor = Color.FromArgb(56, 189, 248);
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar();
            progressBar.Location = new Point(24, 305);
            progressBar.Size = new Size(517, 18);
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 0;
            this.Controls.Add(progressBar);

            // Bottom Buttons
            btnAction = new Button();
            btnAction.Text = "Install";
            btnAction.Location = new Point(426, 345);
            btnAction.Size = new Size(115, 34);
            btnAction.BackColor = Color.FromArgb(14, 165, 233);
            btnAction.ForeColor = Color.White;
            btnAction.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            btnAction.FlatStyle = FlatStyle.Flat;
            btnAction.FlatAppearance.BorderSize = 0;
            btnAction.Cursor = Cursors.Hand;
            btnAction.Click += BtnAction_Click;
            this.Controls.Add(btnAction);

            btnCancel = new Button();
            btnCancel.Text = "Cancel";
            btnCancel.Location = new Point(300, 345);
            btnCancel.Size = new Size(115, 34);
            btnCancel.BackColor = Color.FromArgb(51, 65, 85);
            btnCancel.ForeColor = Color.White;
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Cursor = Cursors.Hand;
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);
        }

        private void BtnAction_Click(object sender, EventArgs e)
        {
            if (isInstalled)
            {
                // Finished: Launch if requested and close
                string targetDir = txtInstallPath.Text.Trim();
                string exePath = Path.Combine(targetDir, "AutoVideoEditor.exe");
                if (chkLaunchNow.Checked && File.Exists(exePath))
                {
                    Process.Start(new ProcessStartInfo(exePath) { WorkingDirectory = targetDir });
                }
                this.Close();
                return;
            }

            // Start Installation Process
            btnAction.Enabled = false;
            btnBrowse.Enabled = false;
            txtInstallPath.ReadOnly = true;
            btnCancel.Enabled = false;

            Thread worker = new Thread(DoInstall);
            worker.IsBackground = true;
            worker.Start();
        }

        private void DoInstall()
        {
            try
            {
                string targetDir = txtInstallPath.Text.Trim();
                UpdateStatus("Preparing destination directory...", 10);
                if (!Directory.Exists(targetDir))
                {
                    Directory.CreateDirectory(targetDir);
                }

                UpdateStatus("Extracting core studio files...", 25);

                // Check for embedded resource "app_bundle.zip"
                Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("app_bundle.zip");
                string tempZip = Path.Combine(Path.GetTempPath(), "ave_bundle_" + Guid.NewGuid().ToString("N") + ".zip");

                if (stream != null)
                {
                    using (FileStream fs = new FileStream(tempZip, FileMode.Create, FileAccess.Write))
                    {
                        byte[] buffer = new byte[81920];
                        int read;
                        while ((read = stream.Read(buffer, 0, buffer.Length)) > 0)
                        {
                            fs.Write(buffer, 0, read);
                        }
                    }
                    stream.Close();
                }
                else
                {
                    // Fallback to local app_bundle.zip if running beside installer
                    string localZip = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app_bundle.zip");
                    if (File.Exists(localZip))
                    {
                        File.Copy(localZip, tempZip, true);
                    }
                }

                UpdateStatus("Deploying application packages...", 50);
                if (File.Exists(tempZip))
                {
                    ZipFile.ExtractToDirectory(tempZip, targetDir);
                    try { File.Delete(tempZip); } catch { }
                }

                UpdateStatus("Creating workspace directories (raw_input, final_export)...", 75);
                string[] subfolders = { "raw_input", "final_export", "uploads", "exports" };
                foreach (var sf in subfolders)
                {
                    string p = Path.Combine(targetDir, sf);
                    if (!Directory.Exists(p)) Directory.CreateDirectory(p);
                }

                // Create Uninstaller script
                CreateUninstaller(targetDir);

                string exePath = Path.Combine(targetDir, "AutoVideoEditor.exe");
                string iconPath = Path.Combine(targetDir, "app_icon.ico");

                if (chkDesktopShortcut.Checked)
                {
                    UpdateStatus("Creating Desktop Shortcut...", 85);
                    string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                    string lnk = Path.Combine(desktop, "Auto Video Editor.lnk");
                    CreateWindowsShortcut(lnk, exePath, targetDir, iconPath, "Auto Video Editor Studio Pro");
                }

                if (chkStartMenu.Checked)
                {
                    UpdateStatus("Creating Start Menu group...", 95);
                    string startMenu = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                        @"Microsoft\Windows\Start Menu\Programs\Auto Video Editor"
                    );
                    if (!Directory.Exists(startMenu)) Directory.CreateDirectory(startMenu);
                    string lnk = Path.Combine(startMenu, "Auto Video Editor.lnk");
                    CreateWindowsShortcut(lnk, exePath, targetDir, iconPath, "Auto Video Editor Studio Pro");
                }

                UpdateStatus("Installation successfully completed! (100%)", 100);

                this.Invoke((MethodInvoker)delegate
                {
                    isInstalled = true;
                    btnAction.Text = "Finish";
                    btnAction.Enabled = true;
                    btnAction.BackColor = Color.FromArgb(16, 185, 129); // Green Finish
                    btnCancel.Visible = false;
                    lblStatus.ForeColor = Color.FromArgb(52, 211, 153);
                    lblStatus.Text = "Successfully installed! Click 'Finish' to launch.";
                });
            }
            catch (Exception ex)
            {
                this.Invoke((MethodInvoker)delegate
                {
                    MessageBox.Show("Installation failed:\n" + ex.Message, "Install Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    btnAction.Enabled = true;
                    btnCancel.Enabled = true;
                    lblStatus.Text = "Installation failed: " + ex.Message;
                    lblStatus.ForeColor = Color.FromArgb(239, 68, 68);
                });
            }
        }

        private void UpdateStatus(string message, int progress)
        {
            if (this.InvokeRequired)
            {
                this.Invoke((MethodInvoker)delegate { UpdateStatus(message, progress); });
                return;
            }
            lblStatus.Text = message;
            progressBar.Value = Math.Min(100, Math.Max(0, progress));
        }

        private void CreateWindowsShortcut(string shortcutPath, string targetExe, string workingDir, string iconPath, string description)
        {
            try
            {
                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                if (shellType == null) return;
                dynamic shell = Activator.CreateInstance(shellType);
                dynamic shortcut = shell.CreateShortcut(shortcutPath);
                shortcut.TargetPath = targetExe;
                shortcut.WorkingDirectory = workingDir;
                if (File.Exists(iconPath))
                {
                    shortcut.IconLocation = string.Format("{0},0", iconPath);
                }
                shortcut.Description = description;
                shortcut.Save();
            }
            catch { }
        }

        private void CreateUninstaller(string targetDir)
        {
            try
            {
                string batPath = Path.Combine(targetDir, "Uninstall.bat");
                string content = string.Format(
                    "@echo off\r\n" +
                    "echo ====================================================\r\n" +
                    "echo           Uninstalling Auto Video Editor\r\n" +
                    "echo ====================================================\r\n" +
                    "taskkill /f /im AutoVideoEditor.exe 2>nul\r\n" +
                    "timeout /t 1 >nul\r\n" +
                    "del /f /q \"{0}\\Auto Video Editor.lnk\" 2>nul\r\n" +
                    "rmdir /s /q \"{1}\\Auto Video Editor\" 2>nul\r\n" +
                    "echo Removing files in {2}...\r\n" +
                    "echo To finish cleanup, this folder will be deleted upon window close.\r\n" +
                    "echo Uninstallation finished successfully.\r\n" +
                    "pause\r\n",
                    Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), @"Microsoft\Windows\Start Menu\Programs"),
                    targetDir
                );
                File.WriteAllText(batPath, content);
            }
            catch { }
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}

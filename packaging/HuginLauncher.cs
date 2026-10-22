// Thin Windows starter; the existing Python application owns input/audio lifetime.
using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Reflection;

[assembly: AssemblyTitle("Hugin")]
[assembly: AssemblyDescription("Lokales Diktieren und Vorlesen")]
[assembly: AssemblyProduct("Hugin")]
[assembly: AssemblyVersion("@VERSION@.0")]
[assembly: AssemblyFileVersion("@VERSION@.0")]

internal static class HuginLauncher
{
    private static string Quote(string value)
    {
        // Windows CommandLineToArgvW quoting, including trailing backslashes.
        StringBuilder result = new StringBuilder("\""); int slashes = 0;
        foreach (char c in value)
        {
            if (c == '\\') { slashes++; continue; }
            if (c == '"') { result.Append('\\', slashes * 2 + 1); result.Append(c); }
            else { result.Append('\\', slashes); result.Append(c); }
            slashes = 0;
        }
        result.Append('\\', slashes * 2); result.Append('"'); return result.ToString();
    }

    private static string InstanceName()
    {
        string sid = WindowsIdentity.GetCurrent().User.Value;
        using (SHA256 sha = SHA256.Create())
        {
            byte[] hash = sha.ComputeHash(Encoding.ASCII.GetBytes(sid));
            return "Local\\Hugin.v1." + BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant().Substring(0, 32);
        }
    }

    private static void Status(string path, string value)
    {
        string temporary = path + ".pending";
        using (FileStream file = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        using (StreamWriter writer = new StreamWriter(file, new UTF8Encoding(false))) { writer.Write(value); }
        File.Move(temporary, path); // Readiness is visible only as complete bytes.
    }

    private static int InstallGuard(string[] args)
    {
        // Parent identity includes creation time and an observed process handle.
        // The guard never terminates any process and survives until release/exit.
        if (args.Length != 8) return 2;
        bool held = false;
        using (Process parent = Process.GetProcessById(Int32.Parse(args[1])))
        using (Mutex mutex = new Mutex(false, InstanceName()))
        {
            IntPtr observedHandle = parent.Handle;
            if (parent.StartTime.ToFileTimeUtc() != Int64.Parse(args[2]) || parent.HasExited) return 2;
            try
            {
                try { held = mutex.WaitOne(0); } catch (AbandonedMutexException) { held = true; }
                if (!held) { Status(args[3], "busy"); return 3; }
                try
                {
                    using (InstallationTarget target=InstallationTarget.Open(args[5],args[6],args[7]))
                    {
                        Status(args[3], "ready");
                        while (!parent.WaitForExit(100) && !File.Exists(args[4])) { }
                    }
                }
                catch { if (!File.Exists(args[3])) Status(args[3], "target_changed"); return 4; }
            }
            finally
            {
                if (held) { mutex.ReleaseMutex(); Status(args[3] + ".closed", "closed"); }
            }
        }
        return 0;
    }

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--install-guard")
        {
            try { return InstallGuard(args); } catch { return 2; }
        }
        bool probe = args.Length == 1 && (args[0] == "--self-test" || args[0] == "--check-inputs");
        try
        {
            string root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
            string scripts = Path.Combine(root, ".runtime", "controller", "Scripts");
            string python = Path.Combine(scripts, probe ? "python.exe" : "pythonw.exe");
            string command;
            if (probe)
            {
                command = "-B " + Quote(Path.Combine(root, "tools", "installation_probe.py")) + " --root " + Quote(root);
                if (args[0] == "--check-inputs") command += " --inputs";
            }
            else
            {
                if (args.Length > 1 || (args.Length == 1 && args[0] != "--background" && args[0] != "--show" && args[0] != "--preview")) return 2;
                command = "-B " + Quote(Path.Combine(root, "tools", "launch.py")) + " --root " + Quote(root);
                if (args.Length == 1 && args[0] == "--preview") command += " --preview";
                else if (args.Length == 0 || args[0] == "--show") command += " --show";
            }
            ProcessStartInfo info = new ProcessStartInfo(python, command);
            info.WorkingDirectory = root; info.UseShellExecute = false; info.CreateNoWindow = true;
            info.RedirectStandardOutput = true; info.RedirectStandardError = true;
            foreach (string key in new string[] { "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONUSERBASE" }) info.EnvironmentVariables.Remove(key);
            info.EnvironmentVariables["TCL_LIBRARY"] = Path.Combine(scripts, "tcl", "tcl8.6");
            info.EnvironmentVariables["TK_LIBRARY"] = Path.Combine(scripts, "tcl", "tk8.6");
            using (Process child = Process.Start(info))
            {
                child.OutputDataReceived += delegate { }; child.ErrorDataReceived += delegate { };
                child.BeginOutputReadLine(); child.BeginErrorReadLine(); child.WaitForExit();
                int code = child.ExitCode;
                if (code != 0 && !probe) MessageBox.Show("Hugin konnte nicht fehlerfrei ausgeführt werden. Bitte prüfe die Installation.", "Hugin", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return code;
            }
        }
        catch
        {
            if (!probe) MessageBox.Show("Die private Hugin-Laufzeit fehlt oder konnte nicht gestartet werden. Bitte den Installer erneut ausführen.", "Hugin", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}

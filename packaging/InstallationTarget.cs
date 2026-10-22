// Owns installation-root identity and present-file coverage before Inno writes.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;

internal sealed class InstallationTarget : IDisposable
{
    [StructLayout(LayoutKind.Sequential)]
    private struct Info
    {
        public uint Attributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME Created, Accessed, Written;
        public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    private static extern SafeFileHandle CreateFile(string name, uint access, uint share, IntPtr security, uint mode, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool GetFileInformationByHandle(SafeFileHandle handle, out Info information);

    private readonly List<SafeFileHandle> handles = new List<SafeFileHandle>();
    private readonly HashSet<string> locked = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    private readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength=32*1024*1024, RecursionLimit=32 };

    private static string Hash(string path)
    {
        using (SHA256 sha=SHA256.Create())
        using (FileStream input=File.OpenRead(path))
            return BitConverter.ToString(sha.ComputeHash(input)).Replace("-", "").ToLowerInvariant();
    }

    private void LockChain(string path)
    {
        DirectoryInfo directory=new DirectoryInfo(path);
        if (locked.Contains(directory.FullName)) return;
        if (directory.Parent!=null) LockChain(directory.Parent.FullName);
        if (!Directory.Exists(directory.FullName))
        {
            if (File.Exists(directory.FullName)) throw new IOException("target_is_file");
            return;
        }
        if ((File.GetAttributes(directory.FullName)&FileAttributes.ReparsePoint)!=0) throw new IOException("target_redirected");
        if (locked.Add(directory.FullName))
        {
            // Deny DELETE sharing through the mutation window: an ancestor
            // cannot be renamed/replaced by a junction after this proof.
            SafeFileHandle handle=CreateFile(directory.FullName,0x80000000,3,IntPtr.Zero,3,0x02200000,IntPtr.Zero);
            if (handle.IsInvalid) { handle.Dispose(); throw new IOException("target_identity_unavailable"); }
            Info info;
            if (!GetFileInformationByHandle(handle,out info) || (info.Attributes&0x400)!=0)
            { handle.Dispose(); throw new IOException("target_redirected"); }
            handles.Add(handle);
        }
    }

    private string Identity(string root)
    {
        using (SafeFileHandle handle=CreateFile(root,0x80,3,IntPtr.Zero,3,0x02200000,IntPtr.Zero))
        {
            Info info;
            if (handle.IsInvalid || !GetFileInformationByHandle(handle,out info)) throw new IOException("target_identity_unavailable");
            return info.Volume.ToString("x8")+":"+info.IndexHigh.ToString("x8")+info.IndexLow.ToString("x8");
        }
    }

    private IEnumerable<string> Files(string root)
    {
        foreach (string path in Directory.GetFileSystemEntries(root))
        {
            FileAttributes attributes=File.GetAttributes(path);
            if ((attributes&FileAttributes.ReparsePoint)!=0) throw new IOException("target_redirected");
            if ((attributes&FileAttributes.Directory)!=0)
            {
                LockChain(path); // Keep each existing payload subtree stable too.
                foreach (string child in Files(path)) yield return child;
            }
            else yield return path;
        }
    }

    private static bool Retained(string relative)
    {
        if (relative.StartsWith(".runtime/state/",StringComparison.OrdinalIgnoreCase) ||
            relative.StartsWith(".runtime/desktop-setup-v1/",StringComparison.OrdinalIgnoreCase) ||
            relative.StartsWith(".runtime/production-migration-v1/",StringComparison.OrdinalIgnoreCase) ||
            Regex.IsMatch(relative,@"^\.runtime/(desktop-prepare|production-migration-prepare)-[0-9a-f-]+/",RegexOptions.IgnoreCase)) return true;
        if (relative==".runtime/production-uninstalled.json" || relative==".runtime/installation-probe.json") return true;
        if (Regex.IsMatch(relative,@"^\.installer/unins[0-9]+\.(exe|dat|msg)$",RegexOptions.IgnoreCase)) return true;
        if ((relative.StartsWith("src/") || Regex.IsMatch(relative,@"^\.runtime/(controller|stt|tts)/")) &&
            relative.Contains("/__pycache__/") && relative.EndsWith(".pyc")) return true;
        // Librosa/Numba's typed compiled-function caches are runtime output,
        // just like Python bytecode; they are never release input.
        if (relative.StartsWith(".runtime/tts/Lib/site-packages/") &&
            relative.Contains("/__pycache__/") &&
            (relative.EndsWith(".nbc") || relative.EndsWith(".nbi"))) return true;
        return relative==".hugin-installation/identity.json" || relative==".hugin-installation/manifest.json";
    }

    private void Prepare(string root,string manifestPath,string expectedHash)
    {
        if (!Regex.IsMatch(expectedHash,"^[0-9a-f]{64}$") || new FileInfo(manifestPath).Length>32*1024*1024 || Hash(manifestPath)!=expectedHash)
            throw new IOException("incoming_manifest_changed");
        Dictionary<string,object> manifest=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(manifestPath,Encoding.UTF8));
        Dictionary<string,string> records=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
        // The compiler-pinned digest authenticates the already validated producer
        // representation. This consumer only uses its filename/hash facts.
        foreach (Dictionary<string,object> record in (System.Collections.IEnumerable)manifest["files"])
            records.Add((string)record["file"],(string)record["sha256"]);
        root=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        if (root.Length<4 || root==Path.GetPathRoot(root).TrimEnd(Path.DirectorySeparatorChar)) throw new IOException("target_is_drive_root");
        LockChain(root);
        bool fresh=!Directory.Exists(root) || !Directory.EnumerateFileSystemEntries(root).Any();
        if (!Directory.Exists(root)) Directory.CreateDirectory(root);
        LockChain(root);
        string owner=Path.Combine(root,".hugin-installation");
        Dictionary<string,string> identity=new Dictionary<string,string> {
            {"product","Hugin.9835C52D-2C14-48B5-B03C-637F14587661.v1"},
            {"root",root}, {"sid",WindowsIdentity.GetCurrent().User.Value},
            {"directory_id",Identity(root)}, {"manifest_sha256",expectedHash}
        };
        string identityBytes=json.Serialize(identity);
        if (fresh)
        {
            // Prepare outside the target: a failed write leaves a fresh root
            // empty and retryable, never a half-published installation owner.
            string stage=Path.Combine(Path.GetDirectoryName(root),".hugin-install-prepare-"+Guid.NewGuid().ToString());
            Directory.CreateDirectory(stage);
            File.Copy(manifestPath,Path.Combine(stage,"manifest.json"),false);
            File.WriteAllText(Path.Combine(stage,"identity.json"),identityBytes,new UTF8Encoding(false));
            Directory.Move(stage,owner);
        }
        else
        {
            // A registry string or marker name alone never grants ownership.
            if (!Directory.Exists(owner) || File.ReadAllText(Path.Combine(owner,"identity.json"),Encoding.UTF8)!=identityBytes ||
                Hash(Path.Combine(owner,"manifest.json"))!=expectedHash) throw new IOException("target_not_owned");
        }
        // Create and hold every authenticated payload parent before publishing
        // ready, including paths absent from a fresh/partially repaired target.
        foreach (string parent in records.Keys.Select(name=>Path.GetDirectoryName(Path.Combine(root,name))).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            LockChain(parent);
            Directory.CreateDirectory(parent);
            LockChain(parent);
        }
        List<KeyValuePair<string,string>> checks=new List<KeyValuePair<string,string>>();
        foreach (string path in Files(root))
        {
            string relative=path.Substring(root.Length+1).Replace('\\','/');
            string expected;
            if (records.TryGetValue(relative,out expected))
            {
                checks.Add(new KeyValuePair<string,string>(path,expected));
            }
            else if (relative=="release-manifest.json")
            {
                if (Hash(path)!=expectedHash) throw new IOException("installed_manifest_changed");
            }
            else if (!Retained(relative)) throw new IOException("unowned_target_file");
        }
        Parallel.ForEach(checks,new ParallelOptions { MaxDegreeOfParallelism=8 },
            check=> { if (Hash(check.Key)!=check.Value) throw new IOException("owned_file_changed"); });
    }

    public static InstallationTarget Open(string root,string manifestPath,string expectedHash)
    {
        InstallationTarget owner=new InstallationTarget();
        try { owner.Prepare(root,manifestPath,expectedHash); return owner; }
        catch { owner.Dispose(); throw; }
    }

    public void Dispose()
    {
        for (int index=handles.Count-1;index>=0;index--) handles[index].Dispose();
        handles.Clear();
    }
}

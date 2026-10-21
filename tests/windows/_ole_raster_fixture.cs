// Synthetic 2x2 OLE provider. No user windows, files, input or captured images.
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Security.Cryptography;

[ComVisible(true), ClassInterface(ClassInterfaceType.None)]
public sealed class HuginRaster : IDataObject {
    public static string TracePath;
    public readonly byte[] Png;
    readonly FORMATETC[] formats;
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern uint RegisterClipboardFormat(string name);
    [DllImport("kernel32.dll")] static extern IntPtr GlobalAlloc(uint flags, UIntPtr size);
    [DllImport("kernel32.dll")] static extern IntPtr GlobalLock(IntPtr handle);
    [DllImport("kernel32.dll")] static extern bool GlobalUnlock(IntPtr handle);
    [DllImport("kernel32.dll")] static extern IntPtr GlobalFree(IntPtr handle);
    [DllImport("ole32.dll")] static extern int CreateStreamOnHGlobal(IntPtr handle, bool deleteOnRelease, out IntPtr stream);
    [DllImport("ole32.dll")] public static extern int OleInitialize(IntPtr reserved);
    [DllImport("ole32.dll")] public static extern void OleUninitialize();
    [DllImport("ole32.dll")] public static extern int OleSetClipboard(IDataObject data);
    [DllImport("ole32.dll")] public static extern int OleIsCurrentClipboard(IDataObject data);
    [DllImport("ole32.dll")] public static extern int OleFlushClipboard();
    [DllImport("ole32.dll")] static extern int OleGetClipboard(out IDataObject data);
    [DllImport("ole32.dll")] static extern void ReleaseStgMedium(ref STGMEDIUM medium);
    [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber();

    public uint Publish(uint expectedSequence) {
        // Compilation and provider construction happen before this final check.
        if(GetClipboardSequenceNumber()!=expectedSequence) throw new InvalidOperationException("clipboard changed before fixture publication");
        Marshal.ThrowExceptionForHR(OleSetClipboard(this));
        uint published=GetClipboardSequenceNumber();
        if(published==0 || OleIsCurrentClipboard(this)!=0 || GetClipboardSequenceNumber()!=published)
            throw new InvalidOperationException("clipboard changed during fixture publication");
        return published;
    }

    static Bitmap Image() {
        Bitmap b=new Bitmap(2,2,PixelFormat.Format32bppArgb);
        b.SetPixel(0,0,Color.Red); b.SetPixel(1,0,Color.FromArgb(128,30,50,70));
        b.SetPixel(0,1,Color.Blue); b.SetPixel(1,1,Color.Transparent); return b;
    }
    static FORMATETC Format(int id, TYMED medium) {
        return new FORMATETC { cfFormat=unchecked((short)id), dwAspect=DVASPECT.DVASPECT_CONTENT,
            lindex=-1, ptd=IntPtr.Zero, tymed=medium };
    }
    public HuginRaster() {
        using(Bitmap b=Image()) using(MemoryStream s=new MemoryStream()) {
            b.Save(s,ImageFormat.Png); Png=s.ToArray();
        }
        formats=new FORMATETC[] { Format(2,TYMED.TYMED_GDI),
            Format((int)RegisterClipboardFormat("PNG"),TYMED.TYMED_ISTREAM),
            Format((int)RegisterClipboardFormat("CanUploadToCloudClipboard"),TYMED.TYMED_HGLOBAL),
            Format((int)RegisterClipboardFormat("CanIncludeInClipboardHistory"),TYMED.TYMED_HGLOBAL) };
    }
    public void GetData(ref FORMATETC f, out STGMEDIUM medium) {
        if(TracePath!=null) File.AppendAllText(TracePath,String.Format("format={0}, aspect={1}, index={2}, medium={3}, query={4}\n",(ushort)f.cfFormat,f.dwAspect,f.lindex,f.tymed,QueryGetData(ref f)));
        try { GetDataCore(ref f,out medium); if(TracePath!=null) File.AppendAllText(TracePath,"GetData succeeded\n"); }
        catch(Exception error) { if(TracePath!=null) File.AppendAllText(TracePath,error.ToString()+"\n"); throw; }
    }
    void GetDataCore(ref FORMATETC f, out STGMEDIUM medium) {
        medium=new STGMEDIUM(); Marshal.ThrowExceptionForHR(QueryGetData(ref f));
        if(f.cfFormat==formats[0].cfFormat) {
            using(Bitmap b=Image()) medium.unionmember=b.GetHbitmap();
            medium.tymed=TYMED.TYMED_GDI;
        } else if(f.cfFormat==formats[1].cfFormat) {
            IntPtr h=Allocate(Png);
            int hr=CreateStreamOnHGlobal(h,true,out medium.unionmember);
            if(hr<0) { GlobalFree(h); Marshal.ThrowExceptionForHR(hr); }
            // IDataObject::GetData defines the transferred byte range by the
            // stream's exit position. An untouched stream at zero is empty.
            object streamObject=Marshal.GetObjectForIUnknown(medium.unionmember);
            try { ((IStream)streamObject).Seek(Png.Length,0,IntPtr.Zero); }
            finally { Marshal.ReleaseComObject(streamObject); }
            medium.tymed=TYMED.TYMED_ISTREAM;
        } else {
            byte[] bytes=f.cfFormat==formats[2].cfFormat ? new byte[4] : new byte[] {1,0,0,0};
            medium.unionmember=Allocate(bytes); medium.tymed=TYMED.TYMED_HGLOBAL;
        }
        if(medium.unionmember==IntPtr.Zero) throw new OutOfMemoryException();
    }
    static IntPtr Allocate(byte[] bytes) {
        IntPtr h=GlobalAlloc(2,(UIntPtr)bytes.Length);
        if(h==IntPtr.Zero) throw new OutOfMemoryException();
        IntPtr p=GlobalLock(h);
        if(p==IntPtr.Zero) { GlobalFree(h); throw new OutOfMemoryException(); }
        Marshal.Copy(bytes,0,p,bytes.Length); GlobalUnlock(h); return h;
    }
    public int QueryGetData(ref FORMATETC f) {
        foreach(FORMATETC supported in formats)
            if(f.cfFormat==supported.cfFormat && f.dwAspect==supported.dwAspect &&
               f.lindex==-1 && f.ptd==IntPtr.Zero && (f.tymed & supported.tymed)!=0) return 0;
        return unchecked((int)0x80040064);
    }
    public IEnumFORMATETC EnumFormatEtc(DATADIR direction) {
        if(direction!=DATADIR.DATADIR_GET) throw new NotImplementedException();
        return new HuginFormats(formats,0);
    }
    public void GetDataHere(ref FORMATETC f, ref STGMEDIUM m) { if(TracePath!=null) File.AppendAllText(TracePath,"GetDataHere called\n"); throw new NotImplementedException(); }
    public int GetCanonicalFormatEtc(ref FORMATETC f, out FORMATETC output) { output=f; output.ptd=IntPtr.Zero; return 0x00040130; }
    public void SetData(ref FORMATETC f, ref STGMEDIUM m, bool release) { throw new NotImplementedException(); }
    public int DAdvise(ref FORMATETC f, ADVF flags, IAdviseSink sink, out int connection) { connection=0; return unchecked((int)0x80040003); }
    public void DUnadvise(int connection) { throw new NotImplementedException(); }
    public int EnumDAdvise(out IEnumSTATDATA output) { output=null; return unchecked((int)0x80040003); }
    public static string Digest(byte[] bytes) { using(SHA256 hash=SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant(); }
    public static string ReadPngStream(uint expectedSequence) {
        if(GetClipboardSequenceNumber()!=expectedSequence) throw new InvalidOperationException("foreign clipboard");
        IDataObject data=null; STGMEDIUM medium=new STGMEDIUM(); object streamObject=null;
        try {
            Marshal.ThrowExceptionForHR(OleGetClipboard(out data));
            FORMATETC f=Format((int)RegisterClipboardFormat("PNG"),TYMED.TYMED_ISTREAM);
            data.GetData(ref f,out medium);
            if(medium.tymed!=TYMED.TYMED_ISTREAM) throw new InvalidOperationException("not a stream");
            streamObject=Marshal.GetObjectForIUnknown(medium.unionmember);
            IStream stream=(IStream)streamObject; System.Runtime.InteropServices.ComTypes.STATSTG stat; stream.Stat(out stat,1);
            if(stat.cbSize<=0 || stat.cbSize>4096) throw new InvalidOperationException("fixture size");
            byte[] bytes=new byte[(int)stat.cbSize]; IntPtr read=Marshal.AllocCoTaskMem(4);
            try { stream.Seek(0,0,IntPtr.Zero); stream.Read(bytes,bytes.Length,read); if(Marshal.ReadInt32(read)!=bytes.Length) throw new InvalidOperationException("short stream"); }
            finally { Marshal.FreeCoTaskMem(read); }
            if(GetClipboardSequenceNumber()!=expectedSequence) throw new InvalidOperationException("clipboard changed");
            return Digest(bytes);
        } finally {
            if(streamObject!=null && Marshal.IsComObject(streamObject)) Marshal.ReleaseComObject(streamObject);
            if(medium.unionmember!=IntPtr.Zero) ReleaseStgMedium(ref medium);
            if(data!=null && Marshal.IsComObject(data)) Marshal.ReleaseComObject(data);
        }
    }
}

[ComVisible(true), ClassInterface(ClassInterfaceType.None)]
public sealed class HuginFormats : IEnumFORMATETC {
    readonly FORMATETC[] formats; int offset;
    public HuginFormats(FORMATETC[] values,int at) { formats=values; offset=at; }
    public int Next(int count,FORMATETC[] values,int[] fetched) {
        int n=0; while(n<count && offset<formats.Length) values[n++]=formats[offset++];
        if(fetched!=null && fetched.Length>0) fetched[0]=n; return n==count ? 0 : 1;
    }
    public int Skip(int count) { int remaining=formats.Length-offset; offset+=Math.Min(count,remaining); return count<=remaining ? 0 : 1; }
    public int Reset() { offset=0; return 0; }
    public void Clone(out IEnumFORMATETC result) { result=new HuginFormats(formats,offset); }
}

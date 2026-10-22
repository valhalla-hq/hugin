"""Real native installation ownership against private filesystem fixtures."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[2]
HARNESS='''using System; using System.IO;
internal static class Harness {
 static int Main(string[] a) {
  try { using(InstallationTarget target=InstallationTarget.Open(a[0],a[1],a[2])) {
   Console.WriteLine("ready");
   if(a.Length>3) while(!File.Exists(a[3])) System.Threading.Thread.Sleep(50);
  } return 0; } catch(Exception e) { Console.WriteLine(e.Message); return 4; }
 }
}'''

@unittest.skipUnless(os.name=='nt','Windows native directory handles required')
class InstallationOwnership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.work=Path(cls.temp.name)
        source=cls.work/'Harness.cs';source.write_text(HARNESS,encoding='utf-8')
        cls.exe=cls.work/'Harness.exe'
        subprocess.run([str(Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
            '/nologo','/target:exe','/reference:System.Web.Extensions.dll','/out:'+str(cls.exe),
            str(ROOT/'packaging/InstallationTarget.cs'),str(source)],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.fixture=self.work/str(uuid.uuid4());self.fixture.mkdir()
        self.root=self.fixture/'Installed';self.manifest=self.fixture/'manifest.json'
        self.manifest.write_text(json.dumps(dict(files=[dict(file='app.py',size=1,
            sha256=hashlib.sha256(b'a').hexdigest())])),encoding='utf-8')
        self.sha=hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def probe(self,code):
        result=subprocess.run([str(self.exe),str(self.root),str(self.manifest),self.sha],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,code,result.stdout+result.stderr)

    def test_repeat_state_retention_and_changed_or_unknown_payload_refusal(self):
        self.probe(0);(self.root/'app.py').write_bytes(b'a');self.probe(0)
        (self.root/'foreign.dll').write_bytes(b'foreign');self.probe(4);(self.root/'foreign.dll').unlink()
        (self.root/'app.py').write_bytes(b'b');self.probe(4);(self.root/'app.py').unlink()
        state=self.root/'.runtime/state';state.mkdir(parents=True);(state/'preferences.json').write_bytes(b'sentinel')
        self.probe(0);self.assertEqual((state/'preferences.json').read_bytes(),b'sentinel')
        self.manifest.write_text('{"files":[]}',encoding='utf-8');self.sha=hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.probe(4)

    def test_unknown_directory_and_redirected_ancestor_refused(self):
        self.root.mkdir();(self.root/'foreign.txt').write_bytes(b'keep');self.probe(4)
        self.assertEqual((self.root/'foreign.txt').read_bytes(),b'keep')
        redirected=self.fixture/'junction'
        subprocess.run(['cmd','/c','mklink','/J',str(redirected),str(self.root)],check=True,capture_output=True)
        try:
            self.root=redirected/'Nested';self.probe(4)
            self.assertFalse((self.fixture/'Installed/Nested').exists())
        finally:os.rmdir(redirected) # Remove only this known junction, never its contents.

    def test_root_and_ancestor_cannot_be_replaced_during_mutation(self):
        stop=self.fixture/'stop'
        child=subprocess.Popen([str(self.exe),str(self.root),str(self.manifest),self.sha,str(stop)],stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(),'ready')
            with self.assertRaises(PermissionError):self.root.rename(self.fixture/'moved')
            with self.assertRaises(PermissionError):self.fixture.rename(self.work/'moved-fixture')
        finally:
            stop.write_bytes(b'stop');self.assertEqual(child.wait(5),0);child.stdout.close()

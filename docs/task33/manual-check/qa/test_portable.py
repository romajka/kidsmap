"""Packaging contracts; no database, server or external connections."""
import json, os, subprocess, sys, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
class PortableContracts(unittest.TestCase):
    def inspect(self, portable=False, port='8781'):
        env={'PATH':'/usr/bin:/bin','KIDSMAP_MANUAL_PORTABLE':'1' if portable else '0','KIDSMAP_PREVIEW_PORT':port}
        return subprocess.run([sys.executable,'-c',"import json,start;print(json.dumps({'root':str(start.ROOT),'python':str(start.PYTHON),'state':str(start.STATE),'owner':start.OWNER,'container':start.CONTAINER,'port':start.PORT}))"],cwd=HERE,env=env,capture_output=True,text=True)
    def test_portable_uses_checkout_and_active_interpreter(self):
        r=self.inspect(True);self.assertEqual(r.returncode,0,r.stderr)
        d=json.loads(r.stdout);self.assertEqual(d['root'],str(HERE.parents[3]));self.assertEqual(d['python'],sys.executable)
        self.assertEqual(d['owner'],'manual-portable');self.assertEqual(d['container'],'kidsmap-manual-portable')
        self.assertEqual(d['state'],'/tmp/kidsmap-task33-qa04-manual-portable');self.assertEqual(d['port'],8781)
    def test_legacy_paths_and_port_preserved(self):
        r=self.inspect();self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout)
        self.assertEqual(d['root'],'/root/km-manual-adminfix');self.assertEqual(d['port'],8780)
        self.assertEqual(d['container'],'kidsmap-manual-20261004')
    def test_unsafe_port_rejected(self):
        for port in ['0','80','65536','wrong']:
            with self.subTest(port=port):self.assertNotEqual(self.inspect(True,port).returncode,0)

if __name__=='__main__':unittest.main()

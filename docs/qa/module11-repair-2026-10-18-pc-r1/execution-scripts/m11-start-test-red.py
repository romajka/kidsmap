import subprocess,sys
R='/mnt/c/kidsmap';raise SystemExit(subprocess.run(['python3',R+'/.tmp/m11-tests.py','social','red','r1','test_m11_candidate.SocialMetadataTests','test_m11_candidate.ContentEditorTests']).returncode)

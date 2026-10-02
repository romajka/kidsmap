"""No Django/DB imports; meaningful negative target checks."""
import copy
import os
import socket
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from guard import install_network_guard, validate_settings

class IsolationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='kidsmap-task33-qa04-')
        self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'TASK33_QA_ROOT':self.temp.name,'TASK33_QA_SOCKET':str(self.root/'socket')});self.env.start()
        self.settings=SimpleNamespace(TESTING=True,DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','HOST':str(self.root/'socket'),'NAME':'qa_stage04','TEST':{'NAME':'test_qa_stage04'}}},CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}},EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',MEDIA_ROOT=str(self.root/'media'))
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_safe_settings_accepted(self):validate_settings(self.settings)
    def test_foreign_database_host_rejected(self):
        for host in ['localhost','127.0.0.1','/var/run/postgresql']:
            self.settings.DATABASES['default']['HOST']=host
            with self.assertRaises(RuntimeError):validate_settings(self.settings)
    def test_extra_alias_rejected(self):
        self.settings.DATABASES['legacy']=copy.deepcopy(self.settings.DATABASES['default'])
        with self.assertRaises(RuntimeError):validate_settings(self.settings)
    def test_cache_smtp_and_working_media_rejected(self):
        for name,value in [('CACHES',{'default':{'BACKEND':'django.core.cache.backends.redis.RedisCache'}}),('EMAIL_BACKEND','django.core.mail.backends.smtp.EmailBackend'),('MEDIA_ROOT','/home/ramin/kidsmap/media'),('TESTING',False),('GOOGLE_MAPS_API_KEY','synthetic-should-be-blocked')]:
            s=copy.deepcopy(self.settings);setattr(s,name,value)
            with self.assertRaises(RuntimeError):validate_settings(s)
    def test_extra_cache_alias_rejected(self):
        self.settings.CACHES['other']={'BACKEND':'django.core.cache.backends.redis.RedisCache'}
        with self.assertRaises(RuntimeError):validate_settings(self.settings)
    def test_symlink_root_rejected(self):
        link=self.root.parent/(self.root.name+'-link');link.symlink_to(self.root,target_is_directory=True)
        try:
            with patch.dict(os.environ,{'TASK33_QA_ROOT':str(link)}):
                with self.assertRaises(RuntimeError):validate_settings(self.settings)
        finally:link.unlink()
    def test_tcp_and_unrelated_unix_blocked_before_connect(self):
        originals=install_network_guard()
        try:
            for family,address in [(socket.AF_INET,('127.0.0.1',5432)),(socket.AF_INET,('example.test',443)),(socket.AF_UNIX,'/var/run/docker.sock')]:
                with socket.socket(family) as sock:
                    with self.assertRaises(RuntimeError):sock.connect(address)
                    with self.assertRaises(RuntimeError):sock.connect_ex(address)
        finally:socket.socket.connect,socket.socket.connect_ex=originals

if __name__=='__main__':unittest.main()

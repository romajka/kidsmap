"""Canonical test IDs/discovery and result capture, existing state reset preserved."""
import contextlib
import io
import json
import os
import sys
import time
import unittest
from collections import Counter
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from config.test_runner import KidsMapTestRunner

OUTPUT=Path(os.environ['TASK33_QA_OUTPUT'])

def dump(name,value):
    (OUTPUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def flatten(suite):
    for child in suite:
        if isinstance(child,unittest.TestSuite):yield from flatten(child)
        else:yield child

def all_labels():
    directory=Path(settings.BASE_DIR)/'src/catalog/testcases'
    return ['catalog.testcases.'+p.stem for p in sorted(directory.glob('*.py')) if p.stem not in {'__init__','utils'}]

class BaselineRunner(KidsMapTestRunner):
    def get_resultclass(self):
        base=super().get_resultclass()
        class Recorded(base):
            def __init__(self,*a,**kw):
                super().__init__(*a,**kw);self.identities=[];self.problem_ids=[];self.skip_ids=[];self.started=time.monotonic()
            def startTest(self,test):self.identities.append(test.id());super().startTest(test)
            def addFailure(self,test,err):self.problem_ids.append({'id':test.id(),'kind':'failure','exception':err[0].__name__});super().addFailure(test,err)
            def addError(self,test,err):self.problem_ids.append({'id':test.id(),'kind':'error','exception':err[0].__name__});super().addError(test,err)
            def addSubTest(self,test,subtest,err):
                if err is not None:self.problem_ids.append({'id':test.id(),'kind':'failure' if issubclass(err[0],test.failureException) else 'error','exception':err[0].__name__,'subtest':True})
                super().addSubTest(test,subtest,err)
            def addSkip(self,test,reason):self.skip_ids.append(test.id());super().addSkip(test,reason)
        return Recorded
    def run_suite(self,suite,**kwargs):
        result=super().run_suite(suite,**kwargs)
        dump('suite-results.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'elapsed_seconds':round(time.monotonic()-result.started,3),'problems':result.problem_ids,'skipped_ids':result.skip_ids,'executed_ids':result.identities,'problem_ids_complete':len(result.problem_ids)==len(result.failures)+len(result.errors),'status':'PASS'if result.wasSuccessful()else'BASELINE_FAILURE'})
        return result

def discovery():
    runner=KidsMapTestRunner(verbosity=0,interactive=False)
    labels=all_labels()
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        default=[test.id()for test in flatten(runner.build_suite(['catalog']))]
        explicit=[test.id()for test in flatten(runner.build_suite(labels))]
        wrapper={k:[test.id()for test in flatten(runner.build_suite(['src.catalog.testcases.'+k]))]for k in ['owner','admin','public','catalog']}
    default_ids=set(default);explicit_ids=set(explicit)
    counts=Counter('.'.join(identity.split('.')[:-2])for identity in explicit)
    result={'default_catalog_count':len(default),'default_unique_count':len(default_ids),'explicit_count':len(explicit),'explicit_unique_count':len(explicit_ids),'missing_from_full':sorted(explicit_ids-default_ids),'extra_default':sorted(default_ids-explicit_ids),'modules':dict(counts),'labels':labels,'explicit_ids':sorted(explicit_ids),'wrapper_counts':{k:len(v)for k,v in wrapper.items()},'duplicate_default_ids':len(default)-len(default_ids),'duplicate_explicit_ids':len(explicit)-len(explicit_ids)}
    assert not any('_FailedTest' in i for i in explicit), 'Test label import failure'
    dump('discovery.json',result)
    return result

def checks():
    results=[]
    for name,args in [('check',{}),('makemigrations',{'check':True,'dry_run':True,'interactive':False})]:
        start=time.monotonic()
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):call_command(name,**args)
            results.append({'command':name,'status':'PASS','exit':0,'elapsed_seconds':round(time.monotonic()-start,3)})
        except (Exception,SystemExit)as e:
            results.append({'command':name,'status':'BASELINE_FAILURE','exception':type(e).__name__,'exit':getattr(e,'code',1)})
    dump('checks.json',results)


def main(mode,selected_labels=None):
    import django
    from guard import validate_settings,install_network_guard,install_libpq_guard
    validate_settings(settings);install_network_guard();install_libpq_guard();django.setup()
    import psycopg
    from django.db import connection
    with connection.cursor()as cursor:
        cursor.execute("SELECT version(), current_database(), inet_server_addr() IS NULL, current_setting('data_directory') LIKE '/var/lib/postgresql/data%'")
        version,db,unix,tmpfs_path=cursor.fetchone()
        assert db=='qa_stage04'and unix and tmpfs_path
    dump('isolation.json',{'django_testing':settings.TESTING,'single_disposable_postgresql_alias':True,'unix_connection':unix,'network_guard':True,'libpq_guard':True,'cache':'LocMemCache','email':'locmem','media_isolated':True,'external_credentials_present':False,'postgresql':version.split(' on ')[0],'django':django.get_version(),'python':sys.version.split()[0],'psycopg':psycopg.__version__})
    found=discovery()
    if selected_labels:
        for label in selected_labels:
            if not any(identity==label or identity.startswith(label+".") for identity in found["explicit_ids"]):raise RuntimeError("Selected label not in canonical discovery")
    if mode=='discovery':return 0
    checks()
    call_command('migrate',interactive=False,verbosity=0)
    from django.db.migrations.executor import MigrationExecutor
    executor=MigrationExecutor(connection);leaves=executor.loader.graph.leaf_nodes()
    dump('migrations.json',{'leaves':[list(x)for x in sorted(leaves)],'applied_count':len(executor.loader.applied_migrations),'unapplied_count':len(executor.migration_plan(leaves)),'vendor':connection.vendor})
    from fixtures import measure
    measure()
    if mode=='probe':return 0
    labels=selected_labels or all_labels()
    runner=BaselineRunner(verbosity=1,interactive=False,parallel=1,keepdb=False)
    return runner.run_tests(labels)

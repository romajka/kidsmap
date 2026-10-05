"""Capture field error names and replay complete payload; retain original failure."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa04_contract_commands',Path('/root/kidsmap-task33/docs/task33/qa04/commands.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
dump=base.dump
original_run_suite=base.BaselineRunner.run_suite
def run_suite(runner,suite,**kwargs):
    from catalog.testcases.admin import TestAdminOwnershipModerationUX
    from catalog.models import Event
    original=TestAdminOwnershipModerationUX.test_event_admin_can_save_draft_and_continue_later
    def diagnosed(self):
        original_post=self.client.post
        captured={}
        def post(*args,**kwargs):
            response=original_post(*args,**kwargs)
            captured.update(args=args,kwargs=kwargs,response=response)
            return response
        self.client.post=post
        try:
            original(self)
        except AssertionError:
            self.client.post=original_post
            response=captured['response']
            form=response.context['adminform'].form
            names=sorted(form.errors)
            assert names==['event_format'],names
            payload=dict(captured['kwargs']['data']);payload['event_format']=Event.FORMAT_PHYSICAL
            repaired=original_post(*captured['args'],data=payload)
            errors=sorted(repaired.context['adminform'].form.errors) if repaired.status_code==200 else []
            dump('legacy-draft-diagnostic.json',{'status':'CHECKPOINT','original_error_fields':names,
                 'replayed_http_status':repaired.status_code,'replayed_error_fields':errors,
                 'replayed_occurrence_guard':repaired.status_code==200 and 'recorded occurrence change service' in str(repaired.context['adminform'].form.errors)})
            assert repaired.status_code==302
            event=Event.objects.get(pk=form.instance.pk)
            assert event.status==Event.STATUS_DRAFT and event.published_at is None
            dump('legacy-draft-diagnostic.json',{'status':'PASS_DIAGNOSTIC','original_assertion_retained':True,
                 'original_http_status':response.status_code,'original_error_fields':names,
                 'replayed_field':'event_format','complete_payload_http_status':repaired.status_code,
                 'complete_payload_saved_draft':True})
            raise
        finally:
            self.client.post=original_post
    TestAdminOwnershipModerationUX.test_event_admin_can_save_draft_and_continue_later=diagnosed
    return original_run_suite(runner,suite,**kwargs)
base.BaselineRunner.run_suite=run_suite
def main(mode,selected_labels=None):return base.main(mode,selected_labels)

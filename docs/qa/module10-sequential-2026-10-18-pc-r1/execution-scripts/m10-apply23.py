import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m10-seq-r1')
from stage_apply import *
S=O/'stages/SITE23';red=json.loads((S/'evidence/red-backend.json').read_text());assert len(red['failures'])==3 and not red['errors']
(S/'IMPLEMENTATION_PLAN.md').write_text('# SITE23 approved sequential repair\n\nFresh5method backend RED:3languages add-only Continue creates one image/file/log then403; editor,view+add,SaveExit,denied,popup controls retained. Native3language RED:single image/log each,wrong forbidden redirect. Override only SiteGalleryImageAdmin.response_add:when _continue and no object view/change permission, use existing response_post_save_add destination through post_url_continue passed to Django super. Standard localized messages/popup behavior remain, no permission grant, no duplicated persistence. Scope domain_admin/site.py +new5method test. Existing SITE20 assertions unchanged. Native3languages6widths controls and real submissions, one write/log and direct change403. Owned inactive baseline rows retained for SITE25 delete checks. No production.\n')
p='src/catalog/domain_admin/site.py';t=(R/p).read_text();marker='    def changelist_view(self, request, extra_context=None):';start=t.index('class SiteGalleryImageAdmin(');pos=t.index(marker,start);t=t[:pos]+'''    def response_add(self, request, obj, post_url_continue=None):
        if "_continue" in request.POST and not self.has_view_or_change_permission(request, obj):
            post_url_continue = self.response_post_save_add(request, obj).url
        return super().response_add(request, obj, post_url_continue)

'''+t[pos:];apply('23',{p:t.encode(),'src/catalog/testcases/test_site_qa23_gallery_add_continuation.py':(Q/'test_site23_candidate.py').read_bytes()})

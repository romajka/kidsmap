import inspect,json
from django.contrib.admin.options import ModelAdmin
methods={}
for name in ['response_add','response_post_save_add','_changeform_view']:
 method=getattr(ModelAdmin,name);lines,start=inspect.getsourcelines(method)
 methods[name]={'source':inspect.getsourcefile(method),'start_line':start,'permission_redirect_lines':[{'line':start+i,'source':s.strip()} for i,s in enumerate(lines) if any(t in s for t in ['"_continue" in request.POST','post_url_continue = obj_url','has_change_permission','has_view_or_change_permission','raise PermissionDenied','return HttpResponseRedirect'])]}
print(json.dumps({'installed_library_source_contract':methods,'classification':'Source orientation for independent pre-existing native add-only Continue403; not a server-permission bypass'},indent=2))

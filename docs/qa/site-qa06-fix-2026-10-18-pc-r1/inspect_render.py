import inspect,json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','inspect-render'];from runtime import *
from django.template.loader import get_template
from django.contrib.admin.widgets import AdminFileWidget
from django.forms.boundfield import BoundField
for name in ['admin/includes/fieldset.html','admin/widgets/clearable_file_input.html']:
 t=get_template(name);print(name,t.origin.name);print(t.template.source)
print(inspect.getsource(AdminFileWidget));print(inspect.getsource(BoundField.build_widget_attrs));print(inspect.getsource(BoundField.aria_describedby.fget))

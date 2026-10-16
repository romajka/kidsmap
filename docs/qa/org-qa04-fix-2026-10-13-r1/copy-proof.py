import json
from pathlib import Path
from django.utils.translation import gettext,override
from django.contrib import admin
from catalog.models import Organization
P=Path(__file__).resolve().parent
labels=['Названия','Организация','Организации','Состояние','Владение','Проверка данных','Владелец назначен','Владелец не назначен','Владение проверено','Владение не проверено','Связанные разделы','Текущие и предложенные данные','Сейчас','Предложено','Программы','Сотрудники','Публикация','Черновик и проверка не меняют публичные данные до одобрения.','Приглашённый редактор сможет менять организацию и общие программы после принятия приглашения.','Email сотрудника','Пригласить сотрудника','Сохранить черновик','Отправить на проверку','Одобрить заявку','Снять с публикации']
data=[]
for lang in ('ru','az','en','ru','en'):
 with override(lang):
  data.append({'lang':lang,'strings':{s:gettext(s) for s in labels},'model_plural':str(Organization._meta.verbose_name_plural),'section':str(admin.site._registry[Organization].editor_sections[0][0]),'ownership_label':str(admin.site._registry[Organization].ownership_badge.short_description)})
(P/'copy-proof.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('Current compiled catalogues and lazy labels recorded in same process')

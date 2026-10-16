import json
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import PlaceOwnershipRequest, PlacePhoto, Activity, OfferingGroup, PricingPlan, VolunteerPlaceRevision
from catalog.testcases.utils import create_ready_place
from catalog.services import publication

HERE = Path(__file__).resolve().parent
scratch = settings.MEDIA_ROOT.parent
secrets = json.loads((scratch/'credentials.json').read_text())
User = get_user_model()
staff = User.objects.create_superuser('preview_admin', 'preview-admin@example.invalid', secrets['admin_password'])
owner = User.objects.create_user('preview_owner', email='preview-owner@example.invalid', password=secrets['owner_password'])

def image(label, color):
    output = BytesIO()
    photo = Image.new('RGB', (1200,800), color)
    draw = ImageDraw.Draw(photo)
    draw.rounded_rectangle((120,100,1080,700), radius=40, fill='#f7faf9')
    draw.text((180,180), 'FICTIONAL QA PHOTO / '+label, fill='#17212c', font_size=44)
    photo.save(output, format='JPEG')
    return ContentFile(output.getvalue(), name=label.lower()+'.jpg')

place = create_ready_place(owner=owner, created_by=owner, city='baku', district='baku_yasamal',
    name_az='Yaradıcılıq və idman mərkəzi', name_ru='Центр творчества и спорта — полная карточка',
    name_en='Creative and Sports Centre',
    description_az='Uşaqlar üçün yaradıcılıq, rəsm və idman dərsləri. Yaşa uyğun qruplar və müntəzəm cədvəl. '*6,
    description_ru='Пространство для творчества и спорта. Здесь проходят занятия для детей, пробные уроки и семейные мастер-классы. Все тексты доступны для проверки без обрезания. '*7,
    description_en='A creative and sports space for children. Trial sessions, regular classes and family workshops. '*6,
    phone2='+994502223344', phone3='+994503334455', instagram='kidsmap_qa_fixture', website='https://example.invalid',
    extra_conditions_ru='Пробное занятие по записи. Материалы включены в стоимость.',
    extra_conditions_az='Sınaq dərsi qeydiyyatla. Materiallar qiymətə daxildir.',
    extra_conditions_en='Trial sessions by appointment. Materials are included.',
    additional_info_ru='Пожалуйста, приходите за 10 минут до начала занятия.',
    additional_info_az='Dərsdən 10 dəqiqə əvvəl gəlməyiniz xahiş olunur.',
    additional_info_en='Please arrive 10 minutes before the session.',
    schedule_note_ru='Во время каникул расписание уточняется.',
    status='pending', is_active=False)
place.photo.save('main.jpg', image('MAIN','#cde7c5'), save=True)
place.cover_photo.save('cover.jpg', image('COVER','#d5e5f1'), save=True)
for index, color in enumerate(['#ead9ba','#b8e1d3','#e3dcf1']):
    photo = PlacePhoto(place=place, caption=f'Фикстура фото {index+1} — зал для занятий', order=index)
    photo.image.save(f'gallery-{index}.jpg', image(f'GALLERY{index}',color), save=True)
activity=Activity.objects.create(place=place, category=place.category, subcategory=place.subcategory,
    name_ru='Рисование и творческое мышление',name_az='Rəsm və yaradıcı düşüncə',name_en='Drawing and creative thinking',
    description_ru='Занятия рисунком, цветом и композицией. Полное описание направления.',
    description_az='Rəsm, rəng və kompozisiya dərsləri.', description_en='Drawing, color and composition classes.',status='draft')
group=OfferingGroup.objects.create(activity=activity, name_ru='Группа 6–10 лет',name_az='6–10 yaş qrupu',name_en='Ages 6–10',
    age_from=6,age_to=10,lesson_format='group',language='AZ / RU',schedule_text='Вт и Чт, 16:00–18:00',
    teachers_text='Преподаватель фикстуры',conditions_ru='До 8 детей. Все материалы предоставляются.')
PricingPlan.objects.create(offering_group=group,product_type='lesson',price='35',title_ru='Разовое занятие',title_az='Bir dərs',title_en='Single session',conditions_ru='Материалы включены',conditions_en='Materials included')
PricingPlan.objects.create(place=place,product_type='lesson',price='9',title_ru='Неактивный тариф',title_az='Aktiv olmayan tarif',title_en='Disabled tariff',is_active=False)
base=publication.snapshot(place,'place')
revision=VolunteerPlaceRevision.objects.create(place=place,author=owner,base_snapshot=base,
    dependencies=publication.dependencies(place,'place'),changed_fields=['description_ru'],schema_version=publication.SCHEMA_VERSION,
    base_content_version=place.content_version,payload={'description_ru':place.description_ru+'\nОтправленное уточнение: семейные занятия по субботам.'},status='pending',version=1)
item=PlaceOwnershipRequest.objects.create(place=place,applicant=owner,request_kind='PUBLICATION',
    note='Прошу проверить фотографии, расписание и тарифы. Все данные сохранены.')
fixtures={'place':place.pk,'request':item.pk,'admin_username':staff.username,'revision':revision.pk}
(scratch/'fixtures.json').write_text(json.dumps(fixtures))
(HERE/'fixtures.json').write_text(json.dumps(fixtures))
print('Own fictional preview fixtures created.')

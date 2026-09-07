"""Admin presentation for the existing restricted proposal form; no write policy."""
from dataclasses import replace
from catalog.services.permanent_place_rules import copy as t
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.volunteer_forms import CONTENT_FIELDS


def editor_context(form):
    readiness = evaluate_form_readiness(form, form.instance)
    issues = [replace(issue, field='district') if issue.field == 'region' else issue for issue in readiness.issues]
    definitions = [
        ('basics', t('Основное', 'Əsas məlumat', 'Basics'), 'tune', t('Название, описание и рубрика карточки.', 'Kartın adı, təsviri və kateqoriyası.', 'Name, description and category.')),
        ('pricing', t('Цена и возраст', 'Qiymət və yaş', 'Price and age'), 'payments', t('Возраст детей, стоимость и условия занятий.', 'Uşaqların yaşı, qiymət və məşğələ şərtləri.', 'Age range, pricing and lesson details.')),
        ('location', t('Локация', 'Məkan və əlaqə', 'Location'), 'place', t('Адрес, точка на карте, контакты и расписание.', 'Ünvan, xəritədə nöqtə, əlaqə və cədvəl.', 'Address, map point, contacts and opening hours.')),
        ('media', t('Фото', 'Şəkillər', 'Photos'), 'image', t('Главное фото и обложка. Загружайте фотографии самого места.', 'Əsas şəkil və örtük. Məkanın öz şəkillərini yükləyin.', 'Main photo and cover. Upload photos of the place itself.')),
        ('verification', t('Проверка', 'Yoxlama', 'Review'), 'check_circle', t('Проверьте данные перед отправкой администратору.', 'Administratora göndərməzdən əvvəl məlumatları yoxlayın.', 'Check the details before sending to the administrator.')),
    ]
    pricing_names = {'age_from', 'age_to', 'age_open_ended', 'offers_adult_classes', 'lesson_duration_minutes', 'lesson_format', 'lessons_per_week', 'lessons_per_month'}
    pricing_names.update(name for name in CONTENT_FIELDS if name.startswith('custom_price_badge_'))
    basics = {'name_az','name_ru','name_en','description_az','description_ru','description_en','category','subcategory'}
    special = basics | pricing_names | {'photo','cover_photo','lat','lng','price_mode','schedule','schedule_mode','schedule_note_az','schedule_note_ru','schedule_note_en'}
    sections = []
    for number, (key, title, icon, hint) in enumerate(definitions, 1):
        items = readiness.items if key == 'verification' else [item for item in readiness.items if item.requirement.section == key]
        done = sum(item.is_complete for item in items)
        fields = [form[name] for name in CONTENT_FIELDS if (key == 'pricing' and name in pricing_names) or (key == 'location' and name not in special) or (key == 'media' and name in {'photo','cover_photo'}) or (key == 'basics' and name in basics)]
        invalid = any(field.errors for field in fields)
        state = 'error' if invalid else 'done' if items and done == len(items) else 'partial' if done else 'empty'
        sections.append(dict(id=key, title=title, icon=icon, description=hint, step=f'{number:02}', fields=[field for field in fields if not field.name.startswith(('custom_price_badge_', 'extra_conditions_', 'additional_info_'))],
            optional=[field for field in fields if field.name.startswith(('custom_price_badge_', 'extra_conditions_', 'additional_info_'))],
            state=dict(state=state, icon={'error':'error','done':'check_circle','partial':'radio_button_checked','empty':'radio_button_unchecked'}[state], label=f'{done} / {len(items)}' if items else '')))
    return dict(volunteer_sections=sections, editor_readiness=readiness, editor_issues=issues,
        km_place_required_fields={'district' if item.requirement.field == 'region' else item.requirement.field for item in readiness.items},
        km_place_language_tabs=[dict(code=lang, label=lang.upper(), optional=lang != 'az', name_field=form[f'name_{lang}'], description_field=form[f'description_{lang}']) for lang in ('az','ru','en')],
        editor_copy=dict(
            instruction=t('Инструкция', 'Təlimat', 'Instructions'),
            instruction_title=t('Как заполнить карточку места', 'Məkan kartını necə doldurmalı', 'How to complete a place card'),
            steps=[t('Укажите точное название и категорию. В описании расскажите о занятиях и особенностях места; не добавляйте непроверенные обещания.', 'Dəqiq ad və kateqoriya seçin. Təsvirə məşğələlər və məkanın xüsusiyyətlərini yazın; yoxlanılmamış vədlər əlavə etməyin.', 'Use the exact name and category. Describe the activities and the place; avoid unverified claims.'),
                   t('Уточните возраст, стоимость и что входит в каждый тариф. Если цена неизвестна, выберите «По запросу».', 'Yaşı, qiyməti və hər tarifə daxil olanları dəqiqləşdirin. Qiymət məlum deyilsə, «Sorğu ilə» seçin.', 'Specify ages, prices and what each plan includes. Choose On request if the price is unknown.'),
                   t('Проверьте адрес, вход на карте, рабочий телефон и расписание. Не ставьте случайную точку ради готовности.', 'Ünvanı, xəritədə girişi, işlək telefonu və cədvəli yoxlayın. Hazırlıq üçün təsadüfi nöqtə seçməyin.', 'Check the address, entrance on the map, working phone and schedule. Do not choose a random map point to complete the checklist.'),
                   t('Загрузите главное фото и при необходимости обложку. После ошибки формы новые файлы нужно выбрать повторно.', 'Əsas şəkli və lazım olsa örtüyü yükləyin. Forma xətasından sonra yeni faylları yenidən seçin.', 'Upload a main photo and an optional cover. Reselect new files after a form validation error.'),
                   t('Сохраните черновик, чтобы продолжить позже. В разделе «Проверка» видны недостающие пункты. Готовность обновляется после сохранения.', 'Sonra davam etmək üçün qaralamanı saxlayın. Çatışmayan bəndlər «Yoxlama» bölməsindədir. Hazırlıq saxladıqdan sonra yenilənir.', 'Save a draft to continue later. Review lists missing items. Readiness updates after saving.'),
                   t('Отправьте карточку на проверку. Администратор опубликует её или оставит замечания. Правки опубликованного места также проходят проверку.', 'Kartı yoxlamaya göndərin. Administrator onu yayımlayacaq və ya qeyd yazacaq. Yayımlanmış məkanın dəyişiklikləri də yoxlanılır.', 'Submit the card for review. The administrator publishes it or leaves feedback. Changes to published places also require review.')],
            saved_readiness=t('Готовность после последнего сохранения', 'Son saxlamadan sonra hazırlıq', 'Readiness after the last save'),
            new_readiness=t('Готовность карточки', 'Kartın hazırlığı', 'Card readiness'),
            update_hint=t('После изменения полей сохраните черновик — готовность будет пересчитана.', 'Sahələri dəyişdikdən sonra qaralamanı saxlayın — hazırlıq yenidən hesablanacaq.', 'Save a draft after editing to recalculate readiness.'),
            dirty=t('Есть несохранённые изменения', 'Saxlanmamış dəyişikliklər var', 'Unsaved changes'),
            initial=t('Заполните данные и сохраните черновик', 'Məlumatları doldurub qaralamanı saxlayın', 'Complete the details and save a draft'),
            translations=t('Добавьте переводы, если они известны. Не выдумывайте данные.', 'Tərcümələr məlumdursa əlavə edin. Məlumat uydurmayın.', 'Add translations if available. Do not invent details.'),
        ))

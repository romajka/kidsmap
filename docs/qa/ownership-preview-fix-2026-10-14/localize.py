"""Append only this feature's new messages; preserve pre-existing PO edits."""
import json
import polib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRANSLATIONS = {
 'Формат занятий': ('Dərs formatı', 'Class format'),
 'Не указано': ('Qeyd edilməyib', 'Not specified'),
 'Фото загружается': ('Şəkil yüklənir', 'Loading photo'),
 'Не удалось загрузить фото': ('Şəkli yükləmək mümkün olmadı', 'Could not load the photo'),
 'Без верхней границы возраста': ('Yuxarı yaş həddi yoxdur', 'No upper age limit'),
 'Редактировать карточку': ('Kartı redaktə et', 'Edit card'),
 'Город': ('Şəhər', 'City'),
 'Тип карточки': ('Kartın növü', 'Card type'),
 'Состояние работы': ('Fəaliyyət vəziyyəti', 'Operating status'),
 'Язык занятий': ('Dərs dili', 'Class language'),
 'Расписание группы': ('Qrup cədvəli', 'Group schedule'),
 'Преподаватели': ('Müəllimlər', 'Teachers'),
 'Программа': ('Proqram', 'Program'),
 'Безлимит': ('Limitsiz', 'Unlimited'),
 'Валюта': ('Valyuta', 'Currency'),
 'Видна на сайте': ('Saytda görünür', 'Visible on the website'),
 'Все условия тарифа': ('Tarifin bütün şərtləri', 'All tariff details'),
 'Все языки': ('Bütün dillər', 'All languages'),
 'Готовность к публикации': ('Dərcə hazırlıq', 'Publication readiness'),
 'Группы не добавлены': ('Qruplar əlavə edilməyib', 'No groups added'),
 'Действует до': ('Etibarlılığın sonu', 'Valid until'),
 'Действует с': ('Etibarlılığın başlanğıcı', 'Valid from'),
 'Для кого': ('Kimlər üçün', 'Audience'),
 'Дни посещения': ('Ziyarət günləri', 'Attendance days'),
 'Дополнение к программе': ('Proqrama əlavə', 'Program supplement'),
 'Единица количества': ('Say vahidi', 'Quantity unit'),
 'Ещё не опубликована': ('Hələ dərc edilməyib', 'Not yet published'),
 'Заявка устарела': ('Müraciət köhnəlib', 'This request is outdated'),
 'Источник цены': ('Qiymət mənbəyi', 'Price source'),
 'К списку заявок': ('Müraciətlər siyahısına', 'Back to requests'),
 'Карточка или отправленные изменения уже изменились. Перед одобрением нужна новая заявка.': ('Kart və ya göndərilmiş dəyişikliklər yenilənib. Təsdiqdən əvvəl yeni müraciət lazımdır.', 'The card or submitted changes have been updated. A new request is needed before approval.'),
 'Карточка удалена': ('Kart silinib', 'Card deleted'),
 'Количество занятий': ('Dərslərin sayı', 'Number of sessions'),
 'Количество периодов': ('Dövrlərin sayı', 'Number of billing periods'),
 'Количество периодов действия': ('Etibarlılıq dövrlərinin sayı', 'Number of validity periods'),
 'Количество платежей': ('Ödənişlərin sayı', 'Number of payments'),
 'Максимум участников': ('Maksimum iştirakçı sayı', 'Maximum participants'),
 'Минимум участников': ('Minimum iştirakçı sayı', 'Minimum participants'),
 'Модель оплаты': ('Ödəniş modeli', 'Billing model'),
 'Надпись цены на карточке': ('Kartda qiymət yazısı', 'Card price label'),
 'Название группы': ('Qrupun adı', 'Group name'),
 'Название направления': ('İstiqamətin adı', 'Activity name'),
 'Название тарифа': ('Tarifin adı', 'Tariff name'),
 'Назначение платежа': ('Ödənişin təyinatı', 'Payment purpose'),
 'Направление': ('İstiqamət', 'Activity'),
 'Направления и группы': ('İstiqamətlər və qruplar', 'Activities and groups'),
 'Направления не добавлены': ('İstiqamətlər əlavə edilməyib', 'No activities added'),
 'Нет комментария': ('Şərh yoxdur', 'No comment'),
 'О карточке': ('Kart haqqında', 'About the card'),
 'Общие ранее сохранённые условия': ('Əvvəllər saxlanılmış ümumi şərtlər', 'Previously saved general conditions'),
 'Обязательные данные заполнены': ('Tələb olunan məlumatlar doldurulub', 'Required information is complete'),
 'Обязательный платёж': ('Məcburi ödəniş', 'Required payment'),
 'Одобрение публикует карточку с отправленными изменениями.': ('Təsdiq kartı göndərilmiş dəyişikliklərlə birlikdə dərc edir.', 'Approval publishes the card with the submitted changes.'),
 'Описание направления': ('İstiqamətin təsviri', 'Activity description'),
 'Отклонить заявку': ('Müraciəti rədd et', 'Reject request'),
 'Отправлено на проверку': ('Yoxlamaya göndərilib', 'Submitted for review'),
 'Перейти к проверке': ('Yoxlamaya keç', 'Review submitted changes'),
 'Период действия': ('Etibarlılıq dövrü', 'Validity period'),
 'Период оплаты': ('Ödəniş dövrü', 'Billing interval'),
 'Подтвердить владение': ('Sahibliyi təsdiqlə', 'Confirm ownership'),
 'Подтверждение владения передаёт управление карточкой. Оно не публикует её.': ('Sahibliyin təsdiqi kartın idarəsini ötürür. Kartı dərc etmir.', 'Confirming ownership transfers management of the card. It does not publish it.'),
 'Показана полная карточка с изменениями, отправленными на проверку.': ('Yoxlamaya göndərilmiş dəyişikliklərlə birlikdə tam kart göstərilir.', 'The full card is shown with the changes submitted for review.'),
 'Показана полная сохранённая карточка. Просмотр не меняет её статус.': ('Tam saxlanılmış kart göstərilir. Baxış onun statusunu dəyişmir.', 'The complete saved card is shown. Viewing it does not change its status.'),
 'Примечание к расписанию': ('Cədvələ qeyd', 'Schedule note'),
 'Пробное занятие': ('Sınaq dərsi', 'Trial session'),
 'Проверить карточку': ('Kartı yoxla', 'Review card'),
 'Проверка заявки на владение': ('Sahiblik müraciətinin yoxlanması', 'Ownership request review'),
 'Проверка перед публикацией': ('Dərcdən əvvəl yoxlama', 'Review before publication'),
 'Развернуть все условия': ('Bütün şərtləri aç', 'Expand all details'),
 'Ранее сохранённые цены': ('Əvvəllər saxlanılmış qiymətlər', 'Previously saved prices'),
 'Расписание по дням не добавлено': ('Günlər üzrə cədvəl əlavə edilməyib', 'No weekly schedule added'),
 'Тариф': ('Tarif', 'Tariff'),
 'Тариф активен': ('Tarif aktivdir', 'Tariff enabled'),
 'Текст расписания': ('Cədvəl mətni', 'Schedule text'),
 'Текущее состояние': ('Cari vəziyyət', 'Current saved card'),
 'Телефон организации': ('Təşkilatın telefonu', 'Organization phone'),
 'Тип заявки': ('Müraciətin növü', 'Request type'),
 'Тип тарифа': ('Tarifin növü', 'Tariff type'),
 'Тип цены': ('Qiymətin növü', 'Price type'),
 'Увеличить фото': ('Şəkli böyüt', 'Enlarge photo'),
 'Условия': ('Şərtlər', 'Conditions'),
 'Условия группы': ('Qrupun şərtləri', 'Group conditions'),
 'Условия и дополнительная информация': ('Şərtlər və əlavə məlumat', 'Conditions and additional information'),
 'Условия тарифа': ('Tarifin şərtləri', 'Tariff conditions'),
 'Фото недоступно': ('Şəkil əlçatan deyil', 'Photo unavailable'),
 'Фотографии не добавлены': ('Şəkillər əlavə edilməyib', 'No photos added'),
 'Цена проверена': ('Qiymət yoxlanılıb', 'Price verified'),
 'Цены и тарифы': ('Qiymətlər və tariflər', 'Prices and tariffs'),
 'Язык содержимого': ('Məzmun dili', 'Content language'),
}
for lang, index in [('az', 0), ('en', 1), ('ru', None)]:
    path = ROOT / 'locale' / lang / 'LC_MESSAGES/django.po'
    source = path.read_text()
    catalogue = polib.pofile(path)
    additions = []
    for msgid, values in TRANSLATIONS.items():
        encoded = json.dumps(msgid, ensure_ascii=False)
        translated = msgid if index is None else values[index]
        active = catalogue.find(msgid, msgctxt=None)
        if active is not None and active.fuzzy:
            paragraphs = source.split('\n\n')
            for position, paragraph in enumerate(paragraphs):
                if '\nmsgid '+encoded+'\n' not in '\n'+paragraph+'\n':
                    continue
                lines = paragraph.splitlines(); repaired = []; continuation = False
                for line in lines:
                    if line.startswith('#,'):
                        flags=[flag.strip() for flag in line[2:].split(',') if flag.strip()!='fuzzy']
                        if flags: repaired.append('#, '+', '.join(flags))
                    elif line.startswith('msgstr '):
                        repaired.append('msgstr '+json.dumps(translated,ensure_ascii=False));continuation=True
                    elif continuation and line.startswith('"'):
                        continue
                    else:
                        continuation=False;repaired.append(line)
                paragraphs[position]='\n'.join(repaired)
                break
            source='\n\n'.join(paragraphs)
            continue
        if active is not None:
            continue
        obsolete = catalogue.find(msgid, include_obsolete_entries=True, msgctxt=None)
        if obsolete is not None and obsolete.obsolete:
            # GNU msgfmt rejects an active duplicate of an obsolete key.
            # Promote only this feature's exact entry, preserving other text.
            paragraphs = source.split('\n\n')
            for position, paragraph in enumerate(paragraphs):
                if '#~ msgid ' + encoded in paragraph:
                    paragraphs[position] = '\n'.join(line[3:] if line.startswith('#~ ') else line for line in paragraph.splitlines())
                    break
            source = '\n\n'.join(paragraphs)
            # Existing obsolete translations remain intact on promotion.
            continue
        additions.append('#: catalog/services/admin_place_preview.py admin/catalog/placeownershiprequest/preview.html\n'
            + 'msgid ' + encoded + '\nmsgstr ' + json.dumps(translated, ensure_ascii=False) + '\n')
    path.write_text((source.rstrip() + ('\n\n' + '\n'.join(additions) if additions else '')).rstrip() + '\n')
    print(lang, 'new messages:', len(additions))

# A pre-existing Russian translation displayed "Metro" for a false boolean.
path = ROOT / 'locale/ru/LC_MESSAGES/django.po'
source = path.read_text()
source = source.replace('msgid "Нет"\nmsgstr "Метро"', 'msgid "Нет"\nmsgstr "Нет"')
path.write_text(source)

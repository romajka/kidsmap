"""Copy curated fresh synthetic screenshots verbatim, with source hashes/context."""
import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/final-audit/screenshots';OUT.mkdir(exist_ok=True)
paths={family:Path(path) for family,path in zip(('r1','specialist','event','targeted'),sys.argv[1:])}
selection=[
('r1','public-catalog-390.png','Каталог для родителя','Публичные фильтры и результаты',390),
('r1','public-map-open-390.png','Карта каталога','Реальная локальная карта: известные точки и записи без координат',390),
('r1','standalone_owner-ru-390.png','Форма владельца','Мобильное редактирование самостоятельного места',390),
('r1','standalone_owner-ru-1440.png','Форма владельца — большой экран','Непрерывные секции редактирования',1440),
('r1','network_owner-ru-390.png','Организация владельца','Доступные филиалы и горизонтальная навигация',390),
('r1','volunteer-ru-390.png','Кабинет волонтёра','Очередь предложенных изменений',390),
('r1','moderator-ru-1440.png','Отзывы для модератора','Одобренный отзыв и отдельный кандидат',1440),
('specialist','public-ru-390.png','Публичный специалист','Текущее сотрудничество, история и публичный сертификат',390),
('specialist','public-ru-1440.png','Специалист — большой экран','Онлайн-формат и фактические сведения',1440),
('specialist','claims-ru-390.png','Подтверждение личности','Личный процесс заявления прав',390),
('specialist','certificates-ru-390.png','Документы специалиста','Публичный сертификат и приватные документы в кабинете',390),
('specialist','index-ru-1440.png','Кабинет специалиста','Личная рабочая область',1440),
('event','calendar-390.png','Мобильный календарь','Выбор дня и список событий',390),
('event','calendar-1440.png','Календарь — большой экран','Полный месяц и отдельный выбранный день',1440),
('event','online-390.png','Онлайн-событие','Организатор, даты по Баку, отсутствие выдуманной площадки',390),
('event','cancelled-390.png','Отменённое событие','Публичная карточка сохраняет честное состояние',390),
('event','rescheduled-1440.png','Перенос события','Новое время и история изменений',1440),
('event','admin_add-390.png','Добавление события администратором','Мобильная форма с языковыми вкладками',390),
('event','owner-precision-after-edit.png','Успешное сохранение владельцем','Реальный POST; точные секунды сохранены в БД',1440),
('event','admin-precision-after-edit.png','Успешное сохранение администратором','Реальный POST опубликованного события, без потери точности',1440),
('targeted','program-ru-390.png','Общая программа','Влияние общей программы на конкретный филиал',390),
('targeted','program-ru-1280.png','Программа — большой экран','Переводы, категория и подтверждение затронутых филиалов',1280),
('targeted','activity-ru-390.png','Публичное занятие','Общая программа плюс местное расписание, группа и цена',390),
('targeted','organization-ru-1280.png','Публичная организация','Филиалы, общие программы и контакты',1280),
('targeted','program-pending-after-edit.png','Программа после отправки изменения','Реальный native POST владельца; изменение ожидает проверки, опубликованный текст прежний',1280),
('targeted','catalog-count-ru-320.png','Счётчик результатов на узком экране','Фактический текст и clipping проверены отдельной геометрией DOM',320),
('targeted','catalog-count-ru-390.png','Счётчик результатов на мобильном экране','Сравнение со320px без изменения приложения',390)]
index=[]
for n,(family,filename,title,context,width) in enumerate(selection,1):
    original=paths[family]/filename;assert original.is_file(),original
    source=json.loads((paths[family]/'source.json').read_text(encoding='utf-8'))
    name=f'{n:02}-{family}-{filename}'
    shutil.copyfile(original,OUT/name)
    digest=hashlib.sha256(original.read_bytes()).hexdigest()
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
    index.append({'filename':name,'path':'screenshots/'+name,'title':title,'caption':context,'context':context,'family':family,'lang':'ru','language':'ru','width':width,
        'sha256':digest,'source_artifact':source['artifact'],'raw_evidence':str(original),'synthetic_only':True,
        'capture':'Actual Chromium PNG copied verbatim; full-page images can require zoom'})
(OUT/'index.json').write_text(json.dumps({'count':len(index),'screenshots':index},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'screenshots':len(index),'verbatim_hashes':'PASS'}))

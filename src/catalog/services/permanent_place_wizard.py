"""Presentation for the permanent-place form; shared by create and edit."""
from catalog.services.permanent_place_rules import copy as t


def localize_fields(form):
    labels = {
        'category': ('Категория', 'Kateqoriya', 'Category'),
        'subcategory': ('Подкатегория', 'Alt kateqoriya', 'Subcategory'),
        'age_from': ('Возраст от', 'Minimum yaş', 'Age from'),
        'age_to': ('Возраст до', 'Maksimum yaş', 'Age to'),
        'offers_adult_classes': ('Кто может заниматься?', 'Kim məşğul ola bilər?', 'Who can attend?'),
        'region': ('Город / регион', 'Şəhər / region', 'City / region'),
        'district': ('Район Баку', 'Bakı rayonu', 'Baku district'),
        'metro': ('Метро', 'Metro', 'Metro'),
        'address': ('Адрес', 'Ünvan', 'Address'),
        'phone1': ('Основной телефон', 'Əsas telefon', 'Main phone'),
        'phone2': ('Дополнительный телефон', 'Əlavə telefon', 'Additional phone'),
        'phone3': ('Ещё один телефон', 'Digər telefon', 'Another phone'),
        'website': ('Сайт', 'Veb-sayt', 'Website'),
        'lesson_duration_minutes': ('Длительность занятия, минут', 'Məşğələnin müddəti, dəqiqə', 'Lesson duration, minutes'),
        'lessons_per_week': ('Занятий в неделю', 'Həftədə məşğələ', 'Lessons per week'),
        'lessons_per_month': ('Занятий в месяц', 'Ayda məşğələ', 'Lessons per month'),
        'photo': ('Главное фото', 'Əsas şəkil', 'Main photo'),
        'gallery_images': ('Дополнительные фото (до 10)', 'Əlavə şəkillər (10-dək)', 'Gallery photos (up to 10)'),
        'moderation_note': ('Комментарий модератору', 'Moderator üçün şərh', 'Note to moderator'),
        'schedule': ('Расписание текстом', 'Mətn cədvəli', 'Text schedule'),
        'extra_conditions': ('Ранее добавленные условия', 'Əvvəl əlavə edilmiş şərtlər', 'Previously added conditions'),
        'additional_info': ('Ранее добавленная информация', 'Əvvəl əlavə edilmiş məlumat', 'Previously added information'),
    }
    for prefix, translations in {
        'name': ('Название', 'Ad', 'Name'),
        'description': ('Описание', 'Təsvir', 'Description'),
        'extra_conditions': ('Дополнительные условия', 'Əlavə şərtlər', 'Additional conditions'),
        'additional_info': ('Дополнительная информация', 'Əlavə məlumat', 'Additional information'),
    }.items():
        for lang in ('az','ru','en'):
            labels[f'{prefix}_{lang}'] = tuple(f'{label} ({lang.upper()})' for label in translations)
    for name, translations in labels.items():
        if name in form.fields:
            form.fields[name].label = t(*translations)
    form.fields['offers_adult_classes'].choices = (('0',t('Только дети','Yalnız uşaqlar','Children only')),('1',t('Дети и взрослые','Uşaqlar və böyüklər','Children and adults')))
    form.fields['lesson_format'].choices = (('', '—'),('group',t('Групповые','Qrup','Group')),('individual',t('Индивидуальные','Fərdi','Individual')))
    hints = {
        'region': ('Выберите город или регион.', 'Şəhər və ya region seçin.', 'Choose a city or region.'),
        'district': ('Обязательно для Баку.', 'Bakı üçün məcburidir.', 'Required for Baku.'),
        'metro': ('Необязательно: ближайшая станция.', 'İstəyə görə: yaxın stansiya.', 'Optional: nearest station.'),
        'address': ('Улица, дом, ориентир.', 'Küçə, bina, istiqamət.', 'Street, building, landmark.'),
        'offers_adult_classes': ('Возраст выше относится к детским группам.', 'Yuxarıdakı yaş uşaqların qruplarına aiddir.', 'The age range above describes children’s groups.'),
        'moderation_note': ('До 500 символов; посетители не увидят этот комментарий.', '500 simvoladək; ziyarətçilər bu şərhi görməyəcək.', 'Up to 500 characters; visitors will not see this note.'),
    }
    for name, field in form.fields.items():
        if name in hints:
            field.help_text = t(*hints[name])
        elif name not in ('name_az','description_az','photo','gallery_images'):
            field.help_text = ''


def ui_copy():
    return dict(
        title=t('Постоянное место', 'Daimi məkan', 'Permanent place'),
        intro=t('Расскажите о месте. После проверки оно появится в каталоге.', 'Məkan haqqında məlumat verin. Yoxlamadan sonra kataloqda görünəcək.', 'Tell us about the place. It will appear in the catalog after review.'),
        back=t('Назад', 'Geri', 'Back'), next=t('Дальше', 'Davam et', 'Continue'),
        draft=t('Сохранить черновик', 'Qaralamanı saxla', 'Save draft'),
        submit=t('Отправить на модерацию', 'Moderasiyaya göndər', 'Send for review'),
        places=t('Мои места', 'Məkanlarım', 'My places'),
        progress=t('Ваше место — шаг за шагом', 'Məkanınız — addım-addım', 'Your place, step by step'),
        step=t('Шаг', 'Addım', 'Step'),
        of=t('из', '/', 'of'),
        photo_choose=t('Выберите фотографию', 'Şəkil seçin', 'Choose a photo'),
        photo_drop=t('Перетащите сюда или нажмите для выбора', 'Buraya sürükləyin və ya seçmək üçün basın', 'Drop here or click to choose'),
        saved_later=t('Можно продолжить позже: сохраните черновик.', 'Daha sonra davam etmək üçün qaralamanı saxlayın.', 'Save a draft to continue later.'),
        optional=t('Дополнительно', 'Əlavə məlumat', 'Additional details'),
        required=t('Обязательно для отправки', 'Göndərmək üçün məcburidir', 'Required for submission'),
        required_badge=t('Обязательно', 'Məcburi', 'Required'),
        optional_badge=t('Необязательно', 'Məcburi deyil', 'Optional'),
        one_name=t('На одном языке', 'Bir dildə', 'In one language'),
        name_requirement=t('Название на азербайджанском', 'Azərbaycan dilində ad', 'Name in Azerbaijani'),
        point_requirement=t('Точка на карте', 'Xəritədə nöqtə', 'Map point'),
        price_requirement=t('Основной тариф', 'Əsas tarif', 'Primary plan'),
        schedule_requirement=t('Дни и часы или текст расписания', 'Gün və saatlar və ya mətn cədvəli', 'Opening hours or text schedule'),
        fields_ready=t('Готово', 'Hazırdır', 'Ready'),
        fields_remaining=t('Осталось', 'Qalıb', 'Remaining'),
        draft_hint=t('Для черновика можно заполнить позже. Дополнительные поля отмечены отдельно.', 'Qaralama üçün sonra doldura bilərsiniz. Əlavə sahələr ayrıca işarələnib.', 'You can complete these later in a draft. Optional fields are marked separately.'),
        translations=t('Переводы RU / EN', 'RU / EN tərcümələri', 'RU / EN translations'),
        range=t('Диапазон возраста', 'Yaş aralığı', 'Age range'),
        open_age=t('От указанного возраста', 'Göstərilən yaşdan', 'From this age'),
        all_ages=t('Все возрасты · 0+', 'Bütün yaşlar · 0+', 'All ages · 0+'),
        add_plan=t('Добавить тариф', 'Tarif əlavə et', 'Add a plan'),
        plans_hint=t('До 12 тарифов. Доплаты и депозит указываются отдельно от основной цены.', '12-dək tarif. Əlavə ödəniş və depozit əsas qiymətdən ayrıdır.', 'Up to 12 plans. Add-ons and deposits are separate from the primary price.'),
        manual=t('Ввести координаты вручную', 'Koordinatları əl ilə daxil et', 'Enter coordinates manually'),
        map_hint=t('Выберите точку на карте или введите координаты. Это обязательно для отправки.', 'Xəritədə nöqtə seçin və ya koordinatları daxil edin. Göndərmək üçün vacibdir.', 'Choose a map point or enter coordinates. This is required for submission.'),
        map_changed=t('Адрес изменился. Проверьте точку на карте.', 'Ünvan dəyişdi. Xəritədə nöqtəni yoxlayın.', 'The address changed. Check the map point.'),
        map_confirm=t('Точка верна', 'Nöqtə düzgündür', 'Point is correct'),
        map_unavailable=t('Карта недоступна. Можно ввести координаты вручную.', 'Xəritə əlçatan deyil. Koordinatları əl ilə daxil edə bilərsiniz.', 'Map unavailable. You can enter coordinates manually.'),
        remove=t('Удалить при сохранении', 'Saxlayarkən sil', 'Remove when saving'),
        restore=t('Отменить удаление', 'Silməni ləğv et', 'Undo removal'),
        photos_hint=t('Главное фото и до 10 дополнительных. Новые фото можно добавлять частями.', 'Əsas şəkil və 10-dək əlavə şəkil. Şəkilləri hissə-hissə əlavə edə bilərsiniz.', 'One main photo and up to 10 gallery photos. Add photos in multiple batches.'),
        preview=t('Так увидят ваше место', 'Məkanınız belə görünəcək', 'Your place preview'),
        check=t('Проверьте перед отправкой', 'Göndərməzdən əvvəl yoxlayın', 'Review before submitting'),
        empty=t('Не заполнено', 'Doldurulmayıb', 'Not filled in'),
        ready=t('Можно отправлять на модерацию', 'Moderasiyaya göndərmək olar', 'Ready to send for review'),
        missing=t('Проверьте обязательные поля', 'Məcburi sahələri yoxlayın', 'Check required fields'),
        invalid=t('Проверьте значение', 'Dəyəri yoxlayın', 'Check this value'),
        browser_saved=t('Текст и тарифы сохранены в этом браузере. Для сохранения фото нажмите «Сохранить черновик».', 'Mətn və tariflər bu brauzerdə saxlanılıb. Şəkillər üçün «Qaralamanı saxla» düyməsini basın.', 'Text and plans saved in this browser. Use Save draft to save photos.'),
        restored=t('Черновик восстановлен. Незагруженные фотографии выберите заново.', 'Qaralama bərpa edildi. Yüklənməmiş şəkilləri yenidən seçin.', 'Draft restored. Select any unuploaded photos again.'),
        storage_error=t('Браузер не смог сохранить черновик. Сохраните его кнопкой ниже.', 'Brauzer qaralamanı saxlaya bilmədi. Aşağıdakı düymə ilə saxlayın.', 'Browser draft could not be saved. Use the Save draft button.'),
        offline=t('Нет соединения. Текст остаётся в этом браузере; отправка будет доступна после подключения.', 'Bağlantı yoxdur. Mətn bu brauzerdə qalır; göndərmək üçün internetə qoşulun.', 'Offline. Text stays in this browser; reconnect to submit.'),
        unsaved=t('Есть несохранённые изменения.', 'Saxlanmamış dəyişikliklər var.', 'You have unsaved changes.'),
        request=t('По запросу', 'Sorğu ilə', 'On request'), free=t('Бесплатно', 'Pulsuz', 'Free'),
        from_price=t('От', 'Başlayır', 'From'),
        pending=t('Карточка появится после одобрения модератором.', 'Kart moderator təsdiqindən sonra görünəcək.', 'The card becomes public after moderator approval.'),
        deletion=t('Удалить место', 'Məkanı sil', 'Delete place'),
        delete_confirm=t('Удалить карточку места?', 'Məkan kartı silinsin?', 'Delete this place?'),
        field_error=t('Исправьте поле', 'Sahəni düzəldin', 'Correct this field'),
        change_mode=t('При смене типа цены или оплаты несовместимые суммы и периоды очищаются.', 'Qiymət və ya ödəniş növü dəyişəndə uyğun olmayan məbləğ və dövrlər təmizlənir.', 'Changing the price or billing type clears incompatible amounts and periods.'),
    )


def build_steps(form):
    def fields(names):
        return [form[name] for name in names.split() if name in form.fields]
    def step(number, title, hint, names='', optional=''):
        return dict(number=number, title=title, hint=hint, fields=fields(names), optional=fields(optional))
    return [
        step(1, t('О месте', 'Məkan haqqında', 'About the place'), t('Начните с названия, категории и описания.', 'Ad, kateqoriya və təsvirlə başlayın.', 'Start with a name, category and description.'), 'name_az description_az category subcategory', 'name_ru description_ru name_en description_en'),
        step(2, t('Для кого', 'Kimlər üçün', 'Audience'), t('Возраст относится к детским группам.', 'Yaş uşaqların qruplarına aiddir.', 'The age range describes children’s groups.'), 'age_from age_to offers_adult_classes', 'lesson_duration_minutes lesson_format lessons_per_week lessons_per_month'),
        step(3, t('Тарифы', 'Tariflər', 'Pricing'), t('Что входит и сколько стоит.', 'Nələr daxildir və qiyməti nədir.', 'What is included and what it costs.')),
        step(4, t('Адрес и карта', 'Ünvan və xəritə', 'Address and map'), t('Помогите семьям найти вход.', 'Ailələrə girişi tapmağa kömək edin.', 'Help families find the entrance.'), 'region district address', 'metro'),
        step(5, t('Контакты и расписание', 'Əlaqə və cədvəl', 'Contact and schedule'), t('Как связаться и когда можно прийти.', 'Necə əlaqə saxlamaq və nə vaxt gəlmək olar.', 'How to get in touch and when to visit.'), 'phone1', 'phone2 phone3 instagram website extra_conditions_az extra_conditions_ru extra_conditions_en additional_info_az additional_info_ru additional_info_en extra_conditions additional_info'),
        step(6, t('Фотографии', 'Şəkillər', 'Photos'), t('Покажите само место и занятия.', 'Məkanı və məşğələləri göstərin.', 'Show the place and its activities.'), 'photo gallery_images'),
        step(7, t('Проверка', 'Yoxlama', 'Review'), t('Проверьте все разделы и отправьте на модерацию.', 'Bütün bölmələri yoxlayıb moderasiyaya göndərin.', 'Review every section and send for moderation.'), 'moderation_note'),
    ]

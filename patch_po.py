import re

translations = {
    "Пользователи сайта": "Sayt istifadəçiləri",
    "Пользователь сайта": "Sayt istifadəçisi",
    "Фото для блоков сайта": "Sayt üçün şəkillər",
    "Фото галереи": "Qalereya şəkli",
    "Сотрудники админки": "Admin panel işçiləri",
    "Сотрудник админки": "Admin panel işçisi",
    "История изменений карточки": "Obyekt dəyişiklik tarixçəsi",
    "История изменений": "Dəyişiklik tarixçəsi",
    "Отзывы по кружкам": "Dərnək rəyləri",
    "Отзыв по кружку": "Dərnək rəyi",
    "Рейтинг кружков": "Dərnək reytinqi",
    "Отзывы о сайте": "Sayt haqqında rəylər",
    "Отзыв о сайте": "Sayt haqqında rəy",
    "Подтверждение email": "E-poçt təsdiqi",
    "Профили пользователей": "İstifadəçi profilləri",
    "Профиль пользователя": "İstifadəçi profili",
    "Аудит заявок на владение": "Sahiblik müraciətlərinin auditi",
    "Аудит заявки на владение": "Sahiblik müraciəti auditi",
    "Настройки контента каталога": "Kataloq məzmunu ayarları",
}

def patch_po(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for msgid, msgstr in translations.items():
        # Find msgid "..."
        # msgstr "" (or existing translation)
        # and replace msgstr
        pattern = r'(msgid "' + re.escape(msgid) + r'"\nmsgstr )".*?"'
        content = re.sub(pattern, r'\1"' + msgstr + '"', content)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_po('locale/az/LC_MESSAGES/django.po')

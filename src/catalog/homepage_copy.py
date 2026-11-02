"""Localized homepage copy; editorial SiteSettings values remain authoritative."""
HOME_TITLES = {
    'ru': 'Места и занятия для детей в Азербайджане',
    'en': 'Places and activities for children in Azerbaijan',
    'az': 'Azərbaycanda uşaqlar üçün məkanlar və məşğələlər',
}
HOME_SUBTITLES = {
    'ru': 'Кружки, секции, парки и развлечения — выбирайте по возрасту и району.',
    'en': 'Clubs, classes, parks and entertainment — choose by age and area.',
    'az': 'Dərnəklər, məşğələlər, parklar və əyləncə — yaşa və rayona görə seçin.',
}
HOME_COPY_DEFAULTS = {
    **{f'home_title_{lang}': text for lang, text in HOME_TITLES.items()},
    **{f'home_subtitle_{lang}': text for lang, text in HOME_SUBTITLES.items()},
}
# Only these known defaults may be replaced on an existing installation.
LEGACY_HOME_COPY = {
    'home_title_ru': {'Найдите кружок для ребёнка в Азербайджане', 'Найдите подходящее занятие для ребёнка'},
    'home_title_en': {'Find a club for your child in Azerbaijan', 'Find the right activity for your child'},
    'home_title_az': {'Azərbaycanda uşağınız üçün dərnək tapın', 'Uşağınız üçün uyğun məşğələni tapın'},
    'home_subtitle_ru': {'Спорт, творчество, музыка, образование по всем регионам — всё в одном месте.', 'Кружки, курсы и события рядом — всё в одном месте.'},
    'home_subtitle_en': {'Sports, creativity, music, and education across all regions in one place.', 'Nearby clubs, classes and events — all in one place.'},
    'home_subtitle_az': {'Bütün regionlarda idman, yaradıcılıq, musiqi və təhsil — hamısı bir yerdə.', 'Yaxınlıqdakı dərnək, kurs və tədbirlər — hamısı bir yerdə.'},
}

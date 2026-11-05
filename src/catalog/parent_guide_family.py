"""Editorial choices for the flagship guide; venue facts stay in the catalog."""

# Public catalog IDs checked on 2026-11-05. Visibility is checked on every request.
PREFERRED_IDS = (366, 363, 324, 80, 294, 287)

FAMILY_COPY = {
    'ru': {
        'situations_title': 'Какой день вы планируете?',
        'situations_intro': 'Начните с ситуации, затем сравните возраст и стоимость в карточках мест.',
        'age_label': 'Возраст', 'age_unit': 'лет', 'age_unknown': 'Уточните у места',
        'price_label': 'Стоимость',
        'places_intro': 'Шесть отправных точек для семейного дня. Возраст и цены — из каталога; тариф может относиться к одному билету или отдельной активности. Перед поездкой проверьте условия.',
        'situations': [
            {'key': 'toddler', 'title': 'С малышом', 'text': 'Начните с короткой прогулки в парке. Проход с коляской, туалет и место для паузы уточните заранее.', 'topic_keys': ['parks'], 'age_range': (0, 3)},
            {'key': 'rain', 'title': 'В дождь', 'text': 'Игровой центр — для движения, музей — для спокойного знакомства с новой темой. Проверьте часы работы и возрастные зоны.', 'topic_keys': ['play-centers', 'museums']},
            {'key': 'free', 'title': 'Бесплатно', 'text': 'Здесь только места с указанным бесплатным посещением. Дорога, еда и дополнительные развлечения — отдельные расходы.', 'free_only': True},
            {'key': 'schoolchild', 'title': 'Со школьником', 'text': 'Выберите одну тему: космос, искусство или животные. Для первого визита достаточно части экспозиции; язык программы уточните заранее.', 'topic_keys': ['science', 'museums', 'animals'], 'age_range': (6, 12)},
        ],
        'situation_empty': 'Сейчас нет подходящих опубликованных мест. Посмотрите другие варианты ниже.',
        'venue_notes': {366: 'Для прогулки на свежем воздухе. Можно начать с короткого маршрута и оставить время для свободной игры.',
            363: 'Крытый игровой центр в Park Bulvar. Сравните возраст ребёнка с условиями выбранной игровой зоны.',
            324: 'Для знакомства с узорами и коврами. Предложите ребёнку найти повторяющиеся цвета и детали.',
            80: 'Для знакомства с животными. Выберите несколько интересных ребёнку видов и спланируйте паузы.',
            294: 'Для ребёнка, которому интересен космос. Перед визитом уточните сеанс, язык и возрастные условия программы.',
            287: 'Для короткой остановки во время прогулки по Старому городу: рассмотрите необычно маленькие книги.'},
    },
    'az': {
        'situations_title': 'Gününüzü necə keçirmək istəyirsiniz?',
        'situations_intro': 'Əvvəl vəziyyətə uyğun seçim edin, sonra məkanların yaş və qiymət məlumatlarını müqayisə edin.',
        'age_label': 'Yaş', 'age_unit': 'yaş', 'age_unknown': 'Məkandan dəqiqləşdirin',
        'price_label': 'Qiymət',
        'places_intro': 'Ailəvi gün üçün altı başlanğıc nöqtəsi. Yaş və qiymət məlumatları kataloqdandır; tarif bir biletə və ya ayrıca fəaliyyətə aid ola bilər. Getməzdən əvvəl şərtləri yoxlayın.',
        'situations': [
            {'key': 'toddler', 'title': 'Balaca uşaqla', 'text': 'Parkda qısa gəzintidən başlayın. Uşaq arabası ilə keçidi, tualeti və fasilə yerini əvvəlcədən dəqiqləşdirin.', 'topic_keys': ['parks'], 'age_range': (0, 3)},
            {'key': 'rain', 'title': 'Yağışlı gündə', 'text': 'Hərəkətli oyun üçün oyun mərkəzi, yeni mövzu ilə sakit tanışlıq üçün muzey seçin. İş saatlarını və yaş zonalarını yoxlayın.', 'topic_keys': ['play-centers', 'museums']},
            {'key': 'free', 'title': 'Ödənişsiz', 'text': 'Burada yalnız ziyarəti ödənişsiz göstərilən məkanlar var. Yol, yemək və əlavə əyləncələr ayrıca xərcdir.', 'free_only': True},
            {'key': 'schoolchild', 'title': 'Məktəbli ilə', 'text': 'Bir mövzu seçin: kosmos, incəsənət və ya heyvanlar. İlk səfərdə ekspozisiyanın bir hissəsi kifayətdir; proqramın dilini əvvəlcədən dəqiqləşdirin.', 'topic_keys': ['science', 'museums', 'animals'], 'age_range': (6, 12)},
        ],
        'situation_empty': 'Hazırda uyğun dərc edilmiş məkan yoxdur. Aşağıdakı digər variantlara baxın.',
        'venue_notes': {366: 'Açıq havada gəzinti üçün. Qısa marşrutdan başlayıb sərbəst oyun üçün vaxt saxlaya bilərsiniz.',
            363: 'Park Bulvar-da qapalı oyun mərkəzi. Uşağın yaşını seçilən oyun zonasının şərtləri ilə müqayisə edin.',
            324: 'Naxışlar və xalçalarla tanışlıq üçün. Uşağa təkrarlanan rəngləri və detalları tapmağı təklif edin.',
            80: 'Heyvanlarla tanışlıq üçün. Uşağın maraqlandığı bir neçə növü seçin və fasilələr planlaşdırın.',
            294: 'Kosmosla maraqlanan uşaq üçün. Seansın vaxtını, dilini və yaş şərtlərini əvvəlcədən dəqiqləşdirin.',
            287: 'İçərişəhər gəzintisi zamanı qısa dayanacaq üçün: qeyri-adi kiçik kitabları nəzərdən keçirin.'},
    },
    'en': {
        'situations_title': 'What kind of day are you planning?',
        'situations_intro': 'Start with your plans, then compare ages and prices in the venue cards.',
        'age_label': 'Age', 'age_unit': 'years', 'age_unknown': 'Check with the venue',
        'price_label': 'Cost',
        'places_intro': 'Six starting points for a family day. Ages and prices come from the catalog; a rate may cover one ticket or a separate activity. Check the conditions before visiting.',
        'situations': [
            {'key': 'toddler', 'title': 'With a toddler', 'text': 'Start with a short park walk. Check stroller access, toilets and somewhere to take a break before you go.', 'topic_keys': ['parks'], 'age_range': (0, 3)},
            {'key': 'rain', 'title': 'On a rainy day', 'text': 'Choose a play centre for movement or a museum for a quieter introduction to a new topic. Check opening hours and age zones.', 'topic_keys': ['play-centers', 'museums']},
            {'key': 'free', 'title': 'Without an entry fee', 'text': 'Only venues listed as free to visit appear here. Travel, food and extra activities are separate costs.', 'free_only': True},
            {'key': 'schoolchild', 'title': 'With a schoolchild', 'text': 'Pick one theme: space, art or animals. Part of an exhibition is enough for a first visit; check the programme language in advance.', 'topic_keys': ['science', 'museums', 'animals'], 'age_range': (6, 12)},
        ],
        'situation_empty': 'No matching published venues are available right now. Explore the other options below.',
        'venue_notes': {366: 'For an outdoor walk. Start with a short route and leave time for free play.',
            363: 'An indoor play centre in Park Bulvar. Compare your child’s age with the rules for the play zone you choose.',
            324: 'For exploring patterns and carpets. Invite your child to spot repeated colours and details.',
            80: 'For discovering animals. Choose a few species your child is interested in and plan some breaks.',
            294: 'For a child interested in space. Check the session time, language and programme age limits before visiting.',
            287: 'For a short stop on an Old City walk: take a closer look at unusually small books.'},
    },
}


def family_situations(guide, topics, by_id, preferred_ids):
    """Use full current topic membership, not just the six featured venues."""
    priority = {pk: rank for rank, pk in enumerate(preferred_ids)}
    result = []
    for item in guide.get('situations', ()):
        sources = [topic['choice_ids'] for topic in topics if topic['key'] in item.get('topic_keys', ())]
        ids = set(by_id) if item.get('free_only') else {pk for source in sources for pk in source}
        eligible = []
        for pk in sorted(ids, key=lambda pk: (priority.get(pk, len(priority)), pk)):
            place = by_id[pk]
            card = place._card_presentation
            if item.get('free_only') and card['prices']['kind'] != 'free':
                continue
            if item.get('age_range'):
                low, high = item['age_range']
                if (place.age_from is None and place.age_to is None
                        or place.age_from is not None and place.age_from > high
                        or place.age_to is not None and place.age_to < low):
                    continue
            eligible.append({'id': pk, 'name': card['name'], 'url': card['url'], 'name_language': card['name_language']})
        result.append({**item, 'places': eligible[:2]})
    return result

from .legal_content import section, paragraph, bullets, email_block

def _terms_sections_az() -> list[dict]:
    return [
        section(
            "general",
            "1. Ümumi müddəalar",
            paragraph("Bu İstifadə Şərtləri https://kidsmap.az ünvanında yerləşən KidsMap saytına girişi və təşkilatların kataloqu, tədbirlər, şəxsi kabinetlər, rəylər, reytinqlər, seçilmişlər, məkan əlavə etmə və idarəetmə sorğuları daxil olmaqla onun imkanlarından istifadəni tənzimləyir."),
            paragraph("İstifadəçi saytdan istifadə etməklə, hesab yaratmaqla və ya forma göndərməklə bu Şərtlərlə tanış olduğunu və onlara əməl etməyi öhdəsinə götürdüyünü təsdiq edir."),
            paragraph("İstifadəçi Şərtlərlə razılaşmırsa, bu Şərtlərin qəbul edilməsini tələb edən sayt funksiyalarından istifadəni dayandırmalıdır."),
            paragraph("Azərbaycan Respublikasının qanunvericiliyində nəzərdə tutulmuş istifadəçilərin məcburi hüquqları bu sənədlə məhdudlaşdırılmır.")
        ),
        section(
            "purpose",
            "2. KidsMap-ın təyinatı",
            paragraph("KidsMap uşaqlar üçün aşağıdakıların məlumat platforması və kataloqudur:"),
            bullets(
                "dərnəklərin;",
                "idman bölmələrinin;",
                "təhsil kurslarının;",
                "yaradıcılıq məşğələlərinin;",
                "mütəxəssislərin;",
                "təşkilatların;",
                "tədbirlərin."
            ),
            paragraph("KidsMap məlumatları tapmaq, baxmaq, müqayisə etmək və saxlamaq, həmçinin müvafiq təşkilatlarla əlaqə saxlamaq üçün texniki imkan yaradır."),
            paragraph("Açıq şəkildə başqa hal nəzərdə tutulmayıbsa, KidsMap:"),
            bullets(
                "məşğələlərin və tədbirlərin təşkilatçısı deyil;",
                "yerləşdirilmiş təşkilatlar adından xidmət göstərmir;",
                "məşqçilərin və ya müəllimlərin işəgötürəni deyil;",
                "səhifə sahiblərinin agenti və ya nümayəndəsi deyil;",
                "istifadəçi və təşkilat arasında müqavilə tərəfi deyil;",
                "uşağın qəbul edilməsi barədə qərar qəbul etmir;",
                "qanunla icazə verilən həddə təşkilat tərəfindən məşğələlərin keçirilməsinə görə məsuliyyət daşımır."
            ),
            paragraph("KidsMap başqa cür bəyan etmədikdə, məşğələlər, ödəniş, vəsaitin qaytarılması, davamiyyət, təhlükəsizlik və digər şərtlər barədə razılaşmalar birbaşa istifadəçi ilə seçilmiş təşkilat arasında yaranır.")
        ),
        section(
            "accuracy",
            "3. Məlumatın düzgünlüyü",
            paragraph("KidsMap məlumatları aktual saxlamağa çalışır, lakin təşkilatlar və istifadəçilər tərəfindən təqdim edilən bütün məlumatların mütləq dəqiqliyinə zəmanət verə bilməz."),
            paragraph("Kartlarda yerləşdirilən məlumatların bir hissəsi açıq mənbələrdən, təşkilat nümayəndələrindən, istifadəçilərdən və digər üçüncü şəxslərdən əldə oluna bilər."),
            paragraph("Qeydiyyatdan və ya ödənişdən əvvəl istifadəçiyə müstəqil şəkildə aşağıdakıları təsdiqləmək tövsiyə olunur:"),
            bullets(
                "aktual qiyməti;",
                "cədvəli;",
                "yaş məhdudiyyətlərini;",
                "boş yerlərin mövcudluğunu;",
                "ünvanı;",
                "mütəxəssislərin ixtisasını;",
                "zəruri lisenziya və icazələri;",
                "ziyarət qaydalarını;",
                "ləğvetmə və qaytarılma şərtlərini;",
                "təhlükəsizlik tələblərini."
            ),
            paragraph("KidsMap administrasiyası bütün məlumatların hər an tam, aktual və səhvsiz olmasına zəmanət vermir. Qeydiyyatdan, ödənişdən və ya ziyarətdən əvvəl istifadəçi əsas şərtləri birbaşa təşkilatla özü dəqiqləşdirməlidir."),
            paragraph("Əgər istifadəçi səhv aşkar edərsə, bu barədə aşağıdakı ünvana yaza bilər:"),
            email_block("KidsMap əlaqə emaili:"),
            paragraph("Bu bölmədəki heç bir müddəa KidsMap-ı qanunla istisna edilə bilməyən məsuliyyətdən azad etmir.")
        ),
        section(
            "badges",
            "4. Yoxlanış nişanları",
            paragraph("Saytda 'KidsMap tərəfindən yoxlanılıb', 'Sahibi təsdiqlənib' və ya oxşar statuslar istifadə edilirsə, hər bir nişanın mənası faktiki olaraq həyata keçirilmiş yoxlama ilə müəyyən edilir (məsələn, istifadəçinin əlaqə nömrəsi və ya email vasitəsilə təşkilatla əlaqəsinin baza təsdiqi)."),
            paragraph("Belə nişan avtomatik olaraq aşağıdakıları ifadə etmir:"),
            bullets(
                "dövlət akkreditasiyasını;",
                "bütün mümkün lisenziyaların mövcudluğunu;",
                "hər bir işçinin yoxlanılmasını;",
                "xidmət keyfiyyətinə zəmanəti;",
                "təhlükəsizlik zəmanətini;",
                "dövlət orqanı adından tövsiyəni."
            )
        ),
        section(
            "users-and-age",
            "5. İstifadəçilər və yaş",
            paragraph("Sayt əsasən yetkinlik yaşına çatmış istifadəçilər, valideynlər, uşaqların qanuni nümayəndələri və təşkilatların nümayəndələri üçün nəzərdə tutulub."),
            paragraph("Yetkinlik yaşına çatmayan şəxs müstəqil şəkildə aşağıdakıları etməməlidir:"),
            bullets(
                "təşkilat kartı əlavə etmək;",
                "təşkilatı idarə etmək üçün sorğu göndərmək;",
                "fərdi məlumatları dərc etmək;",
                "öhdəliklər götürmək;",
                "ödənişli razılaşmalar bağlamaq,"
            ),
            paragraph("əgər bunun üçün qanuni nümayəndənin razılığı və ya iştirakı tələb olunursa."),
            paragraph("İstifadəçi doğru məlumat təqdim etməyə və qanun tələb etdikdə saytdan qanuni nümayəndənin iştirakı ilə istifadə etməyə borcludur.")
        ),
        section(
            "registration",
            "6. Qeydiyyat və hesab",
            paragraph("Ayrı-ayrı funksiyalar üçün qeydiyyat tələb oluna bilər."),
            paragraph("İstifadəçi borcludur:"),
            bullets(
                "doğru məlumatlar təqdim etməyə;",
                "özünə məxsus olan e-poçtdan istifadə etməyə;",
                "özünü başqa şəxs kimi qələmə verməməyə;",
                "giriş məlumatlarının məxfiliyini təmin etməyə;",
                "hesabı üçüncü şəxslərə verməməyə;",
                "icazəsiz giriş barədə məlumat verməyə;",
                "məlumatları vaxtında yeniləməyə."
            ),
            paragraph("Qanunvericiliklə başqa qayda müəyyən edilməyibsə və ya KidsMap tərəfindən pozuntuya səbəb olmayıbsa, istifadəçi öz hesabı vasitəsilə edilən hərəkətlərə görə məsuliyyət daşıyır."),
            paragraph("KidsMap sındırılma, dələduzluq, spam, sui-istifadə, bu Şərtlərin pozulması və ya istifadəçilərin təhlükəsizliyinə təhdid barədə əsaslı şübhə olduqda hesaba girişi müvəqqəti məhdudlaşdırmaq hüququna malikdir.")
        ),
        section(
            "roles",
            "7. İstifadəçilər və kart üzrə hüquqlar",
            paragraph("Saytda qeydiyyatdan keçmiş istifadəçinin yalnız bir növü var. Ayrıca sahib hesabı və ya biznes hesabı nəzərdə tutulmayıb."),
            paragraph("Qeydiyyatdan keçmiş istənilən istifadəçi kataloqa məkan əlavə edə bilər."),
            paragraph("Sahib və ya təşkilatın nümayəndəsi olmaq — konkret şəxsin konkret karta münasibətidir, hesab növü deyil. Kartı idarə etmək hüququ idarəetmə sorğusu təsdiqləndikdən və ya sistem tərəfindən nəzərdə tutulmuş proses vasitəsilə verilir və yalnız həmin karta şamil olunur."),
            paragraph("Kartı idarə etmək hüququnun alınması KidsMap-ə mülkiyyət hüququnun verilməsi, istifadəçinin bütün bəyanatlarının təsdiqi, dövlət orqanı tərəfindən lisenziyanın verilməsi və ya gələcək bütün nəşrlərin avtomatik təsdiqlənməsi demək deyil."),
            paragraph("KidsMap əməkdaşlarının rolları (moderator, administrator) ayrıca xidməti rollardır və adi istifadəçi hesabı ilə birlikdə verilmir.")
        ),
        section(
            "ownership",
            "8. Mülkiyyət (ownership) sorğuları",
            paragraph("Səhifəni idarə etmək üçün sorğu verən istifadəçi təsdiq edir ki:"),
            bullets(
                "təşkilatla qanuni əlaqəsi var;",
                "təşkilatı təmsil etmək hüququna və ya müvafiq icazəyə malikdir;",
                "doğru məlumatlar təqdim edir;",
                "aldatma yolu ilə başqasının təşkilatına giriş əldə etməyə çalışmır."
            ),
            paragraph("KidsMap aşağıdakı hüquqlara malikdir:"),
            bullets(
                "səlahiyyətlərin təsdiqini tələb etmək;",
                "əlavə məlumat tələb etmək;",
                "təşkilatla əlaqə saxlamaq;",
                "sorğudan imtina etmək;",
                "əvvəllər verilmiş girişi ləğv etmək;",
                "idarəetməni digər təsdiqlənmiş nümayəndəyə ötürmək;",
                "təhlükəsizlik və audit üçün qərarların tarixçəsini saxlamaq."
            ),
            paragraph("Yalan sənədlərin və ya məlumatların təqdim edilməsi hesabın bloklanmasına və qanunla nəzərdə tutulmuş digər nəticələrə səbəb ola bilər.")
        ),
        section(
            "team",
            "9. Kart komandası (team)",
            paragraph("Sistem tərəfindən belə funksiya nəzərdə tutulubsa, kartı idarə edən istifadəçi həmin kartın komandasına digər istifadəçiləri dəvət edə bilər."),
            paragraph("Dəvət göndərən şəxs düzgün e-poçtdan istifadə etməyə, yalnız səlahiyyətli şəxsləri dəvət etməyə, minimum zəruri hüquqları təyin etməyə və təşkilatı daha təmsil etməyən şəxslərin girişini silməyə borcludur."),
            paragraph("Komanda üzvü hüquqlardan yalnız verilmiş rol daxilində istifadə etməlidir. KidsMap təhlükəsizliyin və ya bu Şərtlərin pozulması halında komanda üzvünün girişini məhdudlaşdırmaq hüququna malikdir.")
        ),
        section(
            "content-management",
            "10. Səhifələrin yaradılması və redaktəsi",
            paragraph("Sahib və ya digər səlahiyyətli istifadəçi yerləşdirilən məlumatın dəqiqliyinə görə məsuliyyət daşıyır."),
            paragraph("Aşağıdakıları dərc etmək qadağandır:"),
            bullets(
                "uydurma təşkilatlar və xidmətlər;",
                "yalançı qiymətlər;",
                "yanıltıcı endirimlər;",
                "əsassız olaraq başqasının əlaqə məlumatları;",
                "üçüncü şəxslərin hüquqlarını pozan məlumatlar;",
                "qanunla qadağan olunmuş materiallar."
            ),
            paragraph("Məlumat qaralama kimi saxlanıla, moderasiyaya göndərilə, rədd edilə, dərc edilə, yayından qaldırıla, müvəqqəti gizlədilə, silinə və ya arxivə köçürülə bilər."),
            paragraph("Moderasiya təşkilatın tam hüquqi, maliyyə və ya peşəkar auditi demək deyil.")
        ),
        section(
            "pricing",
            "11. Qiymətlər, cədvəl və təkliflər",
            paragraph("Təşkilat dərc edilmiş qiymətləri, cədvəli və şərtləri aktual saxlamağa borcludur."),
            paragraph("Əgər qiymət yaşdan, müddətdən, filialdan, paketdən asılıdırsa, bu anlaşıqlı və istifadəçini çaşdırmadan göstərilməlidir."),
            paragraph("'Pulsuz', 'endirim', 'ən yaxşı qiymət', 'zəmanətli nəticə' və oxşar ifadələrin faktiki əsası olmalıdır.")
        ),
        section(
            "events",
            "12. Tədbirlər",
            paragraph("Tədbirin təşkilatçısı tarixə, vaxta, məkana, yaş məhdudiyyətlərinə, qiymətə, biletlərin mövcudluğuna, ləğvə, dəyişdirilməyə, ziyarət qaydalarına, təhlükəsizliyə və vəsaitin qaytarılmasına görə məsuliyyət daşıyır."),
            paragraph("Qanunla və ya ayrıca KidsMap şərtləri ilə başqa hal nəzərdə tutulmayıbsa, KidsMap müstəqil təşkilatçı tərəfindən tədbirin ləğvinə və ya dəyişdirilməsinə görə məsuliyyət daşımır.")
        ),
        section(
            "reviews",
            "13. Rəylər, reytinqlər və reaksiyalar",
            paragraph("İstifadəçi yalnız öz dürüst təcrübəsi və ya etibarlı məlumat əsasında rəy yaza bilər."),
            paragraph("Aşağıdakılar qadağandır:"),
            bullets(
                "sifarişli yalançı rəylər və reytinqin kütləvi şəkildə süni artırılması;",
                "zərər vurmaq məqsədilə rəqiblər tərəfindən rəylərin dərci;",
                "təhdidlər, təhqirlər, ayrı-seçkilik xarakterli ifadələr;",
                "əsassız olaraq fərdi məlumatların və uşaq haqqında məlumatların yayılması;",
                "spam, reklam, hədə-qorxu və qeyri-qanuni materiallar."
            ),
            paragraph("KidsMap rəyi moderasiya etmək, gizlətmək və ya silmək hüququna malikdir. Rəyin silinməsi KidsMap-ın mübahisədə hər hansı tərəfi tanıması demək deyil."),
            paragraph("Təşkilat əsaslı şikayət verə bilər, lakin mənfi rəyin sırf mənfi olduğu üçün silinməsini tələb edə bilməz.")
        ),
        section(
            "children-materials",
            "14. Uşaqlarla bağlı foto və materiallar",
            paragraph("Zəruri hüquq və icazələr olmadan uşağın təsviri olan foto, video və ya digər materialları yükləmək qadağandır."),
            paragraph("Materialı yükləyən istifadəçi təsdiq edir ki:"),
            bullets(
                "ondan istifadə etmək hüququna malikdir;",
                "valideyn və ya qanuni nümayəndədən lazımi razılıq alıb;",
                "nəşr uşağın təhlükəsizliyini təhdid etmir;",
                "materialda alçaldıcı, zərərli və ya qeyri-qanuni məzmun yoxdur."
            ),
            paragraph("Uşağın ünvanını, əlaqə məlumatlarını, tibbi məlumatlarını, dəqiq marşrutunu və digər həssas məlumatları yayan materialları dərc etmək qadağandır."),
            paragraph("KidsMap şikayət üzrə yoxlama başa çatana qədər materialı dərhal gizlətmək hüququna malikdir. Silinmə sorğusu aşağıdakı ünvana göndərilməlidir:"),
            email_block("KidsMap əlaqə emaili:")
        ),
        section(
            "prohibited-content",
            "15. Qadağan olunmuş məzmun",
            paragraph("İstifadəçiyə qanunla qadağan olunmuş məzmun, zorakılığa çağırış, uşaqların istismarı, pornoqrafik materiallar, təhdidlər, zərərli kod, spam, avtomatlaşdırılmış kütləvi nəşrlər və qeyri-qanuni təkliflər yerləşdirmək və ya yaymaq qadağandır."),
            paragraph("KidsMap belə materialı silmək və ya ona girişi məhdudlaşdırmaq, qanunla nəzərdə tutulmuş hallarda isə məlumatları səlahiyyətli orqanlara vermək hüququna malikdir.")
        ),
        section(
            "intellectual-property",
            "16. KidsMap intellektual mülkiyyəti",
            paragraph("KidsMap adına, loqotipinə, dizaynına, proqram koduna, sayt strukturuna, orijinal mətnlərə, qrafik elementlərə və verilənlər bazasının tərtibinə dair hüquqlar müvafiq hüquq sahiblərinə məxsusdur."),
            paragraph("İcazə olmadan aşağıdakılar qadağandır:"),
            bullets(
                "kataloqun mühüm hissəsini kopyalamaq;",
                "avtomatlaşdırılmış scraping istifadə etmək;",
                "dizaynı kopyalamaq və ya özünü KidsMap kimi qələmə vermək;",
                "texniki məhdudiyyətlərdən yan keçmək."
            ),
            paragraph("İstifadəçi tərəfindən açıq səhifələrdən şəxsi qeyri-kommersiya məqsədləri üçün adi qaydada istifadəyə saytın funksionallığı və qanunvericilik çərçivəsində icazə verilir.")
        ),
        section(
            "user-content",
            "17. İstifadəçi məzmunu",
            paragraph("İstifadəçi ona məxsus olan məzmun üzərindəki hüquqlarını saxlayır."),
            paragraph("Məzmunu yükləyərkən istifadəçi KidsMap-ə ondan yalnız saxlamaq, texniki emal etmək, saytda göstərmək, uyğunlaşdırmaq, moderasiya etmək, tərcümə etmək və konkret KidsMap səhifəsini tanıtmaq üçün zəruri olan həcmdə müstəsna olmayan, pulsuz istifadə hüququ verir."),
            paragraph("Belə icazə material saytda yerləşdirildiyi müddətdə, silindikdən sonra isə yalnız texniki ehtiyat nüsxələri, audit və qanunvericiliyin məcburi tələbləri çərçivəsində etibarlıdır.")
        ),
        section(
            "complaints",
            "18. Hüquq pozuntuları ilə bağlı şikayətlər",
            paragraph("Şikayət aşağıdakı ünvana göndərilə bilər:"),
            email_block("KidsMap əlaqə emaili:"),
            paragraph("Şikayətdə müraciət edənin adını, əlaqə e-poçtunu, materiala keçidi, pozuntunun təsvirini və tələb olunan hərəkəti göstərmək tövsiyə olunur."),
            paragraph("KidsMap əlavə məlumat tələb etmək və yoxlama dövründə mübahisəli materialı müvəqqəti olaraq gizlətmək hüququna malikdir. Bilə-bilə yalan şikayət sui-istifadə hesab edilə bilər.")
        ),
        section(
            "advertising",
            "19. Reklam",
            paragraph("Reklam materialları istifadəçini çaşdırmamalı, reklam xarakterini gizlətməməli və uşaqlar haqqında məlumatlardan qanunsuz şəkildə istifadə etməməlidir.")
        ),
        section(
            "platform-access",
            "20. Platformadan istifadə",
            paragraph("KidsMap-in əsas imkanlarından pulsuz istifadə etmək olar.")
        ),
        section(
            "third-parties",
            "21. Kənar təşkilatlar və keçidlər",
            paragraph("Saytda xarici resurslara, sosial şəbəkələrə və bron sistemlərinə keçidlər ola bilər. Kənar resursa keçid etdikdə istifadəçi müvafiq sahiblə sərbəst şəkildə qarşılıqlı əlaqədə olur."),
            paragraph("KidsMap kənar saytın əlçatanlığına, onun qaydalarına, məlumatların işlənməsinə, qiymətlərinə və təhlükəsizliyinə nəzarət etmir.")
        ),
        section(
            "privacy",
            "22. Fərdi məlumatlar",
            paragraph("Fərdi məlumatların işlənməsi ayrıca KidsMap Məxfilik Siyasəti ilə tənzimlənir."),
            paragraph("Bu Şərtlər ilə Məxfilik Siyasəti arasında ziddiyyət olduqda, fərdi məlumatların işlənməsi məsələləri Məxfilik Siyasəti və qanunvericiliyin məcburi normaları ilə tənzimlənir.")
        ),
        section(
            "availability",
            "23. Saytın əlçatanlığı",
            paragraph("KidsMap sabit işləməyi təmin etməyə çalışır, lakin texniki işlər, nasazlıqlar, üçüncü tərəf xidmətlərinin məhdudiyyətləri və digər hallar mümkündür."),
            paragraph("KidsMap saytın fasiləsiz və səhvsiz işləməsinə zəmanət vermir, lakin məlum kritik səhvləri aradan qaldırmaq və təhlükəsizliyi təmin etmək üçün ağlabatan tədbirlər görməyi öhdəsinə götürür.")
        ),
        section(
            "security",
            "24. Təhlükəsizlik",
            paragraph("İcazəsiz giriş əldə etməyə cəhd etmək, parolları tapmaq, zərərli kod yükləmək, texniki məhdudiyyətləri pozaraq kütləvi şəkildə məlumat toplamaq və ya moderasiya axınından yan keçmək qadağandır."),
            paragraph("KidsMap girişi məhdudlaşdırmaq və insidentlə bağlı texniki məlumatları saxlamaq hüququna malikdir.")
        ),
        section(
            "suspension",
            "25. Girişin dayandırılması və ləğvi",
            paragraph("Şərtlərin kobud şəkildə pozulması, dələduzluq, təhlükəsizlik təhdidi, qanunsuz məzmun və ya səlahiyyətli orqanın qanuni tələbi olduqda KidsMap istifadəçinin girişini məhdudlaşdırmaq və ya ləğv etmək hüququna malikdir."),
            paragraph("Mümkün olduqda və təhlükə yaratmadıqda, istifadəçiyə məhdudiyyətin səbəbi barədə məlumat verilə bilər.")
        ),
        section(
            "deletion",
            "26. Hesabın silinməsi",
            paragraph("İstifadəçi hesabın silinməsi üçün aşağıdakı ünvana sorğu göndərə bilər:"),
            email_block("KidsMap əlaqə emaili:"),
            paragraph("Hesabın silinməsi həmişə hər bir qeydin dərhal fiziki olaraq silinməsi demək deyil. Məlumatların bir hissəsi audit, təhlükəsizlik, mübahisələrin həlli və bazanın bütövlüyünün qorunması üçün qanunla nəzərdə tutulmuş hədlərdə saxlanıla bilər.")
        ),
        section(
            "liability",
            "27. Məsuliyyətin məhdudlaşdırılması",
            paragraph("Qanunvericiliklə yol verilən həddə:"),
            bullets(
                "KidsMap müstəqil təşkilatların hərəkətlərinə görə məsuliyyət daşımır;",
                "KidsMap yalnız üçüncü şəxslərin məlumatları əsasında istifadəçinin qəbul etdiyi qərarlara görə məsuliyyət daşımır;",
                "KidsMap konkret təhsil, idman və ya digər nəticəyə zəmanət vermir;",
                "KidsMap platformanı xəbərdar etmədən təşkilat tərəfindən şərtlərin dəyişdirilməsinə görə məsuliyyət daşımır."
            ),
            paragraph("Tətbiq olunan qanunvericilikdə birbaşa başqa hal nəzərdə tutulmadıqda, KidsMap açıq mənbələrdən və ya üçüncü şəxslərdən əldə edilmiş köhnəlmiş, natamam və ya xəbərdarlıq edilmədən dəyişdirilmiş məlumatlara görə də məsuliyyət daşımır."),
            paragraph("Şərtlərin heç bir müddəası qanunla istisna edilə bilməyən məsuliyyəti, istehlakçının məcburi hüquqlarını və ya qəsdən edilmiş hüquqazidd hərəkətlərə görə məsuliyyəti istisna etmir.")
        ),
        section(
            "user-liability",
            "28. İstifadəçinin məsuliyyəti",
            paragraph("İstifadəçi öz hərəkətlərinin qanuniliyinə, təqdim etdiyi məlumatların doğruluğuna, yerləşdirdiyi məzmuna, icazələrin mövcudluğuna və hesabının təhlükəsizliyinə görə məsuliyyət daşıyır."),
            paragraph("İstifadəçinin hərəkətləri təsdiqlənmiş zərərə səbəb olarsa, ödəniş məsələsi qanunvericiliyə uyğun olaraq həll edilir.")
        ),
        section(
            "changes",
            "29. Saytın dəyişdirilməsi",
            paragraph("KidsMap interfeysi yaxşılaşdırmaq, funksiyalar əlavə etmək və ya silmək, kateqoriyaları və moderasiya qaydalarını dəyişdirmək hüququna malikdir."),
            paragraph("İstifadəçilərin hüquqlarına təsir edən mühüm dəyişikliklər məcburi hüquqların zərərinə gizli və ya keçmiş tarixə tətbiq edilmir.")
        ),
        section(
            "terms-changes",
            "30. Şərtlərin dəyişdirilməsi",
            paragraph("Aktual versiya bu səhifədə yerləşdirilir. Mühüm dəyişikliklər olduqda istifadəçilərə sayt, şəxsi kabinet və ya e-poçt vasitəsilə bildiriş göndərilə bilər."),
            paragraph("Bildirişdən sonra istifadənin davam etdirilməsi yalnız qanunvericiliklə icazə verilən həddə yeni versiyanın qəbul edilməsi demək ola bilər.")
        ),
        section(
            "disputes",
            "31. Mübahisələrin həlli",
            paragraph("İstifadəçi ilk olaraq müraciətini aşağıdakı ünvana göndərə bilər:"),
            email_block("KidsMap əlaqə emaili:"),
            paragraph("Tərəflər mübahisəni danışıqlar yolu ilə həll etməyə çalışırlar. Bu, istifadəçinin səlahiyyətli dövlət orqanına və ya məhkəməyə müraciət etmək hüququnu məhdudlaşdırmır.")
        ),
        section(
            "applicable-law",
            "32. Tətbiq edilən hüquq",
            paragraph("Bu Şərtlərə Azərbaycan Respublikasının qanunvericiliyi tətbiq edilir."),
            paragraph("İstifadəçinin tətbiq edilən qanunvericiliyə əsasən məcburi hüquqları varsa, bu Şərtlər həmin hüquqları məhdudlaşdırmır.")
        ),
        section(
            "severability",
            "33. Müddəaların bölünməsi",
            paragraph("Ayrı-ayrı müddəa etibarsız və ya tətbiq edilə bilməz hesab edildikdə, qalan müddəalar qanunvericiliklə yol verilən həddə qüvvədə qalır.")
        ),
        section(
            "contacts",
            "34. Əlaqə",
            paragraph("Saytdan istifadə, şikayətlər, səhifələr, hesablar və məzmunla bağlı suallar üçün müraciət edin:"),
            email_block("KidsMap əlaqə emaili:")
        )
    ]

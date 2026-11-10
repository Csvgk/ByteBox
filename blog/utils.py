from django.utils.text import slugify

# Українська транслітерація (спрощена), щоб адреси статей були латиницею: «Як обрати БЖ» -> «yak-obraty-bzh»
UA_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ie', 'ж': 'zh', 'з': 'z',
    'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh',
    'щ': 'shch', 'ь': '', 'ю': 'iu', 'я': 'ia', "'": '', '’': '',
}


def make_slug(text):
    latin = ''.join(UA_TO_LAT.get(ch, ch) for ch in text.lower())
    return slugify(latin)

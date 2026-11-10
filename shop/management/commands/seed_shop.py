from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.images import generate_product_image
from shop.models import Brand, Category, Product

K = Category.Kind

CATEGORIES = [
    (K.CPU, 'Процесори', 'processors'),
    (K.MOTHERBOARD, 'Материнські плати', 'motherboards'),
    (K.RAM, 'Оперативна пам\'ять', 'ram'),
    (K.GPU, 'Відеокарти', 'gpu'),
    (K.STORAGE, 'Накопичувачі', 'storage'),
    (K.PSU, 'Блоки живлення', 'psu'),
    (K.CASE, 'Корпуси', 'cases'),
]

# (тип, бренд, назва, ціна, стара ціна, залишок, {характеристики сумісності}, "інші характеристики")
# Ціни демонстраційні
PRODUCTS = [
    (K.CPU, 'AMD', 'Ryzen 5 5600', 3999, 4599, 12,
     {'socket': 'AM4', 'memory_type': 'DDR4', 'power_draw': 65},
     'Ядер / потоків: 6 / 12\nЧастота: 3.5–4.4 ГГц\nКеш L3: 32 МБ'),
    (K.CPU, 'AMD', 'Ryzen 5 7600', 7499, None, 8,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 65, 'integrated_graphics': True},
     'Ядер / потоків: 6 / 12\nЧастота: 3.8–5.1 ГГц\nКеш L3: 32 МБ'),
    (K.CPU, 'AMD', 'Ryzen 7 7800X3D', 15999, 17499, 4,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 120, 'integrated_graphics': True},
     'Ядер / потоків: 8 / 16\nЧастота: 4.2–5.0 ГГц\nКеш L3: 96 МБ (3D V-Cache)'),
    (K.CPU, 'Intel', 'Core i5-12400F', 4599, None, 15,
     {'socket': 'LGA1700', 'power_draw': 117},
     'Ядер / потоків: 6 / 12\nЧастота: 2.5–4.4 ГГц'),
    (K.CPU, 'Intel', 'Core i5-13400F', 6999, None, 10,
     {'socket': 'LGA1700', 'power_draw': 148},
     'Ядер / потоків: 10 / 16\nЧастота: 2.5–4.6 ГГц'),
    (K.CPU, 'Intel', 'Core i7-14700K', 16999, None, 0,
     {'socket': 'LGA1700', 'power_draw': 253, 'integrated_graphics': True},
     'Ядер / потоків: 20 / 28\nЧастота: 3.4–5.6 ГГц'),

    (K.MOTHERBOARD, 'MSI', 'B550-A PRO', 5299, None, 7,
     {'socket': 'AM4', 'memory_type': 'DDR4', 'form_factor': 'ATX', 'power_draw': 30},
     'Чипсет: AMD B550\nСлотів пам\'яті: 4\nM.2: 2'),
    (K.MOTHERBOARD, 'ASUS', 'PRIME B650M-A', 6899, 7499, 6,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'form_factor': 'mATX', 'power_draw': 30},
     'Чипсет: AMD B650\nСлотів пам\'яті: 4\nM.2: 2'),
    (K.MOTHERBOARD, 'Gigabyte', 'B760M DS3H DDR4', 4499, None, 9,
     {'socket': 'LGA1700', 'memory_type': 'DDR4', 'form_factor': 'mATX', 'power_draw': 30},
     'Чипсет: Intel B760\nСлотів пам\'яті: 4\nM.2: 2'),
    (K.MOTHERBOARD, 'MSI', 'PRO Z790-P', 8999, None, 3,
     {'socket': 'LGA1700', 'memory_type': 'DDR5', 'form_factor': 'ATX', 'power_draw': 35},
     'Чипсет: Intel Z790\nСлотів пам\'яті: 4\nM.2: 4'),

    (K.RAM, 'Kingston', 'FURY Beast DDR4 16 ГБ (2×8) 3200 МГц', 1599, None, 20,
     {'memory_type': 'DDR4', 'power_draw': 5}, 'Обсяг: 16 ГБ\nЧастота: 3200 МГц'),
    (K.RAM, 'Kingston', 'FURY Beast DDR5 32 ГБ (2×16) 6000 МГц', 4199, 4599, 14,
     {'memory_type': 'DDR5', 'power_draw': 8}, 'Обсяг: 32 ГБ\nЧастота: 6000 МГц'),
    (K.RAM, 'Corsair', 'Vengeance DDR5 32 ГБ (2×16) 5600 МГц', 3899, None, 10,
     {'memory_type': 'DDR5', 'power_draw': 8}, 'Обсяг: 32 ГБ\nЧастота: 5600 МГц'),

    (K.GPU, 'ASUS', 'Dual GeForce RTX 4060 8 ГБ', 12999, 13999, 9,
     {'power_draw': 115}, 'Пам\'ять: 8 ГБ GDDR6\nРекомендований БЖ: 550 Вт'),
    (K.GPU, 'MSI', 'GeForce RTX 4070 SUPER Ventus 2X 12 ГБ', 26999, None, 5,
     {'power_draw': 220}, 'Пам\'ять: 12 ГБ GDDR6X\nРекомендований БЖ: 650 Вт'),
    (K.GPU, 'Sapphire', 'Pulse Radeon RX 7600 8 ГБ', 11499, None, 7,
     {'power_draw': 165}, 'Пам\'ять: 8 ГБ GDDR6\nРекомендований БЖ: 550 Вт'),
    (K.GPU, 'Sapphire', 'Pulse Radeon RX 7800 XT 16 ГБ', 22499, 23999, 4,
     {'power_draw': 263}, 'Пам\'ять: 16 ГБ GDDR6\nРекомендований БЖ: 700 Вт'),

    (K.STORAGE, 'Samsung', '980 1 ТБ M.2 NVMe', 2999, None, 18,
     {'power_draw': 6}, 'Обсяг: 1 ТБ\nІнтерфейс: PCIe 3.0 NVMe\nЧитання: до 3500 МБ/с'),
    (K.STORAGE, 'Kingston', 'NV2 2 ТБ M.2 NVMe', 4299, 4799, 11,
     {'power_draw': 6}, 'Обсяг: 2 ТБ\nІнтерфейс: PCIe 4.0 NVMe\nЧитання: до 3500 МБ/с'),

    (K.PSU, 'be quiet!', 'System Power 10 550W', 2399, None, 10,
     {'psu_power': 550}, 'Сертифікат: 80 PLUS Bronze'),
    (K.PSU, 'Corsair', 'RM750e 750W', 4199, None, 8,
     {'psu_power': 750}, 'Сертифікат: 80 PLUS Gold\nМодульний: так'),
    (K.PSU, 'Seasonic', 'Focus GX-850 850W', 5499, None, 5,
     {'psu_power': 850}, 'Сертифікат: 80 PLUS Gold\nМодульний: так'),

    (K.CASE, 'DeepCool', 'MATREXX 40', 1499, None, 12,
     {'form_factor': 'mATX'}, 'Підтримка плат: Micro-ATX, Mini-ITX'),
    (K.CASE, 'DeepCool', 'CC560', 2399, None, 9,
     {'form_factor': 'ATX'}, 'Підтримка плат: ATX, Micro-ATX, Mini-ITX\nВентиляторів у комплекті: 4'),
    (K.CASE, 'Lian Li', 'Lancool 216', 4299, 4699, 4,
     {'form_factor': 'ATX'}, 'Підтримка плат: E-ATX, ATX, Micro-ATX\nВентиляторів у комплекті: 3'),

    # ---------- Розширення каталогу ----------
    (K.CPU, 'AMD', 'Ryzen 7 5700X', 5999, 6499, 9,
     {'socket': 'AM4', 'memory_type': 'DDR4', 'power_draw': 65},
     'Ядер / потоків: 8 / 16\nЧастота: 3.4–4.6 ГГц\nКеш L3: 32 МБ'),
    (K.CPU, 'AMD', 'Ryzen 5 8600G', 8299, None, 7,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 65, 'integrated_graphics': True},
     'Ядер / потоків: 6 / 12\nЧастота: 4.3–5.0 ГГц\nГрафіка: Radeon 760M'),
    (K.CPU, 'AMD', 'Ryzen 7 9700X', 14499, None, 6,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 65, 'integrated_graphics': True},
     'Ядер / потоків: 8 / 16\nЧастота: 3.8–5.5 ГГц\nКеш L3: 32 МБ'),
    (K.CPU, 'AMD', 'Ryzen 9 7900X', 15499, 17999, 3,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 170, 'integrated_graphics': True},
     'Ядер / потоків: 12 / 24\nЧастота: 4.7–5.6 ГГц\nКеш L3: 64 МБ'),
    (K.CPU, 'Intel', 'Core i3-12100F', 3299, None, 18,
     {'socket': 'LGA1700', 'power_draw': 89},
     'Ядер / потоків: 4 / 8\nЧастота: 3.3–4.3 ГГц'),
    (K.CPU, 'Intel', 'Core i5-14600K', 12999, 13999, 6,
     {'socket': 'LGA1700', 'power_draw': 181, 'integrated_graphics': True},
     'Ядер / потоків: 14 / 20\nЧастота: 3.5–5.3 ГГц'),
    (K.CPU, 'Intel', 'Core i9-14900K', 23999, None, 2,
     {'socket': 'LGA1700', 'power_draw': 253, 'integrated_graphics': True},
     'Ядер / потоків: 24 / 32\nЧастота: 3.2–6.0 ГГц'),

    (K.MOTHERBOARD, 'ASUS', 'TUF GAMING B550-PLUS', 6299, None, 5,
     {'socket': 'AM4', 'memory_type': 'DDR4', 'form_factor': 'ATX', 'power_draw': 30},
     'Чипсет: AMD B550\nСлотів пам\'яті: 4\nM.2: 2'),
    (K.MOTHERBOARD, 'MSI', 'B550M PRO-VDH WIFI', 4699, 5199, 8,
     {'socket': 'AM4', 'memory_type': 'DDR4', 'form_factor': 'mATX', 'power_draw': 30},
     'Чипсет: AMD B550\nWi-Fi: так\nM.2: 2'),
    (K.MOTHERBOARD, 'Gigabyte', 'B650 AORUS ELITE AX', 9499, None, 4,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'form_factor': 'ATX', 'power_draw': 35},
     'Чипсет: AMD B650\nWi-Fi: так\nM.2: 3'),
    (K.MOTHERBOARD, 'MSI', 'MAG X670E TOMAHAWK WIFI', 13999, 14999, 3,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'form_factor': 'ATX', 'power_draw': 40},
     'Чипсет: AMD X670E\nWi-Fi: так\nM.2: 4'),
    (K.MOTHERBOARD, 'ASUS', 'PRIME B760M-A D4', 5199, None, 7,
     {'socket': 'LGA1700', 'memory_type': 'DDR4', 'form_factor': 'mATX', 'power_draw': 30},
     'Чипсет: Intel B760\nСлотів пам\'яті: 4\nM.2: 2'),
    (K.MOTHERBOARD, 'ASUS', 'TUF GAMING Z790-PLUS WIFI', 12499, None, 3,
     {'socket': 'LGA1700', 'memory_type': 'DDR5', 'form_factor': 'ATX', 'power_draw': 40},
     'Чипсет: Intel Z790\nWi-Fi: так\nM.2: 4'),

    (K.RAM, 'Kingston', 'FURY Beast DDR4 32 ГБ (2×16) 3600 МГц', 2899, 3199, 12,
     {'memory_type': 'DDR4', 'power_draw': 6}, 'Обсяг: 32 ГБ\nЧастота: 3600 МГц'),
    (K.RAM, 'G.Skill', 'Ripjaws V DDR4 16 ГБ (2×8) 3600 МГц', 1799, None, 15,
     {'memory_type': 'DDR4', 'power_draw': 5}, 'Обсяг: 16 ГБ\nЧастота: 3600 МГц'),
    (K.RAM, 'G.Skill', 'Trident Z5 RGB DDR5 32 ГБ (2×16) 6400 МГц', 5499, None, 6,
     {'memory_type': 'DDR5', 'power_draw': 9}, 'Обсяг: 32 ГБ\nЧастота: 6400 МГц\nПідсвітка: RGB'),
    (K.RAM, 'Corsair', 'Vengeance DDR5 64 ГБ (2×32) 6000 МГц', 7999, 8799, 4,
     {'memory_type': 'DDR5', 'power_draw': 10}, 'Обсяг: 64 ГБ\nЧастота: 6000 МГц'),

    (K.GPU, 'Gigabyte', 'GeForce RTX 3050 WINDFORCE OC 8 ГБ', 8999, 9799, 10,
     {'power_draw': 130}, 'Пам\'ять: 8 ГБ GDDR6\nРекомендований БЖ: 450 Вт'),
    (K.GPU, 'MSI', 'GeForce RTX 4060 Ti Ventus 2X 8 ГБ', 16499, None, 6,
     {'power_draw': 160}, 'Пам\'ять: 8 ГБ GDDR6\nРекомендований БЖ: 550 Вт'),
    (K.GPU, 'Gigabyte', 'GeForce RTX 4070 WINDFORCE OC 12 ГБ', 24499, 25999, 5,
     {'power_draw': 200}, 'Пам\'ять: 12 ГБ GDDR6X\nРекомендований БЖ: 650 Вт'),
    (K.GPU, 'ASUS', 'TUF Gaming GeForce RTX 4080 SUPER 16 ГБ', 48999, None, 2,
     {'power_draw': 320}, 'Пам\'ять: 16 ГБ GDDR6X\nРекомендований БЖ: 850 Вт'),
    (K.GPU, 'Sapphire', 'Pulse Radeon RX 7700 XT 12 ГБ', 17999, 19499, 5,
     {'power_draw': 245}, 'Пам\'ять: 12 ГБ GDDR6\nРекомендований БЖ: 700 Вт'),
    (K.GPU, 'Sapphire', 'Nitro+ Radeon RX 7900 XTX 24 ГБ', 44999, None, 2,
     {'power_draw': 355}, 'Пам\'ять: 24 ГБ GDDR6\nРекомендований БЖ: 850 Вт'),
    (K.GPU, 'ASRock', 'Intel Arc A750 Challenger 8 ГБ', 8499, None, 4,
     {'power_draw': 225}, 'Пам\'ять: 8 ГБ GDDR6\nРекомендований БЖ: 600 Вт'),

    (K.STORAGE, 'WD', 'Black SN850X 1 ТБ M.2 NVMe', 4199, 4699, 9,
     {'power_draw': 7}, 'Обсяг: 1 ТБ\nІнтерфейс: PCIe 4.0 NVMe\nЧитання: до 7300 МБ/с'),
    (K.STORAGE, 'Samsung', '990 PRO 2 ТБ M.2 NVMe', 7999, None, 5,
     {'power_draw': 8}, 'Обсяг: 2 ТБ\nІнтерфейс: PCIe 4.0 NVMe\nЧитання: до 7450 МБ/с'),
    (K.STORAGE, 'Crucial', 'P3 Plus 1 ТБ M.2 NVMe', 2699, None, 14,
     {'power_draw': 6}, 'Обсяг: 1 ТБ\nІнтерфейс: PCIe 4.0 NVMe\nЧитання: до 5000 МБ/с'),
    (K.STORAGE, 'Samsung', '870 EVO 500 ГБ SATA', 2199, None, 16,
     {'power_draw': 4}, 'Обсяг: 500 ГБ\nІнтерфейс: SATA III\nЧитання: до 560 МБ/с'),
    (K.STORAGE, 'Seagate', 'BarraCuda 2 ТБ HDD', 2599, None, 11,
     {'power_draw': 6}, 'Обсяг: 2 ТБ\nТип: жорсткий диск 7200 об/хв'),

    (K.PSU, 'MSI', 'MAG A650BN 650W', 2499, 2799, 13,
     {'psu_power': 650}, 'Сертифікат: 80 PLUS Bronze'),
    (K.PSU, 'be quiet!', 'Pure Power 12 M 750W', 4599, None, 7,
     {'psu_power': 750}, 'Сертифікат: 80 PLUS Gold\nМодульний: так'),
    (K.PSU, 'Corsair', 'RM850x 850W', 6299, None, 6,
     {'psu_power': 850}, 'Сертифікат: 80 PLUS Gold\nМодульний: так'),
    (K.PSU, 'Corsair', 'RM1000x 1000W', 7999, 8499, 3,
     {'psu_power': 1000}, 'Сертифікат: 80 PLUS Gold\nМодульний: так'),

    (K.CASE, 'Cooler Master', 'MasterBox Q300L', 1899, None, 10,
     {'form_factor': 'mATX'}, 'Підтримка плат: Micro-ATX, Mini-ITX'),
    (K.CASE, 'NZXT', 'H5 Flow', 3799, None, 6,
     {'form_factor': 'ATX'}, 'Підтримка плат: ATX, Micro-ATX, Mini-ITX\nВентиляторів у комплекті: 2'),
    (K.CASE, 'Corsair', '4000D Airflow', 4199, 4599, 5,
     {'form_factor': 'ATX'}, 'Підтримка плат: ATX, Micro-ATX, Mini-ITX\nВентиляторів у комплекті: 2'),
    (K.CASE, 'Fractal Design', 'North', 5699, None, 3,
     {'form_factor': 'ATX'}, 'Підтримка плат: ATX, Micro-ATX, Mini-ITX\nВентиляторів у комплекті: 2'),
]


class Command(BaseCommand):
    help = 'Заповнює магазин демо-категоріями, брендами і товарами та генерує картинки товарів'

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true', help='Не генерувати картинки товарів')

    def handle(self, *args, **options):
        categories = {}
        for order, (kind, name, slug) in enumerate(CATEGORIES):
            categories[kind], _ = Category.objects.update_or_create(
                kind=kind, defaults={'name': name, 'slug': slug, 'order': order})

        generated = 0
        for kind, brand_name, name, price, old_price, stock, compat, specs in PRODUCTS:
            brand, _ = Brand.objects.get_or_create(name=brand_name, defaults={'slug': slugify(brand_name)})
            product, _ = Product.objects.update_or_create(
                slug=slugify(f'{brand_name}-{name}'),
                defaults={
                    'category': categories[kind],
                    'brand': brand,
                    'name': name,
                    'price': Decimal(price),
                    'old_price': Decimal(old_price) if old_price else None,
                    'stock': stock,
                    'specs': specs,
                    'description': f'{brand_name} {name} — {categories[kind].name.lower()} для вашого ПК.',
                    **compat,
                },
            )
            # Картинку перемальовуємо щоразу (ціна чи знижка могли змінитись), але фото, завантажене
            # вручну через адмінку, не чіпаємо
            if not options['no_images'] and generate_product_image(product, force=False):
                generated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Магазин: {Category.objects.count()} категорій, {Brand.objects.count()} брендів, '
            f'{Product.objects.count()} товарів, згенеровано картинок: {generated}'))

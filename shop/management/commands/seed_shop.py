from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

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
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 65},
     'Ядер / потоків: 6 / 12\nЧастота: 3.8–5.1 ГГц\nКеш L3: 32 МБ'),
    (K.CPU, 'AMD', 'Ryzen 7 7800X3D', 15999, 17499, 4,
     {'socket': 'AM5', 'memory_type': 'DDR5', 'power_draw': 120},
     'Ядер / потоків: 8 / 16\nЧастота: 4.2–5.0 ГГц\nКеш L3: 96 МБ (3D V-Cache)'),
    (K.CPU, 'Intel', 'Core i5-12400F', 4599, None, 15,
     {'socket': 'LGA1700', 'power_draw': 117},
     'Ядер / потоків: 6 / 12\nЧастота: 2.5–4.4 ГГц\nВбудована графіка: немає'),
    (K.CPU, 'Intel', 'Core i5-13400F', 6999, None, 10,
     {'socket': 'LGA1700', 'power_draw': 148},
     'Ядер / потоків: 10 / 16\nЧастота: 2.5–4.6 ГГц\nВбудована графіка: немає'),
    (K.CPU, 'Intel', 'Core i7-14700K', 16999, None, 0,
     {'socket': 'LGA1700', 'power_draw': 253},
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
]


class Command(BaseCommand):
    help = 'Заповнює магазин демо-категоріями, брендами і товарами'

    def handle(self, *args, **options):
        categories = {}
        for order, (kind, name, slug) in enumerate(CATEGORIES):
            categories[kind], _ = Category.objects.update_or_create(
                kind=kind, defaults={'name': name, 'slug': slug, 'order': order})

        for kind, brand_name, name, price, old_price, stock, compat, specs in PRODUCTS:
            brand, _ = Brand.objects.get_or_create(name=brand_name, defaults={'slug': slugify(brand_name)})
            Product.objects.update_or_create(
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

        self.stdout.write(self.style.SUCCESS(
            f'Магазин: {Category.objects.count()} категорій, {Brand.objects.count()} брендів, '
            f'{Product.objects.count()} товарів'))

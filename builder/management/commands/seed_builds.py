from django.core.management.base import BaseCommand

from builder.compatibility import check_build, has_errors
from builder.models import Build
from shop.models import Product

# Готові збірки магазину: назва деталі -> слот
PREBUILT = [
    {
        'name': 'ByteBox Office',
        'purpose': Build.Purpose.OFFICE,
        'description': 'Тихий і компактний ПК для навчання, документів і відео. '
                       'Процесор з вбудованою графікою — окрема відеокарта не потрібна.',
        'parts': {'cpu': 'Ryzen 5 7600', 'motherboard': 'PRIME B650M-A',
                  'ram': 'Vengeance DDR5 32 ГБ (2×16) 5600 МГц', 'storage': '980 1 ТБ M.2 NVMe',
                  'psu': 'System Power 10 550W', 'case': 'MATREXX 40'},
    },
    {
        'name': 'ByteBox Gamer',
        'purpose': Build.Purpose.GAMING,
        'description': 'Оптимальний ігровий ПК: впевнені 60+ FPS у Full HD на високих налаштуваннях.',
        'parts': {'cpu': 'Core i5-12400F', 'motherboard': 'B760M DS3H DDR4',
                  'ram': 'FURY Beast DDR4 16 ГБ (2×8) 3200 МГц', 'gpu': 'Dual GeForce RTX 4060 8 ГБ',
                  'storage': 'NV2 2 ТБ M.2 NVMe', 'psu': 'System Power 10 550W', 'case': 'CC560'},
    },
    {
        'name': 'ByteBox Creator',
        'purpose': Build.Purpose.WORKSTATION,
        'description': 'Потужна збірка для ігор у 1440p, монтажу відео і 3D. 8 ядер з 3D V-Cache і 16 ГБ відеопам\'яті.',
        'parts': {'cpu': 'Ryzen 7 7800X3D', 'motherboard': 'PRIME B650M-A',
                  'ram': 'FURY Beast DDR5 32 ГБ (2×16) 6000 МГц', 'gpu': 'Pulse Radeon RX 7800 XT 16 ГБ',
                  'storage': '980 1 ТБ M.2 NVMe', 'psu': 'RM750e 750W', 'case': 'Lancool 216'},
    },
]


class Command(BaseCommand):
    help = 'Створює готові збірки ПК (потрібно спочатку запустити seed_shop)'

    def handle(self, *args, **options):
        for data in PREBUILT:
            parts = {slot: Product.objects.get(name=name) for slot, name in data['parts'].items()}
            build, _ = Build.objects.update_or_create(
                name=data['name'], is_prebuilt=True,
                defaults={'purpose': data['purpose'], 'description': data['description'], **parts},
            )
            report = check_build(build)
            status = 'ПОМИЛКИ СУМІСНОСТІ' if has_errors(report) else 'сумісна'
            self.stdout.write(f'{build.name}: {build.total_price:.0f} грн, ~{build.power_draw} Вт — {status}')
        self.stdout.write(self.style.SUCCESS(f'Готових збірок: {Build.objects.filter(is_prebuilt=True).count()}'))

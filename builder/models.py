from decimal import Decimal

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

from blog.utils import make_slug
from shop.models import Category, Product

K = Category.Kind

# Слоти збірки: (назва поля, тип категорії, підпис, чи обов'язковий)
SLOTS = [
    ('cpu', K.CPU, 'Процесор', True),
    ('motherboard', K.MOTHERBOARD, 'Материнська плата', True),
    ('ram', K.RAM, 'Оперативна пам\'ять', True),
    ('gpu', K.GPU, 'Відеокарта', False),
    ('storage', K.STORAGE, 'Накопичувач', True),
    ('psu', K.PSU, 'Блок живлення', True),
    ('case', K.CASE, 'Корпус', True),
]
SLOT_NAMES = [slot[0] for slot in SLOTS]


def component_field(kind, label, required=True):
    """Поле-посилання на товар певної категорії. limit_choices_to — в адмінці показуються лише товари цієї категорії."""
    return models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=not required,
                             related_name='+', verbose_name=label, limit_choices_to={'category__kind': kind})


class Build(models.Model):
    """Збірка ПК: або готова (від магазину), або збережена користувачем з конфігуратора."""

    class Purpose(models.TextChoices):
        OFFICE = 'office', 'Офіс і навчання'
        GAMING = 'gaming', 'Ігри'
        WORKSTATION = 'workstation', 'Робота з графікою і відео'
        CUSTOM = 'custom', 'Власна збірка'

    name = models.CharField('Назва', max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField('Опис', blank=True)
    purpose = models.CharField('Призначення', max_length=20, choices=Purpose.choices, default=Purpose.CUSTOM)
    image = models.ImageField('Фото', upload_to='builds/', blank=True)
    is_prebuilt = models.BooleanField('Готова збірка магазину', default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='builds', verbose_name='Власник',
                             help_text='Заповнюється для збірок, збережених з конфігуратора')
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    cpu = component_field(K.CPU, 'Процесор')
    motherboard = component_field(K.MOTHERBOARD, 'Материнська плата')
    ram = component_field(K.RAM, 'Оперативна пам\'ять')
    gpu = component_field(K.GPU, 'Відеокарта', required=False)
    storage = component_field(K.STORAGE, 'Накопичувач')
    psu = component_field(K.PSU, 'Блок живлення')
    case = component_field(K.CASE, 'Корпус')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Збірка'
        verbose_name_plural = 'Збірки'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = make_slug(self.name) or 'build'
            slug, n = base, 2
            while Build.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('builder:build_detail', args=[self.slug])

    # ---------- Робота з деталями ----------

    def components(self):
        """Список рядків (слот, підпис, товар або None) у фіксованому порядку."""
        return [(name, label, getattr(self, name)) for name, _, label, _ in SLOTS]

    def products(self):
        return [product for _, _, product in self.components() if product]

    @property
    def total_price(self):
        return sum((p.price for p in self.products()), Decimal('0'))

    @property
    def power_draw(self):
        return sum(p.power_draw for p in self.products() if p.category.kind != K.PSU)

    @property
    def in_stock(self):
        return bool(self.products()) and all(p.in_stock for p in self.products())

    @property
    def image_url(self):
        return self.image.url if self.image else static('img/categories/case.svg')

    def compatibility(self):
        # Імпорт усередині методу, бо compatibility.py сам імпортує SLOTS з цього файлу
        from .compatibility import check_build
        return check_build(self)

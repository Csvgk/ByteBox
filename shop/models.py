from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Категорія комплектуючих: процесори, відеокарти, корпуси..."""

    # Тип категорії потрібен конфігуратору, щоб знати, яку деталь ми перевіряємо
    class Kind(models.TextChoices):
        CPU = 'cpu', 'Процесор'
        MOTHERBOARD = 'motherboard', 'Материнська плата'
        RAM = 'ram', 'Оперативна пам\'ять'
        GPU = 'gpu', 'Відеокарта'
        STORAGE = 'storage', 'Накопичувач'
        PSU = 'psu', 'Блок живлення'
        CASE = 'case', 'Корпус'

    name = models.CharField('Назва', max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    kind = models.CharField('Тип', max_length=20, choices=Kind.choices, unique=True)
    order = models.PositiveSmallIntegerField('Порядок у меню', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:catalog') + f'?category={self.slug}'


class Brand(models.Model):
    name = models.CharField('Назва', max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Одна комплектуюча, яку можна купити окремо або додати у збірку."""

    class Socket(models.TextChoices):
        AM4 = 'AM4', 'AM4'
        AM5 = 'AM5', 'AM5'
        LGA1700 = 'LGA1700', 'LGA1700'

    class MemoryType(models.TextChoices):
        DDR4 = 'DDR4', 'DDR4'
        DDR5 = 'DDR5', 'DDR5'

    class FormFactor(models.TextChoices):
        MATX = 'mATX', 'Micro-ATX'
        ATX = 'ATX', 'ATX'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products',
                                 verbose_name='Категорія')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products', verbose_name='Бренд')
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField('Опис', blank=True)
    image = models.ImageField('Фото', upload_to='products/', blank=True)
    price = models.DecimalField('Ціна, грн', max_digits=10, decimal_places=2)
    old_price = models.DecimalField('Стара ціна, грн', max_digits=10, decimal_places=2, null=True, blank=True,
                                    help_text='Заповніть, якщо на товар діє знижка')
    stock = models.PositiveIntegerField('Залишок на складі', default=0)
    is_active = models.BooleanField('Показувати на сайті', default=True)
    created_at = models.DateTimeField('Додано', auto_now_add=True)

    # Характеристики для перевірки сумісності (заповнюються не для всіх категорій)
    socket = models.CharField('Сокет', max_length=10, choices=Socket.choices, blank=True,
                              help_text='Для процесорів і материнських плат')
    memory_type = models.CharField('Тип пам\'яті', max_length=10, choices=MemoryType.choices, blank=True,
                                   help_text='Для материнських плат і оперативної пам\'яті')
    form_factor = models.CharField('Форм-фактор', max_length=10, choices=FormFactor.choices, blank=True,
                                   help_text='Для плат — розмір плати, для корпусів — найбільша плата, яка влізе')
    power_draw = models.PositiveIntegerField('Споживання, Вт', default=0,
                                             help_text='Скільки енергії споживає деталь')
    psu_power = models.PositiveIntegerField('Потужність БЖ, Вт', default=0, help_text='Тільки для блоків живлення')

    # Інші характеристики просто для показу: кожен рядок у форматі «Назва: значення»
    specs = models.TextField('Інші характеристики', blank=True,
                             help_text='Кожна характеристика з нового рядка, наприклад «Ядер: 6»')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.brand.name}-{self.name}')
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])

    @property
    def image_url(self):
        """Фото товару, а якщо його не завантажили — картинка-заглушка категорії."""
        if self.image:
            return self.image.url
        return static(f'img/categories/{self.category.kind}.svg')

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((1 - self.price / self.old_price) * 100)
        return 0

    def spec_list(self):
        """Повертає всі характеристики списком пар (назва, значення) для таблиці на сторінці товару."""
        result = [('Бренд', self.brand.name)]
        if self.socket:
            result.append(('Сокет', self.socket))
        if self.memory_type:
            result.append(('Тип пам\'яті', self.memory_type))
        if self.form_factor:
            result.append(('Форм-фактор', self.get_form_factor_display()))
        if self.psu_power:
            result.append(('Потужність', f'{self.psu_power} Вт'))
        elif self.power_draw:
            result.append(('Споживання', f'{self.power_draw} Вт'))
        for line in self.specs.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                result.append((key.strip(), value.strip()))
        return result


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Нове'
        CONFIRMED = 'confirmed', 'Підтверджене'
        SHIPPED = 'shipped', 'Відправлене'
        DONE = 'done', 'Виконане'
        CANCELLED = 'cancelled', 'Скасоване'

    class Delivery(models.TextChoices):
        PICKUP = 'pickup', 'Самовивіз з магазину'
        NOVA_POSHTA = 'nova_poshta', 'Нова пошта'
        COURIER = 'courier', 'Кур\'єр'

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='orders', verbose_name='Покупець')
    full_name = models.CharField("Ім'я та прізвище", max_length=150)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    delivery = models.CharField('Доставка', max_length=20, choices=Delivery.choices, default=Delivery.NOVA_POSHTA)
    address = models.CharField('Адреса / відділення', max_length=255, blank=True)
    comment = models.TextField('Коментар', blank=True)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField('Сума, грн', max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f'Замовлення №{self.id}'

    def get_absolute_url(self):
        return reverse('shop:order_detail', args=[self.id])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Замовлення')
    # SET_NULL: якщо товар колись видалять, рядок замовлення залишиться в історії
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items',
                                verbose_name='Товар')
    # Назву і ціну копіюємо: якщо ціна товару зміниться, у старому замовленні залишиться ціна покупки
    name = models.CharField('Назва', max_length=255)
    price = models.DecimalField('Ціна за шт.', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Кількість', default=1)

    class Meta:
        verbose_name = 'Товар у замовленні'
        verbose_name_plural = 'Товари в замовленні'

    def __str__(self):
        return f'{self.name} × {self.quantity}'

    @property
    def total(self):
        return self.price * self.quantity

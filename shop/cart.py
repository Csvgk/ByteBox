from decimal import Decimal

from django.conf import settings

from .models import Product


class Cart:
    """
    Кошик зберігається в сесії користувача — працює навіть без входу в акаунт.

    У сесії лежить простий словник {id товару: кількість}, наприклад {'3': 1, '12': 2}.
    Ключі — рядки, бо сесія зберігається у форматі JSON.
    """

    def __init__(self, request):
        self.session = request.session
        self.items = self.session.setdefault(settings.CART_SESSION_ID, {})

    def add(self, product, quantity=1):
        key = str(product.id)
        new_quantity = self.items.get(key, 0) + quantity
        self.items[key] = max(1, min(new_quantity, product.stock))  # не більше, ніж є на складі
        self.save()

    def set(self, product, quantity):
        if quantity <= 0:
            self.remove(product)
            return
        self.items[str(product.id)] = min(quantity, product.stock)
        self.save()

    def remove(self, product):
        self.items.pop(str(product.id), None)
        self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.items = self.session[settings.CART_SESSION_ID]
        self.save()

    def save(self):
        # Кажемо Django, що сесію змінено і її треба зберегти
        self.session.modified = True

    def __iter__(self):
        """Перебирає рядки кошика: товар, кількість і сума рядка."""
        products = Product.objects.filter(id__in=self.items.keys()).select_related('category', 'brand')
        for product in products:
            quantity = self.items[str(product.id)]
            yield {'product': product, 'quantity': quantity, 'total': product.price * quantity}

    def __len__(self):
        """Загальна кількість штук у кошику (для значка в меню)."""
        return sum(self.items.values())

    def total_price(self):
        return sum((line['total'] for line in self), Decimal('0'))

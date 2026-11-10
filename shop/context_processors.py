from .models import Category


def cart(request):
    """Дані, потрібні на кожній сторінці: категорії для меню (а згодом і кошик)."""
    return {
        'nav_categories': Category.objects.all(),
    }

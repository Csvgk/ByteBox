from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render

from .models import Brand, Category, Product

SORT_OPTIONS = {
    'new': ('-created_at', 'Спочатку нові'),
    'cheap': ('price', 'Спочатку дешеві'),
    'expensive': ('-price', 'Спочатку дорогі'),
    'name': ('name', 'За назвою'),
}


def home(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    context = {
        'categories': Category.objects.all(),
        # Знижки: є стара ціна і вона більша за нову
        'sale_products': products.filter(old_price__gt=F('price'))[:4],
        'new_products': products[:8],
    }
    return render(request, 'shop/home.html', context)


def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')

    # --- Фільтри з адреси, наприклад /catalog/?category=gpu&brand=msi&min_price=10000 ---
    category = None
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query) | Q(description__icontains=query))

    selected_brands = request.GET.getlist('brand')
    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price.isdigit():
        products = products.filter(price__gte=min_price)
    if max_price.isdigit():
        products = products.filter(price__lte=max_price)

    in_stock_only = request.GET.get('in_stock') == '1'
    if in_stock_only:
        products = products.filter(stock__gt=0)

    sort = request.GET.get('sort', 'new')
    if sort not in SORT_OPTIONS:
        sort = 'new'
    products = products.order_by(SORT_OPTIONS[sort][0])

    # --- Пагінація: по 9 товарів на сторінку ---
    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Бренди показуємо тільки ті, що є в обраній категорії
    brands = Brand.objects.all()
    if category:
        brands = brands.filter(products__category=category).distinct()

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'brands': brands,
        'category': category,
        'query': query,
        'selected_brands': selected_brands,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock_only': in_stock_only,
        'sort': sort,
        'sort_options': [(key, label) for key, (_, label) in SORT_OPTIONS.items()],
        'total': paginator.count,
    }
    return render(request, 'shop/catalog.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category', 'brand'), slug=slug, is_active=True)
    related = (Product.objects.filter(category=product.category, is_active=True)
               .exclude(id=product.id).select_related('category', 'brand')[:4])
    return render(request, 'shop/product_detail.html', {'product': product, 'related': related})

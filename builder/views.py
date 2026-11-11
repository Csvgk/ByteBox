from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.cart import Cart
from shop.models import Product

from .compatibility import check_build, compatible_products, has_errors, is_complete, recommended_psu_power
from .forms import BuildForm
from .models import SLOT_NAMES, SLOTS, Build

SESSION_KEY = 'configurator'
EDITING_KEY = 'configurator_editing'


def get_slot(slot):
    for item in SLOTS:
        if item[0] == slot:
            return item
    raise Http404('Такого слота немає')


def draft_build(request):
    draft = request.session.get(SESSION_KEY, {})
    products = Product.objects.filter(id__in=draft.values()).select_related('category', 'brand')
    by_id = {p.id: p for p in products}
    build = Build(name='Моя збірка')
    for slot in SLOT_NAMES:
        setattr(build, slot, by_id.get(draft.get(slot)))
    return build


def save_draft(request, draft):
    request.session[SESSION_KEY] = draft
    request.session.modified = True


def add_build_to_cart(request, build):
    cart = Cart(request)
    missing = []
    for product in build.products():
        if product.in_stock:
            cart.add(product)
        else:
            missing.append(product.name)
    if missing:
        messages.warning(request, 'Немає в наявності, тому не додано: ' + ', '.join(missing))
    messages.success(request, f'Збірку «{build.name}» додано в кошик.')


def get_visible_build(request, slug):
    visible = Q(is_prebuilt=True)
    if request.user.is_authenticated:
        visible |= Q(user=request.user)
    return get_object_or_404(Build.objects.filter(visible), slug=slug)


def build_list(request):
    builds = Build.objects.filter(is_prebuilt=True).select_related(*SLOT_NAMES)
    purpose = request.GET.get('purpose', '')
    if purpose:
        builds = builds.filter(purpose=purpose)
    purposes = [(value, label) for value, label in Build.Purpose.choices if value != Build.Purpose.CUSTOM]
    return render(request, 'builder/build_list.html', {'builds': builds, 'purposes': purposes, 'purpose': purpose})


def build_detail(request, slug):
    build = get_visible_build(request, slug)
    report = build.compatibility()
    return render(request, 'builder/build_detail.html', {'build': build, 'report': report})


@require_POST
def build_add_to_cart(request, slug):
    build = get_visible_build(request, slug)
    add_build_to_cart(request, build)
    return redirect('shop:cart_detail')


@login_required
def build_update(request, slug):
    build = get_object_or_404(Build, slug=slug, user=request.user)
    form = BuildForm(request.POST or None, instance=build)
    if form.is_valid():
        form.save()
        messages.success(request, 'Збірку оновлено.')
        return redirect(build.get_absolute_url())
    return render(request, 'builder/build_form.html', {'form': form, 'build': build})


@login_required
@require_POST
def build_delete(request, slug):
    build = get_object_or_404(Build, slug=slug, user=request.user)
    if request.session.get(EDITING_KEY) == build.id:
        request.session.pop(EDITING_KEY)
    build.delete()
    messages.info(request, f'Збірку «{build.name}» видалено.')
    return redirect('accounts:profile')


def configurator(request):
    build = draft_build(request)
    report = check_build(build) if build.products() else []
    editing = None
    if request.user.is_authenticated and request.session.get(EDITING_KEY):
        editing = Build.objects.filter(id=request.session[EDITING_KEY], user=request.user).first()
    context = {
        'build': build,
        'editing': editing,
        'report': report,
        'has_errors': has_errors(report),
        'complete': is_complete(build),
        'recommended_psu': recommended_psu_power(build.power_draw) if build.power_draw else 0,
    }
    return render(request, 'builder/configurator.html', context)


def configurator_choose(request, slot):
    slot_name, kind, label, _ = get_slot(slot)
    build = draft_build(request)
    setattr(build, slot_name, None)

    all_products = Product.objects.filter(category__kind=kind, is_active=True).select_related('category', 'brand')
    products = compatible_products(kind, build, all_products).order_by('price')
    hidden = all_products.count() - products.count()

    if request.method == 'POST':
        product = get_object_or_404(products, id=request.POST.get('product_id'))
        draft = request.session.get(SESSION_KEY, {})
        draft[slot_name] = product.id
        save_draft(request, draft)
        messages.success(request, f'{label}: обрано {product.brand.name} {product.name}.')
        return redirect('builder:configurator')

    context = {'slot': slot_name, 'label': label, 'products': products, 'hidden': hidden,
               'current_id': request.session.get(SESSION_KEY, {}).get(slot_name)}
    return render(request, 'builder/choose.html', context)


@require_POST
def configurator_remove(request, slot):
    slot_name = get_slot(slot)[0]
    draft = request.session.get(SESSION_KEY, {})
    draft.pop(slot_name, None)
    save_draft(request, draft)
    return redirect('builder:configurator')


@require_POST
def configurator_reset(request):
    save_draft(request, {})
    request.session.pop(EDITING_KEY, None)
    messages.info(request, 'Конфігуратор очищено.')
    return redirect('builder:configurator')


@require_POST
def configurator_to_cart(request):
    build = draft_build(request)
    if has_errors(check_build(build)) or not build.products():
        messages.error(request, 'Спочатку виправте помилки сумісності.')
        return redirect('builder:configurator')
    build.name = 'Збірка з конфігуратора'
    add_build_to_cart(request, build)
    return redirect('shop:cart_detail')


@login_required
@require_POST
def configurator_save(request):
    build = draft_build(request)
    if not build.products():
        messages.error(request, 'Збірка порожня — оберіть хоча б одну деталь.')
        return redirect('builder:configurator')
    editing_id = request.session.get(EDITING_KEY)
    if request.POST.get('mode') == 'update' and editing_id:
        existing = get_object_or_404(Build, id=editing_id, user=request.user)
        for slot in SLOT_NAMES:
            setattr(existing, slot, getattr(build, slot))
        existing.save()
        messages.success(request, f'Зміни в збірці «{existing.name}» збережено.')
        return redirect(existing.get_absolute_url())

    build.name = request.POST.get('name', '').strip()[:120] or 'Моя збірка'
    build.user = request.user
    build.purpose = Build.Purpose.CUSTOM
    build.save()
    request.session[EDITING_KEY] = build.id
    messages.success(request, f'Збірку «{build.name}» збережено в профілі.')
    return redirect(build.get_absolute_url())


@require_POST
def configurator_load(request, slug):
    build = get_visible_build(request, slug)
    save_draft(request, {slot: getattr(build, f'{slot}_id') for slot in SLOT_NAMES if getattr(build, f'{slot}_id')})
    if request.user.is_authenticated and build.user_id == request.user.id:
        request.session[EDITING_KEY] = build.id
    else:
        request.session.pop(EDITING_KEY, None)
    messages.info(request, f'Збірку «{build.name}» відкрито в конфігураторі.')
    return redirect('builder:configurator')

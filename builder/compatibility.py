import math

from shop.models import Category

from .models import SLOTS

FORM_FACTOR_SIZE = {'mATX': 1, 'ATX': 2}

PSU_RESERVE = 1.3


def recommended_psu_power(draw):
    return int(math.ceil(draw * PSU_RESERVE / 50) * 50)


def check_build(build):
    cpu, mb, ram, gpu = build.cpu, build.motherboard, build.ram, build.gpu
    psu, case = build.psu, build.case
    result = []

    for name, _, label, required in SLOTS:
        if required and getattr(build, name) is None:
            result.append(('warning', f'Не обрано: {label.lower()}.'))

    if cpu and mb:
        if cpu.socket != mb.socket:
            result.append(('error', f'Процесор має сокет {cpu.socket}, а плата — {mb.socket}. Вони несумісні.'))
        else:
            result.append(('ok', f'Процесор і плата сумісні (сокет {cpu.socket}).'))

    if ram and mb:
        if ram.memory_type != mb.memory_type:
            result.append(('error', f'Плата підтримує {mb.memory_type}, а обрано пам\'ять {ram.memory_type}.'))
        else:
            result.append(('ok', f'Пам\'ять {ram.memory_type} підходить до плати.'))
    elif ram and cpu and cpu.memory_type and ram.memory_type != cpu.memory_type:
        result.append(('error', f'Процесор працює з {cpu.memory_type}, а обрано {ram.memory_type}.'))

    if mb and case:
        if FORM_FACTOR_SIZE[mb.form_factor] > FORM_FACTOR_SIZE[case.form_factor]:
            result.append(('error', f'Плата {mb.form_factor} не влізе в корпус для {case.form_factor}.'))
        else:
            result.append(('ok', f'Плата {mb.form_factor} поміщається в корпус.'))

    if cpu and not gpu and not cpu.integrated_graphics:
        result.append(('error', f'{cpu.name} не має вбудованої графіки — додайте відеокарту.'))

    if psu:
        draw = build.power_draw
        if psu.psu_power < draw:
            result.append(('error', f'Потужності БЖ ({psu.psu_power} Вт) не вистачить: деталі споживають ~{draw} Вт.'))
        elif psu.psu_power < draw * PSU_RESERVE:
            result.append(('warning', f'БЖ {psu.psu_power} Вт працюватиме на межі. '
                                      f'Рекомендовано від {recommended_psu_power(draw)} Вт.'))
        else:
            result.append(('ok', f'Блока живлення {psu.psu_power} Вт вистачає (споживання ~{draw} Вт).'))

    for product in build.products():
        if not product.in_stock:
            result.append(('warning', f'{product.name} зараз немає в наявності.'))

    return result


def has_errors(messages):
    return any(level == 'error' for level, _ in messages)


def is_complete(build):
    return all(getattr(build, name) is not None for name, _, _, required in SLOTS if required)


def compatible_products(slot_kind, build, queryset):
    K = Category.Kind
    cpu, mb, ram, case = build.cpu, build.motherboard, build.ram, build.case

    if slot_kind == K.CPU:
        if mb:
            queryset = queryset.filter(socket=mb.socket)
    elif slot_kind == K.MOTHERBOARD:
        if cpu:
            queryset = queryset.filter(socket=cpu.socket)
        if ram:
            queryset = queryset.filter(memory_type=ram.memory_type)
        if case:
            allowed = [ff for ff, size in FORM_FACTOR_SIZE.items() if size <= FORM_FACTOR_SIZE[case.form_factor]]
            queryset = queryset.filter(form_factor__in=allowed)
    elif slot_kind == K.RAM:
        if mb:
            queryset = queryset.filter(memory_type=mb.memory_type)
        elif cpu and cpu.memory_type:
            queryset = queryset.filter(memory_type=cpu.memory_type)
    elif slot_kind == K.CASE:
        if mb:
            allowed = [ff for ff, size in FORM_FACTOR_SIZE.items() if size >= FORM_FACTOR_SIZE[mb.form_factor]]
            queryset = queryset.filter(form_factor__in=allowed)
    elif slot_kind == K.PSU:
        queryset = queryset.filter(psu_power__gte=build.power_draw)
    return queryset

"""
Перевірка сумісності деталей збірки.

Кожне правило — проста перевірка двох (або кількох) деталей. Результат — список повідомлень:
  ('error', текст)   — так зібрати не можна (деталі фізично не підходять);
  ('warning', текст) — зібрати можна, але є ризик або незручність;
  ('ok', текст)      — підказка, що перевірка пройдена.
"""
import math

from shop.models import Category

from .models import SLOTS

# Наскільки великою плата може бути в корпусі: ATX-корпус вміщає і ATX, і mATX
FORM_FACTOR_SIZE = {'mATX': 1, 'ATX': 2}

# Рекомендований запас потужності блока живлення
PSU_RESERVE = 1.3


def recommended_psu_power(draw):
    """Споживання × запас, округлене вгору до 50 Вт: 410 Вт -> 550 Вт."""
    return int(math.ceil(draw * PSU_RESERVE / 50) * 50)


def check_build(build):
    cpu, mb, ram, gpu = build.cpu, build.motherboard, build.ram, build.gpu
    psu, case = build.psu, build.case
    result = []

    # 1. Чи всі обов'язкові деталі обрано
    for name, _, label, required in SLOTS:
        if required and getattr(build, name) is None:
            result.append(('warning', f'Не обрано: {label.lower()}.'))

    # 2. Процесор і материнська плата: однаковий сокет
    if cpu and mb:
        if cpu.socket != mb.socket:
            result.append(('error', f'Процесор має сокет {cpu.socket}, а плата — {mb.socket}. Вони несумісні.'))
        else:
            result.append(('ok', f'Процесор і плата сумісні (сокет {cpu.socket}).'))

    # 3. Пам'ять і материнська плата: однаковий тип DDR
    if ram and mb:
        if ram.memory_type != mb.memory_type:
            result.append(('error', f'Плата підтримує {mb.memory_type}, а обрано пам\'ять {ram.memory_type}.'))
        else:
            result.append(('ok', f'Пам\'ять {ram.memory_type} підходить до плати.'))
    elif ram and cpu and cpu.memory_type and ram.memory_type != cpu.memory_type:
        # Плату ще не обрали, але процесори AMD працюють лише з одним типом пам'яті
        result.append(('error', f'Процесор працює з {cpu.memory_type}, а обрано {ram.memory_type}.'))

    # 4. Плата і корпус: форм-фактор
    if mb and case:
        if FORM_FACTOR_SIZE[mb.form_factor] > FORM_FACTOR_SIZE[case.form_factor]:
            result.append(('error', f'Плата {mb.form_factor} не влізе в корпус для {case.form_factor}.'))
        else:
            result.append(('ok', f'Плата {mb.form_factor} поміщається в корпус.'))

    # 5. Відеокарта: без неї потрібна вбудована графіка
    if cpu and not gpu and not cpu.integrated_graphics:
        result.append(('error', f'{cpu.name} не має вбудованої графіки — додайте відеокарту.'))

    # 6. Блок живлення: потужності має вистачати із запасом
    if psu:
        draw = build.power_draw
        if psu.psu_power < draw:
            result.append(('error', f'Потужності БЖ ({psu.psu_power} Вт) не вистачить: деталі споживають ~{draw} Вт.'))
        elif psu.psu_power < draw * PSU_RESERVE:
            result.append(('warning', f'БЖ {psu.psu_power} Вт працюватиме на межі. '
                                      f'Рекомендовано від {recommended_psu_power(draw)} Вт.'))
        else:
            result.append(('ok', f'Блока живлення {psu.psu_power} Вт вистачає (споживання ~{draw} Вт).'))

    # 7. Наявність на складі
    for product in build.products():
        if not product.in_stock:
            result.append(('warning', f'{product.name} зараз немає в наявності.'))

    return result


def has_errors(messages):
    return any(level == 'error' for level, _ in messages)


def is_complete(build):
    return all(getattr(build, name) is not None for name, _, _, required in SLOTS if required)


def compatible_products(slot_kind, build, queryset):
    """
    Залишає в списку лише деталі, сумісні з уже обраними.
    Наприклад, якщо обрано процесор AM5, для слота «плата» лишаться тільки плати AM5.
    """
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

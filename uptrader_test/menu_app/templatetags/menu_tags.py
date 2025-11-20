from django import template
from django.urls import resolve
from django.utils.safestring import mark_safe

from menu_app.models import Menu, MenuItem

register = template.Library()


def _build_tree(items):
    """Построить дерево из queryset (или списка) элементов.

    Ожидается, что все элементы для одного меню уже загружены в память.
    Возвращает список корневых элементов, у каждого элемента добавлен атрибут `children` — список.
    """
    nodes = {}
    children_map = {}
    roots = []

    for item in items:
        item.children = []  # добавляем атрибут для шаблона
        nodes[item.id] = item
        children_map.setdefault(item.parent_id, []).append(item)

    for item in items:
        if item.parent_id is None:
            roots.append(item)
        else:
            parent = nodes.get(item.parent_id)
            if parent:
                parent.children.append(item)
            else:
                # если parent не найден — считаем корнем
                roots.append(item)

    # Сортировка детей по полю order — база уже возвращала ordering, но сделаем явную сортировку
    def sort_children(node):
        node.children.sort(key=lambda x: x.order)
        for c in node.children:
            sort_children(c)

    for r in roots:
        sort_children(r)

    return roots


def _mark_active_and_expanded(roots, request):
    """Отметить активный пункт и развернуть все предков и один уровень под ним.

    Правила:
    - Пункт активен, если его named_url совпадает с разрешённым именем view (resolve(request.path_info).url_name)
      либо если его raw_url (если это путь) совпадает точно с request.path_info.
    - Все предки активного пункта получают флаг `expanded = True`.
    - Кроме того, первый уровень вложенности под активным пунктом тоже получает `expanded = True`.
    """
    from django.urls import resolve, Resolver404

    try:
        match = resolve(request.path_info)
        current_view_name = match.view_name  # this may be like 'app:view'
    except Resolver404:
        current_view_name = None

    # рекурсивный проход по дереву, отмечаем active и expanded
    active_node = None

    def dfs(node, parent_chain):
        nonlocal active_node
        node.active = False
        node.expanded = False

        # determine node url(s)
        node_urlname = node.named_url or ''
        node_raw = node.raw_url or ''

        # active conditions
        is_active = False
        if node_urlname and current_view_name and node_urlname == current_view_name:
            is_active = True
        elif node_raw and node_raw == request.path_info:
            is_active = True

        if is_active:
            node.active = True
            active_node = node
            # mark parents expanded
            for p in parent_chain:
                p.expanded = True

        # visit children
        for child in node.children:
            dfs(child, parent_chain + [node])

    for root in roots:
        dfs(root, [])

    # если найден активный — развернуть его (expanded = True) и первый уровень детей
    if active_node is not None:
        active_node.expanded = True
        for c in getattr(active_node, 'children', []):
            c.expanded = True


@register.inclusion_tag('menu/menu.html', takes_context=True)
def draw_menu(context, menu_name):
    request = context.get('request')

    # ---- 1 SQL QUERY ----
    # Получаем ВСЕ пункты меню + сам объект Menu через select_related('menu')
    items_qs = (
        MenuItem.objects
        .filter(menu__name=menu_name)
        .select_related('menu')
        .order_by('parent_id', 'order')
    )
    items = list(items_qs)   # выполнение queryset → один единственный запрос

    # Извлекаем Menu из первого элемента или None
    menu = items[0].menu if items else None

    # Построение дерева в памяти
    roots = _build_tree(items)

    # Отметить active / expanded
    if request is not None:
        _mark_active_and_expanded(roots, request)

    return {
        'menu': menu,
        'items': roots,
        'request': request,
    }

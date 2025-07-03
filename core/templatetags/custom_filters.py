from django import template
from django.db.models import Avg

register = template.Library()

@register.filter
def avg(items, attr_name):
    """Listedeki nesnelerin belirtilen attribute ortalamasını alır"""
    values = [getattr(item, attr_name, 0) for item in items if hasattr(item, attr_name)]
    return sum(values) / len(values) if values else 0


@register.filter
def sum_items(items, attr_name):
    """Listedeki nesnelerin belirtilen attribute toplamını alır"""
    try:
        return sum(getattr(item, attr_name, 0) for item in items)
    except (TypeError, AttributeError):
        return 0
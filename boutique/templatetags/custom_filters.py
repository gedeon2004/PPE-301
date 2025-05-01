from django import template

register = template.Library()

@register.filter
def batch(list_, size):
    """Divise une liste en sous-listes de taille donnée"""
    return [list_[i:i + size] for i in range(0, len(list_), size)]
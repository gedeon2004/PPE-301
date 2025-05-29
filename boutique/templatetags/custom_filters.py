from django import template

register = template.Library()

@register.filter
def batch(list_, size):
    """Divise une liste en sous-listes de taille donnée."""
    return [list_[i:i + size] for i in range(0, len(list_), size)]

@register.filter(name='add_class')
def add_class(field, css_class):
    """Ajoute une classe CSS à un champ de formulaire."""
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='attr')
def attr(field, attrs):
    """Ajoute des attributs spécifiés à un champ de formulaire."""
    if hasattr(field, 'as_widget'):
        attrs_dict = dict(item.split(':') for item in attrs.split(','))
        return field.as_widget(attrs=attrs_dict)
    return field  # Return the original field if it doesn't have as_widget
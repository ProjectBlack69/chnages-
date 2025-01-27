from django import template

register = template.Library()

@register.filter
def range_filter(value):
    return range(1, value + 1)

@register.filter
def is_half_star(value, i):
    # Check if the rating is a half star at position 'i'
    if value >= i and value < i + 1:
        return True
    return False

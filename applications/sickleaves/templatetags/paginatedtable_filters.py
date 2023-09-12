from django import template

register = template.Library()


@register.filter(name='items_numbers')
def items_numbers(start_num, end_num):
    return range(start_num, end_num+1)

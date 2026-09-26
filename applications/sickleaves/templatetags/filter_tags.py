from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters based on the current request's
    parameters, with the specified GET parameters added or changed.
    """
    d = context['request'].GET.copy()

    d.pop('csrfmiddlewaretoken', None)

    for k, v in kwargs.items():
        d[k] = v

    for k in [k for k, v in d.items() if not v]:
        del d[k]

    return d.urlencode()

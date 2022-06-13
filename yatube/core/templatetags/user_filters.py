from django import template, forms


register = template.Library()


@register.filter
def addclass(field: forms.fields.Field, css):
    return field.as_widget(attrs={'class': css})

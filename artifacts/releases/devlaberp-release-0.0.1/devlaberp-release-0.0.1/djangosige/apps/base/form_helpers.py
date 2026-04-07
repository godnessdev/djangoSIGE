# -*- coding: utf-8 -*-


def get_selected_model_choice_value(form, field_name):
    if getattr(form, 'is_bound', False):
        return form.data.get(form.add_prefix(field_name)) or None
    instance = getattr(form, 'instance', None)
    return getattr(instance, '%s_id' % field_name, None) if instance else None


def configure_remote_model_choice_field(field, queryset, lookup_url, placeholder, selected_value=None):
    field.queryset = queryset

    empty_label = getattr(field, 'empty_label', None) or '----------'
    selected_instance = queryset.filter(pk=selected_value).first() if selected_value else None

    field.choices = [('', empty_label)]
    if selected_instance:
        field.choices.append((selected_instance.pk, str(selected_instance)))

    widget_classes = field.widget.attrs.get('class', '').split()
    if 'js-remote-select' not in widget_classes:
        widget_classes.append('js-remote-select')

    field.widget.attrs.update({
        'class': ' '.join(css_class for css_class in widget_classes if css_class).strip(),
        'data-lookup-url': str(lookup_url),
        'data-lookup-placeholder': placeholder,
        'autocomplete': 'off',
    })

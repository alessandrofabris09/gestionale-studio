from django import template

register = template.Library()


@register.filter
def can_view_parcelle(user):
    return True


@register.filter
def can_use_agenda(user):
    return True


@register.filter
def can_manage_subscription(user):
    return True


@register.filter
def can_manage_backup(user):
    return True


@register.filter
def has_group(user, group_name):

    return user.groups.filter(
        name=group_name
    ).exists()
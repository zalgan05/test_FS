from django.contrib import admin
# from phonenumber_field.formfields import PhoneNumberField
# from phonenumber_field.widgets import PhoneNumberPrefixWidget

from .models import Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'code_operator', 'tag', 'timezone')
    # formfield_overrides = {
    #     PhoneNumberField: {'widget': PhoneNumberPrefixWidget},
    # }


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'text',
        'start_date',
        'end_date',
        'filter_tag',
        'filter_code_operator'
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    pass

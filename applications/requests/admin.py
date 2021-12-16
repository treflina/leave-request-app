from django.contrib import admin
from .models import Request

class RequestsAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'work_date',
        'start_date',
        'days',
        'status',
        'send_to_person',
    )

    search_fields = ('author__last_name', 'author__first_name')
    list_filter = ('type', )


admin.site.register(Request, RequestsAdmin)
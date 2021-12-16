from django.contrib import admin


from .models import User

class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'position',
        'role',
        'workplace',
        'working_hours',
    )


    search_fields = ('last_name', )
    list_filter = ('role', 'workplace',)


admin.site.register(User, EmployeeAdmin)




from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from nnmware.apps.board.models import Board, BoardCategory
from nnmware.core.admin import TreeAdmin, AbstractDataAdmin


class BoardCategoryAdmin(TreeAdmin):
    fieldsets = (
        (_("Main"), {"fields": [("name", "slug"), ("parent", "login_required",)]}),
        (_("Description"), {"classes": ("collapse",),
                            "fields": [("description",), ("ordering", "rootnode"), ('admins', )]}),
    )


class BoardAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Board'), {'fields': [('user', 'enabled', 'category', 'region')]}),
        (_('Content'), {'fields': [('name',), ('description',)]}),
        (_('Meta'), {'fields': [('created_date', 'updated_date')]}),
    )
    list_display = ('user', 'created_date', 'name')
    list_filter = ('created_date',)
    date_hierarchy = 'created_date'
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_date', 'updated_date')

admin.site.register(Board, BoardAdmin)
admin.site.register(BoardCategory, BoardCategoryAdmin)

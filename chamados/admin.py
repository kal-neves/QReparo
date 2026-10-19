from django.contrib import admin
from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nome', 'outro']
    search_fields = ['nome']
    actions = None

    def get_readonly_fields(self, request, obj=None):
        return ['outro'] if obj else []

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.outro) and super().has_delete_permission(request, obj)


# Chamados não são registrados: não há edição, exclusão, inline ou auditoria
# de texto livre capaz de contornar a regra de descarte do modelo.

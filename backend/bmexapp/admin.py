"""
Django admin configuration for masses app
"""

from django.contrib import admin
from .models import TheoreticalModel, Nucleus, MassRecord


@admin.register(TheoreticalModel)
class TheoreticalModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'full_name', 'version', 'created_at']
    search_fields = ['name', 'full_name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Nucleus)
class NucleusAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'Z', 'N', 'A', 'element_symbol', 'element_name']
    list_filter = ['Z']
    search_fields = ['element_symbol', 'element_name']
    ordering = ['Z', 'N']


@admin.register(MassRecord)
class MassRecordAdmin(admin.ModelAdmin):
    list_display = ['nucleus', 'model', 'BE', 'MassExcess', 'created_at']
    list_filter = ['model']
    search_fields = ['nucleus__element_symbol']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['nucleus', 'model']

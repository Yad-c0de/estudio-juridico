from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Cliente, EstadoCaso, Caso, Expediente, Pago, PerfilAbogado


class PerfilAbogadoInline(admin.StackedInline):
    model = PerfilAbogado
    can_delete = False
    verbose_name_plural = "Perfil de abogado"


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilAbogadoInline]
    list_display = ("username", "first_name", "last_name", "email", "is_staff")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombres", "documento", "telefono", "correo")
    search_fields = ("nombres", "documento", "correo")


@admin.register(EstadoCaso)
class EstadoCasoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "permite_pagos")
    list_filter = ("permite_pagos",)
    search_fields = ("nombre",)

class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 1


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "cliente", "estado", "total", "fecha_inicio")
    list_filter = ("estado", "fecha_inicio", "cliente")
    search_fields = ("codigo", "titulo", "cliente__nombres", "cliente__documento")
    filter_horizontal = ("abogados",)
    list_select_related = ("cliente", "estado")
    inlines = [ExpedienteInline, PagoInline]

    @admin.display(description="Total pagado (S/)")
    def total(self, obj):
        return obj.total_pagado()


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ("numero", "juzgado", "fecha_presentacion", "caso")
    search_fields = ("numero", "juzgado", "caso__codigo")
    list_filter = ("juzgado", "fecha_presentacion")
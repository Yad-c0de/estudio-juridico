from django.db import models
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class Cliente(models.Model):
    nombres = models.CharField(max_length=150)
    documento = models.CharField("DNI o RUC", max_length=11, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nombres} ({self.documento})"


class EstadoCaso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    permite_pagos = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="casos"
    )
    estado = models.ForeignKey(
        EstadoCaso, on_delete=models.PROTECT, related_name="casos"
    )
    abogados = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="casos_asignados"
    )

    def total_pagado(self):
        total = self.pagos.aggregate(total=Sum("monto"))["total"]
        return total or Decimal("0")

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"


class Expediente(models.Model):
    numero = models.CharField(max_length=30, unique=True)
    juzgado = models.CharField(max_length=150)
    fecha_presentacion = models.DateField()
    caso = models.ForeignKey(
        Caso, on_delete=models.CASCADE, related_name="expedientes"
    )
    documento = models.FileField(upload_to="expedientes/", blank=True)

    def __str__(self):
        return f"Exp. {self.numero} - {self.juzgado}"


class Pago(models.Model):
    caso = models.ForeignKey(
        Caso, on_delete=models.PROTECT, related_name="pagos"
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=200, blank=True)

    def clean(self):
        if self.caso_id and not self.caso.estado.permite_pagos:
            raise ValidationError(
                f"El caso está en estado '{self.caso.estado}' y no admite pagos."
            )

    def __str__(self):
        return f"Pago de S/ {self.monto} - {self.caso.codigo}"


class PerfilAbogado(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    numero_colegiatura = models.CharField(max_length=20)
    especialidad = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - CAL {self.numero_colegiatura}"

from django.shortcuts import render

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClienteForm
from .models import Caso, Cliente, EstadoCaso, Expediente, Pago

def lista_clientes(request):
    clientes = Cliente.objects.all().order_by("nombres")
    return render(request, "casos/cliente_lista.html", {"clientes": clientes})


def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect("casos:lista_clientes")
    else:
        form = ClienteForm()
    return render(request, "casos/cliente_form.html", {"form": form, "titulo": "Nuevo cliente"})


def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            return redirect("casos:lista_clientes")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "casos/cliente_form.html", {"form": form, "titulo": "Editar cliente"})


def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(request, "Cliente eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar: el cliente tiene casos registrados.",
            )
        return redirect("casos:lista_clientes")
    return render(request, "casos/cliente_eliminar.html", {"cliente": cliente})


def lista_casos(request):
    casos = (
        Caso.objects.select_related("cliente", "estado")
        .prefetch_related("abogados")
        .order_by("codigo")
    )

    estado_id = None
    guardar_cookie = False
    borrar_cookie = False

    if "estado" in request.GET:
        valor = request.GET["estado"]
        if valor.isdigit():
            estado_id = int(valor)
            guardar_cookie = True
        else:
            borrar_cookie = True          # ?estado= vacío = ver todos
    else:
        valor = request.COOKIES.get("ultimo_estado", "")
        if valor.isdigit():
            estado_id = int(valor)        # aplica el último estado consultado

    if estado_id is not None:
        casos = casos.filter(estado_id=estado_id)

    response = render(
        request,
        "casos/lista_casos.html",
        {
            "casos": casos,
            "estados": EstadoCaso.objects.all(),
            "estado_actual": estado_id,
        },
    )
    if guardar_cookie:
        response.set_cookie("ultimo_estado", str(estado_id), max_age=60 * 60 * 24 * 30)
    elif borrar_cookie:
        response.delete_cookie("ultimo_estado")
    return response

def detalle_caso(request, id):
    caso = get_object_or_404(Caso, pk=id)
    return render(
        request,
        "casos/detalle_caso.html",
        {
            "caso": caso,
            "expedientes": caso.expedientes.all(),
            "pagos": caso.pagos.order_by("fecha"),
        },
    )

def registrar_pago(request, id):
    caso = get_object_or_404(Caso, pk=id)
    if request.method != "POST":
        return redirect("casos:detalle_caso", id=caso.id)

    try:
        monto = Decimal(request.POST.get("monto", "").strip().replace(",", "."))
        if not monto.is_finite() or monto <= 0:
            raise InvalidOperation
    except InvalidOperation:
        messages.error(request, "Ingrese un monto válido mayor que cero.")
        return redirect("casos:detalle_caso", id=caso.id)

    pago = Pago(
        caso=caso,
        monto=monto,
        fecha=timezone.localdate(),
        descripcion=request.POST.get("descripcion", "").strip(),
    )
    try:
        pago.full_clean()          # ejecuta Pago.clean(): regla del estado
    except ValidationError as e:
        messages.error(request, "Pago rechazado: " + " ".join(e.messages))
    else:
        pago.save()
        messages.success(request, f"Pago de S/ {monto:.2f} registrado correctamente.")
    return redirect("casos:detalle_caso", id=caso.id)


def subir_documento(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    if request.method == "POST":
        archivo = request.FILES.get("documento")
        if archivo:
            expediente.documento = archivo
            expediente.save()
            messages.success(request, f"Documento subido al expediente {expediente.numero}.")
        else:
            messages.error(request, "Seleccione un archivo para subir.")
    return redirect("casos:detalle_caso", id=expediente.caso_id)


def api_caso(request, id):
    caso = get_object_or_404(
        Caso.objects.select_related("cliente", "estado"), pk=id
    )
    data = {
        "codigo": caso.codigo,
        "cliente": caso.cliente.nombres,
        "estado": caso.estado.nombre,
        "abogados": [a.get_full_name() or a.username for a in caso.abogados.all()],
        "numero_expedientes": caso.expedientes.count(),
        "total_pagado": float(caso.total_pagado()),
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})

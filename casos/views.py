from django.shortcuts import render

from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Caso, Cliente

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
    return render(request, "casos/lista_casos.html", {"casos": casos})


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

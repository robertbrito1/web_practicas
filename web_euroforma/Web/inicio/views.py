from django.shortcuts import render
from django.shortcuts import render
from .models import Profesor
from django.shortcuts import get_object_or_404


def inicio(request):
    return render(request, 'inicio.html')

def equipo(request):
    profesores = Profesor.objects.all()
    return render(request, 'equipo.html', {'profesores': profesores})
def profesor_detalle(request, slug):
    profesor = get_object_or_404(Profesor, slug=slug)
    return render(request, 'profesores/profesor1.html', {'profesor': profesor})

def nosotros(request):
    return render(request, 'nosotros.html')


def preguntas(request):
    return render(request, 'preguntas.html')
def politicas(request):
    return render(request, 'politicas.html')

def avisos(request):
    return render(request, 'avisos.html')
def cockies(request):
    return render(request, 'cockies.html')

from django.shortcuts import render
from django.shortcuts import render

def inicio(request):
    return render(request, 'inicio.html')

def nosotros(request):
    return render(request, 'nosotros.html')

def equipo(request):
    return render(request, 'equipo.html')
    
def preguntas(request):
    return render(request, 'preguntas.html')
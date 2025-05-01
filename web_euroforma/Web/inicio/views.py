from django.shortcuts import render
from django.shortcuts import render

def inicio(request):
    return render(request, 'inicio.html')

def profesor1(request):
    return render(request, 'profesores/profesor1.html')

def profesor2(request):
    return render(request, 'profesores/profesor2.html')

def profesor3(request):
    return render(request, 'profesores/profesor3.html')

def profesor4(request):
    return render(request, 'profesores/profesor4.html')

def profesor5(request):
    return render(request, 'profesores/profesor5.html')

def profesor6(request):
    return render(request, 'profesores/profesor6.html')

def profesor7(request):
    return render(request, 'profesores/profesor7.html')

def profesor8(request):
    return render(request, 'profesores/profesor8.html')

def nosotros(request):
    return render(request, 'nosotros.html')

def equipo(request):
    return render(request, 'equipo.html')
    
def preguntas(request):
    return render(request, 'preguntas.html')
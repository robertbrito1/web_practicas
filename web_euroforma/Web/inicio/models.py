from django.db import models




class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, default='Sin apellido')
    slug = models.SlugField(unique=True)
    experiencia = models.IntegerField()
    asignaturas = models.CharField(max_length=255)
    fp = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='imagenes_profesores/')
    centros_trabajo = models.TextField()
    formacion = models.TextField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

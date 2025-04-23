from django.db import models

class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    numero_tlf = models.CharField(max_length=15)
    asunto = models.TextField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
# Create your models here.

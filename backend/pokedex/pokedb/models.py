from django.db import models

# Create your models here.

class Pokemon(models.Model):
    entry = models.IntegerField(null=True, unique=True)
    name = models.CharField(max_length=30)
    description = models.TextField(default="No description available")  # Default value
    images = models.TextField(default="")

    def __str__(self):
        return f"{self.entry} {self.name}"


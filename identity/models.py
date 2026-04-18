from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avatar_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username

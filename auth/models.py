from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "main_role"
        managed = False

    def __str__(self) -> str:
        return self.name


class User(models.Model):
    name = models.CharField(max_length=150)
    token = models.CharField(max_length=255, unique=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    phone = models.CharField(max_length=50, null=True, blank=True)
    avatar_path = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "main_user"
        managed = False

    def __str__(self) -> str:
        return self.name

    @property
    def is_authenticated(self):
        return True

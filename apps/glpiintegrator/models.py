from django.db import models
from django.contrib.auth.models import User

class GlpiProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='glpi_profile')
    glpi_id = models.IntegerField(unique=True, db_index=True)
    last_sync = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GLPI ID {self.glpi_id} linked to {self.user.username}"

from django.db import models

class Config(models.Model):
    interval = models.DurationField(
        help_text='Intervalo de tempo entre cada solicitação.'
    )

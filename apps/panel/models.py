from django.db import models

class DashboardSettingsManager(models.Manager):
    def get_settings(self):
        # get_or_create garante que sempre teremos nosso objeto de ID=1
        # Se não existir, ele o cria com os valores padrão.
        settings, created = self.get_or_create(
            id=1,
            defaults={
                'fetch_interval_seconds': 30,
                'notification_sound_url': 'https://example.com/sounds/default_beep.mp3'
            }
        )
        return settings

class DashboardSettings(models.Model):

    fetch_interval_seconds = models.PositiveIntegerField(
        default=30,
        verbose_name="Intervalo de Busca (em segundos)",
        help_text="Tempo que o dashboard leva para buscar novos chamados. (Ex: 30)"
    )
    
    notification_sound_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="URL do Som de Notificação",
        help_text="Cole a URL completa de um arquivo de áudio online (ex: .mp3, .wav)",
        default='https://example.com/sounds/default_beep.mp3'
    )

    # ... (No futuro, você pode adicionar mais campos aqui)
    # volume = models.PositiveIntegerField(default=100, ...)
    # show_popups = models.BooleanField(default=True, ...)

    # Anexa o manager customizado
    objects = DashboardSettingsManager()

    def save(self, *args, **kwargs):
        # Garante que o ID seja sempre 1
        self.pk = 1
        super(DashboardSettings, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Impede que este registro seja deletado
        pass 

    class Meta:
        verbose_name = "Configurações do Dashboard"
        verbose_name_plural = "Configurações do Dashboard"

class Display(models.Model):
    SCREEN_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('tickets', 'Tickets'),
        ('projects', 'Projetos'),
        ('remote', 'Controle Remoto'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Display (Client ID)")
    channel_name = models.CharField(max_length=255, verbose_name="Canal WebSocket")
    current_screen = models.CharField(max_length=50, choices=SCREEN_CHOICES, default='tickets', verbose_name="Tela Atual")
    available_screens = models.JSONField(default=list, verbose_name="Telas Disponíveis")
    connected_at = models.DateTimeField(auto_now_add=True, verbose_name="Conectado em")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Visto por último em")

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        # Check if current_screen changed
        if self.pk:
            try:
                old_instance = Display.objects.get(pk=self.pk)
                if old_instance.current_screen != self.current_screen:
                    # Send update to client
                    from asgiref.sync import async_to_sync
                    from channels.layers import get_channel_layer
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.send)(
                        self.channel_name,
                        {
                            "type": "display.control",
                            "command": "change_screen",
                            "screen": self.current_screen,
                        }
                    )
            except Display.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Display Conectado"
        verbose_name_plural = "Displays Conectados"

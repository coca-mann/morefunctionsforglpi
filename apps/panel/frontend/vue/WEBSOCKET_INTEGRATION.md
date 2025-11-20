# Integração com Django Channels - Guia Completo

Este documento descreve como integrar o painel Vue.js 3 com Django Channels para comunicação via WebSocket.

## 📋 Estrutura de Dados

### Campos que o Backend Deve Enviar

#### **1. Tickets Update**
```json
{
  "type": "tickets_update",
  "data": [
    {
      "id": "123",
      "title": "Servidor Web - Falha de Disco",
      "description": "Disco rígido apresentando erros",
      "assignedTo": "João Silva",
      "priority": "critical",
      "status": "open",
      "createdAt": "2025-11-18T10:30:00Z",
      "updatedAt": "2025-11-18T10:30:00Z",
      "entity": "Servidor Principal",
      "urgency": "Muito Alta"
    }
  ],
  "counters": {
    "critical": 2,
    "high": 3,
    "medium": 5,
    "low": 1,
    "total": 11
  },
  "timestamp": "2025-11-18T10:35:00Z"
}
```

#### **2. Projects Update**
```json
{
  "type": "projects_update",
  "data": [
    {
      "id": "proj-001",
      "name": "Migração para Cloud",
      "responsible": "Ana Oliveira",
      "status": "in_progress",
      "completed": 45,
      "inProgress": 12,
      "pending": 8,
      "progress": 82,
      "dueDate": "2025-12-15",
      "updatedAt": "2025-11-18T10:30:00Z"
    }
  ],
  "timestamp": "2025-11-18T10:35:00Z"
}
```

#### **3. Dashboard Update**
```json
{
  "type": "dashboard_update",
  "kpis": {
    "openTickets": 12,
    "avgResponseTime": "2h 30m",
    "resolutionRate": 92,
    "customerSatisfaction": 88,
    "surveyCount": 47
  },
  "technicians": [
    {
      "id": "tech-001",
      "name": "João Silva",
      "role": "technician",
      "specialization": "Hardware",
      "available": true,
      "assignedCount": 3
    }
  ],
  "analysts": [
    {
      "id": "analyst-001",
      "name": "Carlos Mendes",
      "role": "analyst",
      "specialization": "Infraestrutura",
      "available": true,
      "assignedCount": 2
    }
  ],
  "recentActivity": [
    {
      "id": "activity-001",
      "timestamp": "2025-11-18T14:35:00Z",
      "description": "Ticket #005 atribuído a Carlos Mendes",
      "type": "assignment",
      "severity": "medium"
    }
  ],
  "timestamp": "2025-11-18T10:35:00Z"
}
```

#### **4. New Ticket Alert**
```json
{
  "type": "new_ticket_alert",
  "data": {
    "id": "124",
    "title": "Impressora Rede - Sem Conectividade",
    "severity": "high",
    "soundUrl": "https://seu-servidor.com/static/sounds/notification.mp3"
  },
  "timestamp": "2025-11-18T10:35:00Z"
}
```

#### **5. Project Update Alert**
```json
{
  "type": "project_update_alert",
  "data": {
    "id": "proj-001",
    "title": "Migração para Cloud",
    "severity": "medium",
    "soundUrl": "https://seu-servidor.com/static/sounds/notification.mp3"
  },
  "timestamp": "2025-11-18T10:35:00Z"
}
```

#### **6. Critical Alert**
```json
{
  "type": "critical_alert",
  "data": {
    "id": "critical-001",
    "title": "Servidor Principal Offline",
    "severity": "critical",
    "soundUrl": "https://seu-servidor.com/static/sounds/critical.mp3"
  },
  "timestamp": "2025-11-18T10:35:00Z"
}
```

## 🔌 Mensagens Recebidas do Frontend

### Remote Switch Command
```json
{
  "type": "remote_switch",
  "target": "tickets",
  "timestamp": "2025-11-18T10:35:00Z"
}
```

### Identification Message
```json
{
  "type": "identify",
  "clientId": "Kiosk-ABCDE",
  "timestamp": "2025-11-18T10:35:00Z"
}
```

### Request Data Refresh
```json
{
  "type": "request_data",
  "view": "tickets",
  "timestamp": "2025-11-18T10:35:00Z"
}
```

## 🚀 Implementação no Django Channels

### 1. Consumer Básico

```python
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Ticket, Project
from .serializers import TicketSerializer, ProjectSerializer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.client_id = None
        await self.accept()
        print(f"[WebSocket] Cliente conectado")

    async def disconnect(self, close_code):
        print(f"[WebSocket] Cliente desconectado: {self.client_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'identify':
                self.client_id = data.get('clientId')
                print(f"[WebSocket] Cliente identificado: {self.client_id}")
                
                # Envia dados iniciais
                await self.send_initial_data()

            elif message_type == 'request_data':
                view = data.get('view')
                await self.handle_data_request(view)

            elif message_type == 'remote_switch':
                # Processa comando remoto se necessário
                target = data.get('target')
                print(f"[WebSocket] Comando remoto: {target}")

        except json.JSONDecodeError:
            await self.send_error("Erro ao decodificar JSON")

    async def send_initial_data(self):
        """Envia dados iniciais ao conectar"""
        await self.send_tickets_update()
        await self.send_projects_update()
        await self.send_dashboard_update()

    async def send_tickets_update(self):
        """Envia atualização de tickets"""
        tickets = await self.get_tickets()
        counters = await self.get_ticket_counters()
        
        await self.send(text_data=json.dumps({
            'type': 'tickets_update',
            'data': tickets,
            'counters': counters,
            'timestamp': self.get_timestamp()
        }))

    async def send_projects_update(self):
        """Envia atualização de projetos"""
        projects = await self.get_projects()
        
        await self.send(text_data=json.dumps({
            'type': 'projects_update',
            'data': projects,
            'timestamp': self.get_timestamp()
        }))

    async def send_dashboard_update(self):
        """Envia atualização do dashboard"""
        kpis = await self.get_dashboard_kpis()
        technicians = await self.get_technicians()
        analysts = await self.get_analysts()
        activities = await self.get_recent_activities()
        
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'kpis': kpis,
            'technicians': technicians,
            'analysts': analysts,
            'recentActivity': activities,
            'timestamp': self.get_timestamp()
        }))

    async def send_new_ticket_alert(self, ticket_id, sound_url=None):
        """Envia alerta de novo ticket"""
        ticket = await self.get_ticket(ticket_id)
        
        await self.send(text_data=json.dumps({
            'type': 'new_ticket_alert',
            'data': {
                'id': ticket['id'],
                'title': ticket['title'],
                'severity': ticket['priority'],
                'soundUrl': sound_url or '/static/sounds/notification.mp3'
            },
            'timestamp': self.get_timestamp()
        }))

    async def send_error(self, message):
        """Envia mensagem de erro"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # ============ MÉTODOS AUXILIARES ============

    @sync_to_async
    def get_tickets(self):
        """Busca todos os tickets"""
        tickets = Ticket.objects.filter(status__in=['open', 'in_progress'])
        return TicketSerializer(tickets, many=True).data

    @sync_to_async
    def get_ticket(self, ticket_id):
        """Busca um ticket específico"""
        ticket = Ticket.objects.get(id=ticket_id)
        return TicketSerializer(ticket).data

    @sync_to_async
    def get_ticket_counters(self):
        """Conta tickets por prioridade"""
        return {
            'critical': Ticket.objects.filter(priority='critical', status='open').count(),
            'high': Ticket.objects.filter(priority='high', status='open').count(),
            'medium': Ticket.objects.filter(priority='medium', status='open').count(),
            'low': Ticket.objects.filter(priority='low', status='open').count(),
            'total': Ticket.objects.filter(status__in=['open', 'in_progress']).count(),
        }

    @sync_to_async
    def get_projects(self):
        """Busca todos os projetos"""
        projects = Project.objects.filter(status__in=['planning', 'in_progress', 'testing'])
        return ProjectSerializer(projects, many=True).data

    @sync_to_async
    def get_dashboard_kpis(self):
        """Calcula KPIs do dashboard"""
        open_tickets = Ticket.objects.filter(status='open').count()
        # Calcule os demais KPIs conforme sua lógica
        return {
            'openTickets': open_tickets,
            'avgResponseTime': '2h 30m',
            'resolutionRate': 92,
            'customerSatisfaction': 88,
            'surveyCount': 47
        }

    @sync_to_async
    def get_technicians(self):
        """Busca técnicos de manutenção"""
        # Implemente conforme seu modelo
        return []

    @sync_to_async
    def get_analysts(self):
        """Busca analistas de sistemas"""
        # Implemente conforme seu modelo
        return []

    @sync_to_async
    def get_recent_activities(self):
        """Busca atividades recentes"""
        # Implemente conforme seu modelo
        return []

    def get_timestamp(self):
        """Retorna timestamp ISO 8601"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    async def handle_data_request(self, view):
        """Processa requisição de dados específica"""
        if view == 'tickets':
            await self.send_tickets_update()
        elif view == 'projects':
            await self.send_projects_update()
        elif view == 'dashboard':
            await self.send_dashboard_update()
```

### 2. Routing

```python
# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard_control/$', consumers.DashboardConsumer.as_asgi()),
]
```

### 3. ASGI Configuration

```python
# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
```

## 📡 Envio de Dados Periódicos

### Opção 1: Polling Periódico

```python
import asyncio

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.client_id = None
        await self.accept()
        
        # Inicia task de polling
        self.polling_task = asyncio.create_task(self.periodic_update())

    async def disconnect(self, close_code):
        if hasattr(self, 'polling_task'):
            self.polling_task.cancel()

    async def periodic_update(self):
        """Envia atualizações a cada 30 segundos"""
        while True:
            try:
                await asyncio.sleep(30)
                await self.send_tickets_update()
                await self.send_projects_update()
                await self.send_dashboard_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erro no polling: {e}")
```

### Opção 2: Signals (On Change)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Ticket)
def ticket_updated(sender, instance, created, **kwargs):
    """Notifica clientes quando um ticket é criado/atualizado"""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'dashboard_group',
        {
            'type': 'ticket_update',
            'ticket_id': instance.id,
            'sound_url': '/static/sounds/notification.mp3'
        }
    )
```

## 🧪 Testando no Frontend

1. **Abra o painel** em http://localhost:3000
2. **Clique no ícone de bug** (roxo) na sidebar para abrir o **Painel de Teste**
3. **Simule eventos**:
   - Novo Ticket: Preencha título e prioridade, clique "Enviar Novo Ticket"
   - Atualização de Projeto: Preencha nome e progresso, clique "Enviar Atualização"
   - Som: Preencha URL do som e clique "Tocar Som"
   - Comando Remoto: Selecione tela e clique "Enviar Comando"

## 📊 Campos Obrigatórios por View

### TicketsView
- `id`, `title`, `assignedTo`, `priority`, `status`, `createdAt`

### ProjectsView
- `id`, `name`, `responsible`, `status`, `completed`, `inProgress`, `pending`, `progress`, `dueDate`

### DashboardView
- `kpis` (openTickets, avgResponseTime, resolutionRate, customerSatisfaction, surveyCount)
- `technicians` (name, specialization, available, assignedCount)
- `analysts` (name, specialization, available, assignedCount)
- `recentActivity` (timestamp, description, type)

## 🔐 Segurança

- Sempre valide os dados recebidos do frontend
- Implemente autenticação/autorização adequada
- Use HTTPS/WSS em produção
- Implemente rate limiting para evitar abuso

## 📝 Notas Importantes

- O frontend se reconecta automaticamente em caso de desconexão
- O painel suporta múltiplas conexões simultâneas
- As notificações de som requerem interação do usuário (clique/toque) para funcionar
- O painel de teste está disponível apenas em modo desenvolvimento

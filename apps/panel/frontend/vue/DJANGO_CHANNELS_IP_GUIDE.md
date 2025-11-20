# Guia: Extrair IP Real da Rede Interna via Django Channels

## Visão Geral

O navegador não consegue acessar o IP real do dispositivo na rede interna por questões de segurança. Porém, quando o cliente se conecta ao servidor via WebSocket, o Django Channels tem acesso ao IP da conexão. Este guia mostra como extrair essa informação e enviá-la de volta ao frontend.

## Implementação no Django Channels

### 1. Consumer Django Channels

Crie um arquivo `consumers.py` na sua aplicação Django:

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class DashboardControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Chamado quando o cliente WebSocket se conecta.
        Extrai o IP real da conexão e envia ao cliente.
        """
        # Extrair IP real da conexão
        client_ip = self.get_client_ip()
        
        # Aceitar a conexão
        await self.accept()
        
        # Enviar o IP ao cliente na primeira mensagem
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'client_ip': client_ip,
            'message': 'Conectado ao servidor'
        }))
    
    async def disconnect(self, close_code):
        """Chamado quando o cliente desconecta."""
        pass
    
    async def receive(self, text_data):
        """
        Chamado quando o servidor recebe uma mensagem do cliente.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Responder ao ping com pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': str(datetime.now())
                }))
            
            elif message_type == 'request_ip':
                # Cliente pedindo o IP novamente
                client_ip = self.get_client_ip()
                await self.send(text_data=json.dumps({
                    'type': 'client_ip_response',
                    'client_ip': client_ip
                }))
            
            # Adicione aqui outros tipos de mensagens (tickets, projetos, etc)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))
    
    def get_client_ip(self):
        """
        Extrai o IP real do cliente da conexão WebSocket.
        Trata proxies e X-Forwarded-For headers.
        """
        # Tenta obter do header X-Forwarded-For (quando atrás de proxy)
        headers = dict(self.scope.get('headers', []))
        x_forwarded_for = headers.get(b'x-forwarded-for', b'').decode('utf-8')
        
        if x_forwarded_for:
            # Pega o primeiro IP da lista (cliente real)
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Fallback: IP direto da conexão
        client_addr = self.scope.get('client')
        if client_addr:
            return client_addr[0]
        
        return 'Desconhecido'
```

### 2. Configuração do Routing (routing.py)

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard_control/$', consumers.DashboardControlConsumer.as_asgi()),
]
```

### 3. Configuração do asgi.py

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seu_projeto.settings')

django_asgi_app = get_asgi_application()

from seu_app.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
```

## Implementação no Frontend Vue.js

### 1. Atualizar useWebSocket.ts

```typescript
import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const isConnected = ref(false)
  const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('disconnected')
  const clientId = ref('')
  const clientIp = ref('Detectando...')
  const lastMessage = ref<any>(null)
  let ws: WebSocket | null = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  const connect = () => {
    connectionStatus.value = 'connecting'
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard_control/`
    
    try {
      ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('[WebSocket] Conectado ao servidor')
        isConnected.value = true
        connectionStatus.value = 'connected'
        reconnectAttempts = 0
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          lastMessage.value = data
          
          // Quando o servidor envia o IP, armazenar
          if (data.type === 'connection_established' && data.client_ip) {
            clientIp.value = data.client_ip
            console.log('[WebSocket] IP recebido:', data.client_ip)
          }
          
          if (data.type === 'client_ip_response' && data.client_ip) {
            clientIp.value = data.client_ip
          }
          
          // Processar outras mensagens aqui
          console.log('[WebSocket] Mensagem recebida:', data)
        } catch (e) {
          console.error('[WebSocket] Erro ao processar mensagem:', e)
        }
      }
      
      ws.onerror = (error) => {
        console.error('[WebSocket] Erro:', error)
        connectionStatus.value = 'disconnected'
        isConnected.value = false
      }
      
      ws.onclose = () => {
        console.log('[WebSocket] Desconectado')
        isConnected.value = false
        connectionStatus.value = 'disconnected'
        
        // Tentar reconectar
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          console.log(`[WebSocket] Tentando reconectar (${reconnectAttempts}/${maxReconnectAttempts})...`)
          setTimeout(connect, reconnectDelay)
        }
      }
    } catch (error) {
      console.error('[WebSocket] Erro ao conectar:', error)
      connectionStatus.value = 'disconnected'
    }
  }

  const send = (data: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    } else {
      console.warn('[WebSocket] Não conectado. Mensagem não enviada:', data)
    }
  }

  const requestIp = () => {
    send({
      type: 'request_ip'
    })
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    connectionStatus,
    clientId,
    clientIp,
    lastMessage,
    send,
    requestIp,
    disconnect,
    connect
  }
}
```

### 2. Atualizar App.vue

```typescript
import { useWebSocket } from './composables/useWebSocket'

const {
  isConnected: wsConnected,
  connectionStatus,
  clientId,
  clientIp,  // Agora vem do WebSocket!
  lastMessage,
  send: sendWebSocketMessage
} = useWebSocket()
```

## Fluxo de Comunicação

```
1. Frontend conecta ao WebSocket
   ↓
2. Django Channels recebe conexão
   ↓
3. Extrai IP da conexão (self.scope['client'][0])
   ↓
4. Envia mensagem 'connection_established' com IP
   ↓
5. Frontend recebe IP e armazena em clientIp
   ↓
6. Frontend exibe IP no header
```

## Exemplo de Mensagens WebSocket

### Conexão Estabelecida (servidor → cliente)
```json
{
  "type": "connection_established",
  "client_ip": "192.168.1.100",
  "message": "Conectado ao servidor"
}
```

### Requisição de IP (cliente → servidor)
```json
{
  "type": "request_ip"
}
```

### Resposta de IP (servidor → cliente)
```json
{
  "type": "client_ip_response",
  "client_ip": "192.168.1.100"
}
```

## Tratamento de Proxies

Se seu servidor estiver atrás de um proxy (Nginx, Apache, etc), certifique-se de que o proxy está passando o header `X-Forwarded-For`:

### Nginx
```nginx
location /ws/ {
    proxy_pass http://seu_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Apache
```apache
<Location /ws/>
    ProxyPass ws://seu_backend/ws/
    ProxyPassReverse ws://seu_backend/ws/
    ProxyPreserveHost On
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"
</Location>
```

## Segurança

⚠️ **Importante**: O IP extraído via WebSocket é confiável apenas se:
1. A conexão é direta (sem proxies)
2. Ou o proxy está configurado corretamente para passar `X-Forwarded-For`
3. Você valida o header `X-Forwarded-For` no seu servidor

Nunca confie cegamente em headers HTTP, pois podem ser falsificados pelo cliente.

## Teste

Para testar no painel de demonstração:
1. Abra o painel no navegador
2. Verifique se o IP aparece no header (ao lado do ID DISPLAY-XXXXX)
3. Clique no ícone de bug para abrir o painel de teste
4. Veja o IP também exibido no painel de teste

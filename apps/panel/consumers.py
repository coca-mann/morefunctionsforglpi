import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from apps.dbcom.glpi_queries import get_panel_data, tickets_open_today, tickets_resolved_today
from datetime import datetime

class PanelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"WebSocket connecting... Scope: {self.scope['type']}")
        await self.accept()
        print("WebSocket accepted")
        
        # Send initial data upon connection
        await self.send_panel_data()
        
        # Start background polling task
        self.polling_task = asyncio.create_task(self.poll_data())

    async def disconnect(self, close_code):
        # Cancel polling task
        if hasattr(self, 'polling_task'):
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass

    async def poll_data(self):
        while True:
            try:
                await asyncio.sleep(30) # Poll every 30 seconds
                await self.send_panel_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in polling task: {e}")
                await asyncio.sleep(30) # Wait before retrying

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_data':
                await self.send_panel_data()
            elif message_type == 'identify':
                # Log client identification if needed
                client_id = data.get('clientId')
                # print(f"Client identified: {client_id}")
            elif message_type == 'request_ip':
                # Get client IP from scope or headers (for proxies)
                client_ip = self.scope.get('client', ['unknown'])[0]
                
                # Check for X-Forwarded-For header
                headers = dict(self.scope.get('headers', []))
                
                print(f"\n[DEBUG] Headers received: {headers}")
                
                if b'x-forwarded-for' in headers:
                    x_forwarded = headers[b'x-forwarded-for'].decode()
                    print(f"[DEBUG] X-Forwarded-For found: {x_forwarded}")
                    client_ip = x_forwarded.split(',')[0].strip()
                
                print(f"[DEBUG] Resolved Client IP: {client_ip}\n")
                
                await self.send(text_data=json.dumps({
                    'type': 'client_ip_response',
                    'client_ip': client_ip
                }))
                
        except json.JSONDecodeError:
            pass

    async def send_panel_data(self):
        # Fetch data from GLPI (sync call wrapped in async)
        tickets_data = await sync_to_async(get_panel_data)()
        open_today_data = await sync_to_async(tickets_open_today)()
        resolved_today_data = await sync_to_async(tickets_resolved_today)()
        
        # Extract values from single-row results
        open_today = open_today_data[0].get('Open_today', 0) if open_today_data else 0
        resolved_today = resolved_today_data[0].get('Solved_today', 0) if resolved_today_data else 0
        
        # Calculate counters based on the data
        counters = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total': len(tickets_data),
            'open_today': open_today,
            'resolved_today': resolved_today
        }

        # Map urgency to counters
        # Urgency: 'Muito Alta' -> critical, 'Alta' -> high, 'Média' -> medium, 'Baixa'/'Muito baixa' -> low
        # Note: get_panel_data returns 'Urgencia' as string.
        
        for ticket in tickets_data:
            urgency = ticket.get('Urgencia', '')
            if urgency == 'Muito Alta':
                counters['critical'] += 1
            elif urgency == 'Alta':
                counters['high'] += 1
            elif urgency == 'Média':
                counters['medium'] += 1
            else:
                counters['low'] += 1

        response = {
            'type': 'tickets_update',
            'data': tickets_data,
            'counters': counters,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        await self.send(text_data=json.dumps(response, default=str))

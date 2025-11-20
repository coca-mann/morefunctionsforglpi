import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from apps.dbcom.glpi_queries import get_panel_data, newpanel_dashboard_ticketcounter
from apps.panel.models import DashboardSettings
from datetime import datetime

class PanelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"WebSocket connecting... Scope: {self.scope['type']}")
        await self.accept()
        print("WebSocket accepted")
        
        # Send initial settings upon connection
        await self.send_settings()
        
        # Send initial data upon connection
        await self.send_panel_data()
        await self.send_dashboard_kpi_data()
        
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
        # Fetch settings once per loop to get the interval
        settings_data = await sync_to_async(DashboardSettings.objects.get_settings)()
        interval = settings_data.fetch_interval_seconds

        while True:
            try:
                # Use the interval from settings
                await asyncio.sleep(interval) 

                # Periodically re-fetch settings to check for changes
                new_settings_data = await sync_to_async(DashboardSettings.objects.get_settings)()
                if new_settings_data.fetch_interval_seconds != interval or \
                   new_settings_data.notification_sound_url != settings_data.notification_sound_url:
                    
                    settings_data = new_settings_data
                    interval = new_settings_data.fetch_interval_seconds
                    await self.send_settings(settings_data)

                # Send data updates
                await self.send_panel_data()
                await self.send_dashboard_kpi_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in polling task: {e}")
                await asyncio.sleep(interval or 30) # Wait before retrying

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_data':
                view = data.get('view')
                if view == 'dashboard':
                    await self.send_dashboard_kpi_data()
                else:
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

    async def send_settings(self, settings_obj=None):
        """Fetches settings from DB and sends them to the client."""
        if not settings_obj:
            settings_obj = await sync_to_async(DashboardSettings.objects.get_settings)()

        settings_payload = {
            'fetch_interval_seconds': settings_obj.fetch_interval_seconds,
            'notification_sound_url': settings_obj.notification_sound_url
        }

        response = {
            'type': 'settings_update',
            'settings': settings_payload,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        await self.send(text_data=json.dumps(response, default=str))

    async def send_dashboard_kpi_data(self):
        counter_data = await sync_to_async(newpanel_dashboard_ticketcounter)()
        
        kpis = counter_data[0] if counter_data else {
            'total_hoje': 0,
            'total_ontem': 0,
            'diferenca': 0
        }

        response = {
            'type': 'dashboard_update',
            'kpis': kpis,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        await self.send(text_data=json.dumps(response, default=str))

    async def send_panel_data(self):
        # Fetch data from GLPI (sync call wrapped in async)
        tickets_data = await sync_to_async(get_panel_data)()
        
        response = {
            'type': 'tickets_update',
            'data': tickets_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        await self.send(text_data=json.dumps(response, default=str))

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from apps.dbcom.glpi_queries import get_panel_data, newpanel_dashboard_ticketcounter, newpanel_dashboard_responsetimeavg, tickets_resolved_today, newpanel_dashboard_clientsatisfactionpercent, newpanel_dashboard_departmentteam, newpanel_projects_data
from apps.panel.models import DashboardSettings, Display
from datetime import datetime, date
from decimal import Decimal

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

        # Remove display from DB
        try:
            await sync_to_async(Display.objects.filter(channel_name=self.channel_name).delete)()
        except Exception as e:
            print(f"Error removing display: {e}")

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
                await self.send_projects_data()

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
                elif view == 'projects':
                    await self.send_projects_data()
                else:
                    await self.send_panel_data()
            elif message_type == 'identify':
                # Log client identification if needed
                client_id = data.get('clientId')
                available_screens = data.get('availableScreens', [])
                
                # Register or update display
                await sync_to_async(self.register_display)(client_id, available_screens)
                print(f"Client identified and registered: {client_id}")
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
        
        kpis = counter_data[0] if counter_data and counter_data[0] else {
            'total_hoje': 0,
            'total_ontem': 0,
            'diferenca': 0
        }

        # Fetch response time data
        responsetime_data = await sync_to_async(newpanel_dashboard_responsetimeavg)()
        if responsetime_data and responsetime_data[0]:
            # Convert decimal values to string for JSON serialization
            rt_kpis = {k: str(v) if v is not None else None for k, v in responsetime_data[0].items()}
            kpis.update(rt_kpis)
        else:
            kpis.update({
                'solucao_mes_atual': None,
                'solucao_mes_passado': None,
                'diferenca_segundos': None
            })

        
        # Fetch resolved today data
        resolved_today_data = await sync_to_async(tickets_resolved_today)()
        resolved_today_count = resolved_today_data[0].get('Solved_today', 0) if resolved_today_data else 0
        kpis['resolved_today'] = resolved_today_count

        # Fetch satisfaction data
        satisfaction_data = await sync_to_async(newpanel_dashboard_clientsatisfactionpercent)()
        if satisfaction_data and satisfaction_data[0]:
            satisfaction_kpis = {k: str(v) if v is not None else None for k, v in satisfaction_data[0].items()}
            kpis.update(satisfaction_kpis)
        else:
            kpis.update({
                'porcentagem_satisfacao': '0.00',
                'qtd_pesquisas_respondidas': 0
            })
        
        # Fetch team data
        team_data = await sync_to_async(newpanel_dashboard_departmentteam)()
        # Explicitly convert Decimal to string/int for each member in the list
        processed_team_data = []
        for member in team_data:
            processed_member = {k: str(v) if isinstance(v, Decimal) else v for k, v in member.items()}
            processed_team_data.append(processed_member)
        kpis['team_members'] = processed_team_data

        response = {
            'type': 'dashboard_update',
            'kpis': kpis,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        await self.send(text_data=json.dumps(response, default=str))

    async def send_projects_data(self):
        projects_data = await sync_to_async(newpanel_projects_data)()

        processed_data = []
        for project in projects_data:
            processed_project = {k: str(v) if isinstance(v, (Decimal, date)) else v for k, v in project.items()}
            processed_data.append(processed_project)
            
        response = {
            'type': 'projects_update',
            'data': processed_data,
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
        await self.send(text_data=json.dumps(response, default=str))

    def register_display(self, client_id, available_screens):
        Display.objects.update_or_create(
            name=client_id,
            defaults={
                'channel_name': self.channel_name,
                'available_screens': available_screens,
            }
        )

    async def display_control(self, event):
        """
        Handle display control messages sent from the model signal.
        """
        command = event.get('command')
        screen = event.get('screen')

        if command == 'change_screen':
            await self.send(text_data=json.dumps({
                'type': 'change_screen',
                'screen': screen
            }))

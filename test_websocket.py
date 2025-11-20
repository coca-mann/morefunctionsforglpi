import asyncio
import websockets
import json
import sys

async def test_connection():
    uri = "ws://127.0.0.1:8000/ws/panel/"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Wait for initial data
            print("Waiting for initial data...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received message type: {data.get('type')}")
            
            if data.get('type') == 'tickets_update':
                print(f"Success! Received {len(data.get('data', []))} tickets.")
                print(f"Counters: {data.get('counters')}")
            
            # Test identification
            print("\nTesting identification...")
            await websocket.send(json.dumps({
                'type': 'identify',
                'clientId': 'TEST-SCRIPT'
            }))
            print("Identification sent.")
            
            # Test IP request
            print("\nTesting IP request...")
            await websocket.send(json.dumps({
                'type': 'request_ip'
            }))
            response = await websocket.recv()
            print(f"Received: {response}")
            
            print("\nTest completed successfully.")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        pass

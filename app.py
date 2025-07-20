from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
import json
from typing import List, Dict
import asyncio
from persistence import GamePersistence, AutoSaveManager
import asyncio
import urllib.parse

from models import GameState, Player, Commander

app = FastAPI(title="Commander EDH Tray")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global game state
game_state = GameState()
persistence = GamePersistence()
auto_save_manager = AutoSaveManager(game_state, persistence, interval=300)  # 5 minutes

# WebSocket connections - FIXED VERSION
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"Client connected to room {room_id}. Total connections: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                print(f"Client disconnected from room {room_id}. Remaining connections: {len(self.active_connections[room_id])}")

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error sending message to client: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                if conn in self.active_connections[room_id]:
                    self.active_connections[room_id].remove(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "rooms": game_state.rooms
    })

@app.post("/create_room")
async def create_room():
    room_id = game_state.create_room()
    if room_id:
        return RedirectResponse(url=f"/room/{room_id}", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Maximum rooms reached")

@app.post("/join_room")
async def join_room(room_id: str = Form(...)):
    room = game_state.get_room(room_id)
    if room:
        return RedirectResponse(url=f"/room/{room_id}", status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Room not found")

@app.get("/room/{room_id}", response_class=HTMLResponse)
async def game_room(request: Request, room_id: str):
    room = game_state.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return templates.TemplateResponse("room.html", {
        "request": request,
        "room": room,
        "room_id": room_id
    })

@app.post("/api/join_player/{room_id}")
async def join_player(room_id: str, player_name: str = Form(...)):
    room = game_state.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.add_player(player_name):
        # Broadcast update to all clients
        await manager.broadcast_to_room(
            json.dumps({"type": "player_joined", "player": player_name}),
            room_id
        )
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Cannot add player")

@app.post("/api/update_life/{room_id}/{player_name}")
async def update_life(room_id: str, player_name: str, change: int = Form(...)):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    room.players[player_name].life += change
    
    await manager.broadcast_to_room(
        json.dumps({
            "type": "life_update",
            "player": player_name,
            "life": room.players[player_name].life
        }),
        room_id
    )
    
    return {"success": True, "new_life": room.players[player_name].life}

@app.post("/api/update_tax/{room_id}/{player_name}")
async def update_tax(room_id: str, player_name: str, change: int = Form(...)):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    room.players[player_name].tax += change
    if room.players[player_name].tax < 0:
        room.players[player_name].tax = 0
    
    await manager.broadcast_to_room(
        json.dumps({
            "type": "tax_update",
            "player": player_name,
            "tax": room.players[player_name].tax
        }),
        room_id
    )
    
    return {"success": True, "new_tax": room.players[player_name].tax}

@app.post("/api/update_misc/{room_id}/{player_name}")
async def update_misc(room_id: str, player_name: str, change: int = Form(...)):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    room.players[player_name].misc += change
    if room.players[player_name].misc < 0:
        room.players[player_name].misc = 0
    
    await manager.broadcast_to_room(
        json.dumps({
            "type": "misc_update",
            "player": player_name,
            "misc": room.players[player_name].misc
        }),
        room_id
    )
    
    return {"success": True, "new_misc": room.players[player_name].misc}

@app.post("/api/update_poison/{room_id}/{player_name}")
async def update_poison(room_id: str, player_name: str, change: int = Form(...)):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    room.players[player_name].poison += change
    if room.players[player_name].poison < 0:
        room.players[player_name].poison = 0
    
    await manager.broadcast_to_room(
        json.dumps({
            "type": "poison_update",
            "player": player_name,
            "poison": room.players[player_name].poison
        }),
        room_id
    )
    
    return {"success": True, "new_poison": room.players[player_name].poison}

@app.post("/api/update_commander_damage/{room_id}/{player_name}")
async def update_commander_damage(
    room_id: str, 
    player_name: str, 
    target: str = Form(...), 
    change: int = Form(...)
):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if target not in room.players[player_name].commander_damage:
        room.players[player_name].commander_damage[target] = 0
    
    room.players[player_name].commander_damage[target] += change
    if room.players[player_name].commander_damage[target] < 0:
        room.players[player_name].commander_damage[target] = 0
    
    await manager.broadcast_to_room(
        json.dumps({
            "type": "commander_damage_update",
            "player": player_name,
            "target": target,
            "damage": room.players[player_name].commander_damage[target]
        }),
        room_id
    )
    
    return {"success": True}

@app.get("/api/search_commander")
async def search_commander(name: str):
    try:
        # URL encode the name to handle special characters
        encoded_name = urllib.parse.quote(name)
        url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_name}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's a legendary creature (valid commander)
            type_line = data.get("type_line", "").lower()
            is_legendary = "legendary" in type_line
            is_creature = "creature" in type_line
            is_planeswalker = "planeswalker" in type_line
            
            # Some planeswalkers can be commanders
            can_be_commander = data.get("oracle_text", "").lower()
            has_commander_text = "can be your commander" in can_be_commander
            
            commander = {
                "name": data.get("name", ""),
                "image_url": data.get("image_uris", {}).get("normal", ""),
                "mana_cost": data.get("mana_cost", ""),
                "type_line": data.get("type_line", ""),
                "oracle_text": data.get("oracle_text", ""),
                "colors": data.get("colors", []),
                "color_identity": data.get("color_identity", []),
                "is_valid_commander": is_legendary and (is_creature or is_planeswalker or has_commander_text),
                "cmc": data.get("cmc", 0),
                "power": data.get("power", ""),
                "toughness": data.get("toughness", ""),
                "artist": data.get("artist", ""),
                "set_name": data.get("set_name", "")
            }
            return commander
        else:
            raise HTTPException(status_code=404, detail="Commander not found")
    
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Scryfall: {str(e)}")

@app.get("/api/commander_suggestions")
async def commander_suggestions(q: str):
    try:
        if len(q) < 2:
            return {"suggestions": []}
        
        encoded_query = urllib.parse.quote(q)
        url = f"https://api.scryfall.com/cards/autocomplete?q={encoded_query}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("data", [])[:10]
            return {"suggestions": suggestions}
        else:
            return {"suggestions": []}
    
    except requests.RequestException:
        return {"suggestions": []}

@app.post("/api/set_commander/{room_id}/{player_name}")
async def set_commander(
    room_id: str, 
    player_name: str, 
    commander_name: str = Form(...)
):
    room = game_state.get_room(room_id)
    if not room or player_name not in room.players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    try:
        commander_data = await search_commander(commander_name)
        
        room.players[player_name].commander = Commander(
            name=commander_data["name"],
            image_url=commander_data["image_url"],
            mana_cost=commander_data["mana_cost"]
        )
        
        await manager.broadcast_to_room(
            json.dumps({
                "type": "commander_update",
                "player": player_name,
                "commander": commander_data
            }),
            room_id
        )
        
        return {"success": True, "commander": commander_data}
    
    except HTTPException as e:
        raise e

@app.get("/api/random_commanders")
async def random_commanders():
    try:
        url = "https://api.scryfall.com/cards/search?q=is%3Acommander&order=random&unique=cards"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            commanders = []
            
            for card in data.get("data", [])[:12]:
                commander = {
                    "name": card.get("name", ""),
                    "image_url": card.get("image_uris", {}).get("small", ""),
                    "mana_cost": card.get("mana_cost", ""),
                    "type_line": card.get("type_line", ""),
                    "colors": card.get("colors", [])
                }
                commanders.append(commander)
            
            return {"commanders": commanders}
        else:
            return {"commanders": []}
    
    except requests.RequestException:
        return {"commanders": []}

@app.post("/api/save_game/{room_id}")
async def save_game(room_id: str, filename: str = Form(None)):
    room = game_state.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        saved_filename = persistence.save_room(room, filename)
        return {"success": True, "filename": saved_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving game: {str(e)}")

@app.post("/api/load_game/{room_id}")
async def load_game(room_id: str, filename: str = Form(...)):
    try:
        loaded_room = persistence.load_room(filename)
        if not loaded_room:
            raise HTTPException(status_code=404, detail="Save file not found")
        
        # Replace the current room with loaded data
        loaded_room.room_id = room_id  # Keep the current room ID
        game_state.rooms[room_id] = loaded_room
        
        # Broadcast full room update to all clients
        await manager.broadcast_to_room(
            json.dumps({"type": "room_loaded"}),
            room_id
        )
        
        return {"success": True, "message": "Game loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading game: {str(e)}")

@app.get("/api/saved_games")
async def list_saved_games():
    try:
        saved_games = persistence.list_saved_games()
        return {"saved_games": saved_games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing saved games: {str(e)}")

@app.delete("/api/saved_games/{filename}")
async def delete_saved_game(filename: str):
    try:
        success = persistence.delete_saved_game(filename)
        if success:
            return {"success": True, "message": "Game deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Save file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting game: {str(e)}")

@app.post("/api/export_room/{room_id}")
async def export_room(room_id: str):
    room = game_state.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # Create export data
        export_data = persistence.serialize_room(room)
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting room: {str(e)}")

# FIXED WebSocket endpoint
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_sync":
                    room = game_state.get_room(room_id)
                    if room:
                        await websocket.send_text(json.dumps({
                            "type": "full_sync",
                            "game_state": {
                                "players": {
                                    name: {
                                        "life": player.life,
                                        "tax": player.tax,
                                        "misc": player.misc,
                                        "poison": player.poison, # Added poison here
                                        "commander_damage": player.commander_damage,
                                        "commander": {
                                            "name": player.commander.name,
                                            "image_url": player.commander.image_url,
                                            "mana_cost": player.commander.mana_cost
                                        } if player.commander else None
                                    } for name, player in room.players.items()
                                }
                            }
                        }))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)

@app.get("/api/room_status/{room_id}")
async def room_status(room_id: str):
    room = game_state.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    connections = len(manager.active_connections.get(room_id, []))
    return {
        "room_id": room_id,
        "players": len(room.players),
        "connections": connections,
        "player_names": list(room.players.keys())
    }

@app.on_event("startup")
async def startup_event():
    await auto_save_manager.start_auto_save()

@app.on_event("shutdown")
async def shutdown_event():
    await auto_save_manager.stop_auto_save()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
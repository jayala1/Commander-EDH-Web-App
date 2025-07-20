import json
import os
from datetime import datetime
from typing import Dict, Optional
import asyncio
from models import GameState, GameRoom, Player, Commander

class GamePersistence:
    def __init__(self, save_directory: str = "saved_games"):
        self.save_directory = save_directory
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        """Create the save directory if it doesn't exist"""
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
    
    def serialize_player(self, player: Player) -> Dict:
        """Convert Player object to dictionary"""
        return {
            "name": player.name,
            "life": player.life,
            "tax": player.tax,
            "misc": player.misc,
            "poison": player.poison,
            "commander_damage": player.commander_damage,
            "commander": {
                "name": player.commander.name,
                "image_url": player.commander.image_url,
                "mana_cost": player.commander.mana_cost
            }
        }
    
    def serialize_room(self, room: GameRoom) -> Dict:
        """Convert GameRoom object to dictionary"""
        return {
            "room_id": room.room_id,
            "max_players": room.max_players,
            "players": {
                name: self.serialize_player(player) 
                for name, player in room.players.items()
            },
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def deserialize_player(self, data: Dict) -> Player:
        """Convert dictionary to Player object"""
        player = Player(name=data["name"])
        player.life = data.get("life", 40)
        player.tax = data.get("tax", 0)
        player.misc = data.get("misc", 0)
        player.poison = data.get("poison", 0)  # New poison counter
        player.commander_damage = data.get("commander_damage", {})
        
        commander_data = data.get("commander", {})
        player.commander = Commander(
            name=commander_data.get("name", ""),
            image_url=commander_data.get("image_url", ""),
            mana_cost=commander_data.get("mana_cost", "")
        )
        
        return player
    
    def deserialize_room(self, data: Dict) -> GameRoom:
        """Convert dictionary to GameRoom object"""
        room = GameRoom(
            room_id=data["room_id"],
            max_players=data.get("max_players", 8)
        )
        
        for player_name, player_data in data.get("players", {}).items():
            room.players[player_name] = self.deserialize_player(player_data)
        
        return room
    
    def save_game_state(self, game_state: GameState, filename: Optional[str] = None) -> str:
        """Save entire game state to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_state_{timestamp}.json"
        
        filepath = os.path.join(self.save_directory, filename)
        
        # Serialize all rooms
        serialized_data = {
            "timestamp": datetime.now().isoformat(),
            "max_rooms": game_state.max_rooms,
            "rooms": {
                room_id: self.serialize_room(room)
                for room_id, room in game_state.rooms.items()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def save_room(self, room: GameRoom, filename: Optional[str] = None) -> str:
        """Save single room to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"room_{room.room_id}_{timestamp}.json"
        
        filepath = os.path.join(self.save_directory, filename)
        
        serialized_data = {
            "timestamp": datetime.now().isoformat(),
            "room": self.serialize_room(room)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_game_state(self, filename: str) -> Optional[GameState]:
        """Load game state from JSON file"""
        filepath = os.path.join(self.save_directory, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            game_state = GameState()
            game_state.max_rooms = data.get("max_rooms", 2)
            
            for room_id, room_data in data.get("rooms", {}).items():
                game_state.rooms[room_id] = self.deserialize_room(room_data)
            
            return game_state
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading game state from {filename}: {e}")
            return None
    
    def load_room(self, filename: str) -> Optional[GameRoom]:
        """Load single room from JSON file"""
        filepath = os.path.join(self.save_directory, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            room_data = data.get("room")
            if room_data:
                return self.deserialize_room(room_data)
            
            return None
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading room from {filename}: {e}")
            return None
    
    def list_saved_games(self) -> list:
        """List all saved game files"""
        if not os.path.exists(self.save_directory):
            return []
        
        files = []
        for filename in os.listdir(self.save_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(self.save_directory, filename)
                try:
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except OSError:
                    continue
        
        # Sort by modification time, newest first
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files
    
    def delete_saved_game(self, filename: str) -> bool:
        """Delete a saved game file"""
        filepath = os.path.join(self.save_directory, filename)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        
        return False
    
    def auto_save_room(self, room: GameRoom) -> str:
        """Auto-save room with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"autosave_room_{room.room_id}_{timestamp}.json"
        return self.save_room(room, filename)

class AutoSaveManager:
    def __init__(self, game_state: GameState, persistence: GamePersistence, interval: int = 300):
        """
        Auto-save manager
        interval: auto-save interval in seconds (default: 5 minutes)
        """
        self.game_state = game_state
        self.persistence = persistence
        self.interval = interval
        self.running = False
        self.task = None
    
    async def start_auto_save(self):
        """Start auto-save background task"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._auto_save_loop())
        print(f"Auto-save started with {self.interval} second interval")
    
    async def stop_auto_save(self):
        """Stop auto-save background task"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("Auto-save stopped")
    
    async def _auto_save_loop(self):
        """Auto-save loop"""
        while self.running:
            try:
                await asyncio.sleep(self.interval)
                
                if self.running and self.game_state.rooms:
                    # Save each active room
                    for room_id, room in self.game_state.rooms.items():
                        if room.players:  # Only save rooms with players
                            filename = self.persistence.auto_save_room(room)
                            print(f"Auto-saved room {room_id} to {filename}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in auto-save: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
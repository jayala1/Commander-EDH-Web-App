from typing import Dict, Optional
from dataclasses import dataclass, field
import uuid

@dataclass
class Commander:
    name: str = ""
    image_url: str = ""
    mana_cost: str = ""

@dataclass
class Player:
    name: str
    life: int = 40
    tax: int = 0
    misc: int = 0
    poison: int = 0  # NEW: Poison counter
    commander_damage: Dict[str, int] = field(default_factory=dict)
    commander: Commander = field(default_factory=Commander)

@dataclass
class GameRoom:
    room_id: str
    players: Dict[str, Player] = field(default_factory=dict)
    max_players: int = 8
    
    def add_player(self, player_name: str) -> bool:
        if len(self.players) >= self.max_players:
            return False
        if player_name in self.players:
            return False
        
        # Initialize commander damage for all existing players
        new_player = Player(name=player_name)
        for existing_player_name in self.players:
            new_player.commander_damage[existing_player_name] = 0
            self.players[existing_player_name].commander_damage[player_name] = 0
            
        self.players[player_name] = new_player
        return True
    
    def remove_player(self, player_name: str) -> bool:
        if player_name not in self.players:
            return False
        
        # Remove from all other players' commander damage
        for player in self.players.values():
            if player_name in player.commander_damage:
                del player.commander_damage[player_name]
        
        del self.players[player_name]
        return True

class GameState:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.max_rooms = 2
    
    def create_room(self) -> Optional[str]:
        if len(self.rooms) >= self.max_rooms:
            return None
        
        room_id = str(uuid.uuid4())[:8]
        self.rooms[room_id] = GameRoom(room_id=room_id)
        return room_id
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)
    
    def delete_room(self, room_id: str) -> bool:
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False
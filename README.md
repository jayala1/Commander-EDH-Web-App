# Commander EDH Tray(AI Created)

Commander EDH Tray is a web-based application designed to help **Magic: The Gathering Commander (EDH)** players keep track of their life totals, commander damage, and other counters during a game. It features **real-time updates** using WebSockets, **commander search and display** powered by the **Scryfall API**, and **game state persistence**.

<img width="1791" height="811" alt="image" src="https://github.com/user-attachments/assets/04bd7819-7e2f-441b-afe2-9a938b21301d" />

<img width="1540" height="847" alt="image" src="https://github.com/user-attachments/assets/9586b38a-ae74-40e2-b8fe-fd9f3945573a" />



---

## Features

- **Life Tracking:** Easily adjust life totals for each player.
- **Commander Damage Tracking:** Track commander damage dealt by each commander to each opponent.
- **Tax, Misc, and Poison Counters:** Keep track of commander tax, miscellaneous counters, and poison counters.
- **Real-time Updates:** WebSockets ensure all connected players in a room see updates instantly.
- **Commander Search & Display:** Search for commanders using the Scryfall API, display their image and mana cost.
- **Random Commander Suggestions:** Get random commander suggestions.
- **Game State Persistence:** Save and load game states to/from JSON files.
- **Auto-save:** Automatically saves game state periodically.
- **Export Game State:** Export the current game state as a JSON file.
- **Responsive Design:** Optimized for various screen sizes, including mobile.

---

## Technologies Used

- **Backend:** FastAPI (Python)  
- **Frontend:** HTML, CSS, JavaScript  
- **Real-time Communication:** WebSockets  
- **Commander Data:** Scryfall API  

---

## Setup and Installation

Follow these steps to set up and run the **Commander EDH Tray** application on your local machine.

### ✅ Prerequisites

- Python 3.7+
- pip (Python package installer)

---

### 1. Set up a Python Virtual Environment (Recommended)
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
# Install packages
pip install fastapi uvicorn Jinja2 requests python-multipart(or pip install -r requirements)

## Run Application
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

## Usage
1. Create a New Room → Click "Create New Room" to generate a unique room ID.
2. Join an Existing Room → Enter the room ID and click "Join Room".
3. Join the Game → Enter your player name and click "Join Game".
4. Update Counters → Use the + / - buttons to adjust life, tax, misc, and poison counters.
5. Commander Damage → Track damage dealt to other players.
6. Set Commander → Search, select, and set your commander (powered by Scryfall API).
7. Commander Details → Click a commander's image for more details.
8. Save/Load Game → Save, load, or export the game state (JSON format).
9. Random Commanders → Get random commander suggestions.

## Project Structure
- app.py → Main FastAPI application (routes, WebSocket handling, API endpoints).
- models.py → Data models (Commander, Player, GameRoom).
- persistence.py → Saving/loading game states to/from JSON files.
- static/ → CSS (style.css) and JavaScript (script.js).
- templates/ → Jinja2 HTML templates (base.html, index.html, room.html).
- saved_games/ → (Auto-created) directory for saved game files.

## Project Layout
```bash
.
├── app.py
├── models.py
├── persistence.py
├── static/
│   ├── style.css
│   └── script.js
└── templates/
    ├── base.html
    ├── index.html
    └── room.html
```

## Acknowledgements
-This application uses the Scryfall API to fetch Magic: The Gathering card data, including commander details and random suggestions.
Special thanks to the Scryfall team for providing such an excellent resource!

-Magic: The Gathering, Magic, and their logos are trademarks of Wizards of the Coast LLC. This project is unaffiliated with and not endorsed by Wizards of the Coast.

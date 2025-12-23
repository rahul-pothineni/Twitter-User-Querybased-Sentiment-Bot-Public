"""
PlayerRAG.py - Claude-based player resolution using Anthropic API
"""
import json
from pathlib import Path
import Database
from anthropic import Anthropic
from Keys import ANTHROPIC_API_KEY

class PlayerRAG:
    def __init__(self, kb_file: str = "nfl_players_kb.json"):
        self.kb_file = kb_file
        self.knowledge_base = self._load_kb()
        self.nickname_map = self._build_nickname_map()
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def _load_kb(self):
        """Load knowledge base from JSON file"""
        if Path(self.kb_file).exists():
            with open(self.kb_file, 'r') as f:
                return json.load(f)
        return []
    
    def _build_nickname_map(self):
        """Build a map of nicknames to official names"""
        nickname_map = {}
        for player in self.knowledge_base:
            official_name = player["name"]
            nickname_map[official_name.lower()] = official_name
            
            if "nicknames" in player:
                for nickname in player["nicknames"]:
                    nickname_map[nickname.lower()] = official_name
        
        return nickname_map
    
    def resolve_player_from_kb(self, query: str):
        """Try to resolve player from existing knowledge base first"""
        query_lower = query.lower()
        
        # Direct nickname match
        if query_lower in self.nickname_map:
            return self.nickname_map[query_lower]
        
        # Partial name match
        for player in self.knowledge_base:
            if query_lower in player["name"].lower() or player["name"].lower() in query_lower:
                return player["name"]
        
        return None
    
    def resolve_player(self, query: str):
        """
        Use Claude to identify NFL player from nickname/query.
        """
        print(f"\nResolving player: '{query}'")
        
        # Step 1: Try KB first
        player_name = self.resolve_player_from_kb(query)
        if player_name:
            print(f"✓ Found in KB: {player_name}")
            for player in self.knowledge_base:
                if player["name"] == player_name:
                    return player
        
        # Step 2: Use Claude to identify player
        print(f"Using Claude to identify player: ")

        kb_context = json.dumps(self.knowledge_base, indent=2) if self.knowledge_base else "Empty knowledge base"

        prompt = f"""You are an NFL expert. A user has mentioned a player with this query: "{query}"

Here is our current knowledge base of NFL players:
{kb_context}

Find the matching NFL player. If the query doesn't match anyone in the KB, use your knowledge to find the most likely NFL player matching this nickname/abbreviation.

Return ONLY a JSON object with this exact format (no markdown, just JSON):
{{
  "name": "Full Player Name",
  "team": "Team Name",
  "position": "Position",
  "nicknames": ["{query}"]
}}

If you cannot identify a player, return:
{{"error": "Player not found"}}"""
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            player_info = json.loads(response_text)
            
            if "error" in player_info:
                print(f"✗ Could not identify player: {query}")
                return None
            
            # Step 3: Confirm with user
            if self.confirm_player_with_user(player_info):
                self.add_player_to_kb(player_info)
                return player_info
            else:
                print("Player not confirmed.")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse Claude response: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def confirm_player_with_user(self, player_info: dict):
        """Ask user to confirm player"""
        print(f"\n✓ Found: {player_info['name']}")
        print(f"  Team: {player_info['team']}")
        print(f"  Position: {player_info['position']}")
        
        confirm = input("\nIs this the player? (y/n): ").strip().lower()
        return confirm == 'y'
    
    def add_player_to_kb(self, player_info: dict):
        """Add new player to knowledge base and save to file"""
        # Check if already exists
        for player in self.knowledge_base:
            if player["name"].lower() == player_info["name"].lower():
                print(f"Player {player_info['name']} already exists in KB")
                return
        
        # Add to KB
        self.knowledge_base.append(player_info)
        self.nickname_map[player_info["name"].lower()] = player_info["name"]
        
        for nickname in player_info.get("nicknames", []):
            self.nickname_map[nickname.lower()] = player_info["name"]
        
        # Save to file
        self._save_kb()
        print(f"Added {player_info['name']} to knowledge base")
    
    def _save_kb(self):
        """Save knowledge base to file"""
        with open(self.kb_file, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def retrieve_player_info(self, query: str):
        """Retrieve player info by query"""
        return self.resolve_player(query)
"""
Game integration example for MotiveProxy.

This example shows how MotiveProxy can be used in a game scenario
where a human player controls an NPC that normally would be AI-controlled.
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class GameState:
    """Represents the current state of the game."""
    player_name: str
    location: str
    health: int
    inventory: List[str]
    npc_name: str = "Guard"


class GameNPC:
    """Represents an NPC that can be controlled by either AI or human."""
    
    def __init__(self, npc_id: str, proxy_url: str = "http://localhost:8000"):
        self.npc_id = npc_id
        self.proxy_url = proxy_url
        self.is_human_controlled = False
    
    async def send_message(self, message: str) -> str:
        """Send a message to the proxy and get response."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.proxy_url}/v1/chat/completions",
                json={
                    "model": self.npc_id,
                    "messages": [{"role": "user", "content": message}]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
            
            return "I'm not sure how to respond..."
    
    async def connect_human(self):
        """Connect a human controller to this NPC."""
        print(f"🤖 {self.npc_id}: Human controller connecting...")
        # Send initial ping to establish connection
        await self.send_message("ping")
        self.is_human_controlled = True
        print(f"✅ {self.npc_id}: Human controller connected!")
    
    async def interact_with_player(self, game_state: GameState, player_message: str) -> str:
        """Handle interaction with the player."""
        context = f"""
You are a {game_state.npc_name} in a fantasy game. 
Player: {game_state.player_name}
Location: {game_state.location}
Player Health: {game_state.health}
Player Inventory: {', '.join(game_state.inventory)}

Player says: "{player_message}"

Respond as the {game_state.npc_name} would. Keep responses brief and in character.
"""
        
        response = await self.send_message(context)
        return response


class GameEngine:
    """Simple game engine that demonstrates MotiveProxy integration."""
    
    def __init__(self):
        self.state = GameState(
            player_name="Adventurer",
            location="Town Square",
            health=100,
            inventory=["sword", "potion", "gold coins"]
        )
        self.npc = GameNPC("town-guard")
    
    async def start_game(self):
        """Start the game and set up human-controlled NPC."""
        print("🎮 Fantasy Game Starting...")
        print("=" * 50)
        
        # Connect human controller to the guard NPC
        await self.npc.connect_human()
        
        print(f"\n📍 You are in the {self.state.location}")
        print(f"💚 Health: {self.state.health}")
        print(f"🎒 Inventory: {', '.join(self.state.inventory)}")
        print(f"👮 A {self.state.npc_name} approaches you...")
        
        # Start the interaction loop
        await self.interaction_loop()
    
    async def interaction_loop(self):
        """Main game interaction loop."""
        while True:
            print(f"\n💬 What do you say to the {self.state.npc_name}?")
            print("(Type 'quit' to exit, 'status' for game state)")
            
            # In a real game, this would be player input
            # For this example, we'll simulate some interactions
            player_inputs = [
                "Hello there!",
                "Can you tell me about this town?",
                "Where can I find a healer?",
                "quit"
            ]
            
            for player_input in player_inputs:
                if player_input.lower() == "quit":
                    print("👋 Thanks for playing!")
                    return
                elif player_input.lower() == "status":
                    self.show_status()
                    continue
                
                print(f"\n🗣️  You: {player_input}")
                
                # Get NPC response through MotiveProxy
                npc_response = await self.npc.interact_with_player(
                    self.state, 
                    player_input
                )
                
                print(f"👮 {self.state.npc_name}: {npc_response}")
                
                # Simulate some game logic based on the interaction
                await self.process_interaction(player_input, npc_response)
                
                await asyncio.sleep(1)  # Brief pause between interactions
    
    async def process_interaction(self, player_input: str, npc_response: str):
        """Process the interaction and update game state."""
        # Simple game logic based on interactions
        if "healer" in player_input.lower():
            print("📍 The guard points you toward the temple district.")
            self.state.location = "Temple District"
        elif "thank" in player_input.lower():
            print("💚 The guard's kind words restore some of your health!")
            self.state.health = min(100, self.state.health + 10)
    
    def show_status(self):
        """Show current game status."""
        print(f"\n📊 Game Status:")
        print(f"   Player: {self.state.player_name}")
        print(f"   Location: {self.state.location}")
        print(f"   Health: {self.state.health}")
        print(f"   Inventory: {', '.join(self.state.inventory)}")
        print(f"   NPC Control: {'Human' if self.npc.is_human_controlled else 'AI'}")


async def main():
    """Run the game example."""
    print("🎮 MotiveProxy Game Integration Example")
    print("=" * 50)
    print("This example shows how MotiveProxy can be used to let")
    print("a human control an NPC in a game that normally uses AI.")
    print()
    print("Make sure MotiveProxy is running: motive-proxy")
    print()
    
    try:
        game = GameEngine()
        await game.start_game()
    except httpx.ConnectError:
        print("❌ Could not connect to MotiveProxy.")
        print("Make sure the server is running on http://localhost:8000")
    except KeyboardInterrupt:
        print("\n👋 Game interrupted. Thanks for playing!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

from typing import List, Optional
from enum import Enum
import random
from server.py.game import Game, Player
from pydantic import BaseModel

class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'

class BattleshipAction(BaseModel):
    action_type: ActionType
    ship_name: Optional[str]
    location: List[str]


class Ship(BaseModel):
    name: str
    length: int
    location: Optional[List[str]]
    hits: List = []

    def is_sunk(self) -> bool:
        """Check if the ship is sunk (all coordinates are hit)."""
        return len(self.hits) == self.length

    def register_hit(self, loc: str) -> bool:
        """Register a hit on the ship if the location matches."""
        if loc in self.location:
            self.hits.append(loc)
            return True
        return False

class PlayerState(BaseModel):
    name: str
    ships: List[Ship]
    shots: List[str] = []
    successful_shots: List[str] = []

    def all_ships_sunk(self) -> bool:
        """Check if all the player's ships are sunk."""
        return all(ship.is_sunk() for ship in self.ships)

    def has_all_ships_placed(self) -> bool:
        """Check if the player has placed all required ships."""
        return len(self.ships) == 5  # Expecting 5 ships


class GamePhase(str, Enum):
    SETUP = 'setup'
    RUNNING = 'running'
    FINISHED = 'finished'

class BattleshipGameState(BaseModel):
    idx_player_active: int
    phase: GamePhase
    winner: Optional[int]
    players: List[PlayerState]



class Battleship(Game):
    def __init__(self, name_player_1: str = "player-1", name_player_2: str = "player-2") -> None:
        self.players: List[PlayerState] = [PlayerState(name='a', ships=[]), PlayerState(name='b', ships=[])]
        self.idx_player_active: int = 0
        self.phase = GamePhase.SETUP
        self.winner: Optional[int] = None
        self.ship_lengths = [2, 3, 3, 4, 5]  # Ships that need to be placed by each player
        self.is_ship_placement_phase: bool = True

    def print_state(self) -> None:
        """Print the current game state."""
        state = self.get_state()
        print(f"Current turn: {state.idx_player_active}")
        for player in state.players:
            print(f"Player: {player.name}")
            print(f"Ships:")
            for ship in player.ships:
                print(f"  {ship.name} at {ship.location}, hits: {ship.hits}")
            print(f"Shots taken: {player.shots}")
            print(f"Successful shots: {player.successful_shots}")
        if state.phase == GamePhase.FINISHED:
            print(f"Game over! Winner: Player {state.winner}")

    def get_state(self) -> BattleshipGameState:
        """Get the complete, unmasked game state."""
        return BattleshipGameState(idx_player_active=self.idx_player_active, phase=self.phase, winner=self.winner, players=self.players)

    def set_state(self, state: BattleshipGameState) -> None:
        """Set the game to a given state."""
        self.idx_player_active = state.idx_player_active
        self.phase = state.phase
        self.winner = state.winner
        self.players = state.players

    def is_valid_ship_placement(self, player: PlayerState, length: int, start: str, orientation: str) -> bool:
        """
        Check if a ship of the given length can be placed starting at 'start' with the given 'orientation'
        (either 'horizontal' or 'vertical') without overlapping existing ships and within the grid bounds.
        """
        # Convert start position to row and column (e.g., 'A1' -> row = 'A', col = 1)
        row = ord(start[0])  # Row as ASCII (A=65, B=66, ..., J=74)
        col = int(start[1:])  # Column as integer (1-10)

        # Generate the coordinates for the proposed ship placement
        coordinates = self.generate_ship_coordinates(start, length, orientation)
        
        # Check if the coordinates fit within the grid
        if not coordinates:
            return False

        # Check for overlap with existing ships
        for ship in player.ships:
            if set(coordinates) & set(ship.location):  # Check if any coordinates overlap
                return False

        return True

    def generate_ship_coordinates(self, start: str, length: int, orientation: str) -> Optional[List[str]]:
        """
        Generate the list of coordinates for a ship given the starting position, length, and orientation.
        """
        row = ord(start[0])  # Row as ASCII (A=65, B=66, ..., J=74)
        col = int(start[1:])  # Column as integer (1-10)
        
        coordinates = []

        if orientation == "horizontal":
            # Horizontal placement: check if it fits within columns 1-10
            if col + length - 1 > 10:
                return None  # Does not fit horizontally
            for i in range(length):
                coordinates.append(f"{chr(row)}{col + i}")

        elif orientation == "vertical":
            # Vertical placement: check if it fits within rows A-J
            if row + length - 1 > ord('J'):
                return None  # Does not fit vertically
            for i in range(length):
                coordinates.append(f"{chr(row + i)}{col}")

        return coordinates if coordinates else None


    def get_list_action(self) -> List[BattleshipAction]:
        """Get a list of possible actions for the active player."""
        actions = []
        active_player = self.players[self.idx_player_active]

        if self.is_ship_placement_phase:
            # Allow ship placement
            ship_to_place = len(active_player.ships)
            if ship_to_place < len(self.ship_lengths):
                length_of_ship = self.ship_lengths[ship_to_place]
                # Allow setting the next ship (of given length)
                all_locations = [f"{chr(r)}{c}" for r in range(ord('A'), ord('J') + 1) for c in range(1, 11)]
                for loc in all_locations:
                    # Check for horizontal and vertical placement
                    if self.is_valid_ship_placement(active_player, length_of_ship, loc, "horizontal"):
                        actions.append(BattleshipAction(action_type=ActionType.SET_SHIP, ship_name=f"Ship-{length_of_ship}", location=self.generate_ship_coordinates(loc, length_of_ship, "horizontal")))
                    if self.is_valid_ship_placement(active_player, length_of_ship, loc, "vertical"):
                        actions.append(BattleshipAction(action_type=ActionType.SET_SHIP, ship_name=f"Ship-{length_of_ship}", location=self.generate_ship_coordinates(loc, length_of_ship, "vertical")))

        else:
            # Shooting phase - shoot at any position that hasn't been shot at yet
            all_locations = [f"{chr(r)}{c}" for r in range(ord('A'), ord('J') + 1) for c in range(1, 11)]
            remaining_shots = [loc for loc in all_locations if loc not in active_player.shots]
            for loc in remaining_shots:
                actions.append(BattleshipAction(action_type=ActionType.SHOOT, ship_name=None, location=[loc]))

        return actions

    def apply_action(self, action: BattleshipAction) -> None:
        """Apply the given action to the game."""
        active_player = self.players[self.idx_player_active]
        opponent = self.players[1 - self.idx_player_active]

        if action.action_type == ActionType.SET_SHIP:
            # Player is placing a ship
            ship_name = action.ship_name
            ship_length = len(action.location)#int(ship_name.split('-')[1])  # Get length from name, e.g., 'Ship-3'
            location = action.location
            if len(location) == ship_length:
                # Simplified: just placing ship at given location (in practice, check orientation and fit within grid)
                new_ship = Ship(name=ship_name, length=ship_length, location=location)
                active_player.ships.append(new_ship)
                print(f"Placed {ship_name} at {location}")
            else:
                print(f"Invalid placement for {ship_name}")

            # Check if all ships are placed
            if all(player.has_all_ships_placed() for player in self.players):
                self.is_ship_placement_phase = False
                self.phase = GamePhase.RUNNING

        elif action.action_type == ActionType.SHOOT:
            # Player is shooting at the opponent
            shot_location = action.location[0]
            active_player.shots.append(shot_location)

            # Check if any opponent's ship is hit
            hit = False
            for ship in opponent.ships:
                if ship.register_hit(shot_location):
                    active_player.successful_shots.append(shot_location)
                    hit = True
                    break

            if not hit:
                print(f"Missed shot at {shot_location}")
            else:
                print(f"Hit shot at {shot_location}")

            # Check if the game is over
            if opponent.all_ships_sunk():
                self.phase = GamePhase.FINISHED
                self.winner = self.idx_player_active

        # Switch turns
        self.idx_player_active = 1 - self.idx_player_active

    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        """Get the masked state for the active player (opponent's ships hidden)."""
        players_view = []
        for idx, player in enumerate(self.players):
            if idx == idx_player:
                # Player can see their own ships and hits
                players_view.append(player)
            else:
                # Opponent's ships are hidden
                hidden_ships = [Ship(name=ship.name, length=ship.length, location=None) for ship in player.ships]
                players_view.append(PlayerState(name=player.name, ships=hidden_ships, shots=player.shots, successful_shots=player.successful_shots))

        return BattleshipGameState(idx_player_active=self.idx_player_active, phase=self.phase, winner=self.winner, players=players_view)

class RandomPlayer(Player):

    def select_action(self, state: BattleshipGameState, actions: List[BattleshipAction]) -> Optional[BattleshipAction]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None

if __name__ == "__main__":

    game=Battleship()
    rand_player=RandomPlayer()
    for i in range(10):
        acts = game.get_list_action()
        act = rand_player.select_action(game.get_state(), acts)
        print(act)
        game.apply_action(act)
        game.print_state()
    #print('all_ships_located:', game.state.all_ships_located())
    game.print_state()
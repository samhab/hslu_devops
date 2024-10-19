from typing import List, Optional
import random
from enum import Enum
from server.py.game import Game, Player

class GuessLetterAction:

    def __init__(self, letter: str) -> None:
        self.letter = letter


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class HangmanGameState:

    def __init__(self, word_to_guess: str, guesses: List[str], phase: GamePhase) -> None:
        self.word_to_guess = word_to_guess.upper()
        self.guesses = guesses
        self.phase = phase

    def masked_word(self) -> str:
        """Return the masked version of the word (letters guessed so far)."""
        return ''.join(letter if letter in self.guesses else '_' for letter in self.word_to_guess)


class Hangman(Game):

    MAX_WRONG_GUESSES = 8  # Max incorrect guesses before losing

    def __init__(self) -> None:
        self.state: Optional[HangmanGameState] = None
        self.wrong_guesses = 0

    def get_state(self) -> HangmanGameState:
        """ Get the complete, unmasked game state """
        return self.state

    def set_state(self, state: HangmanGameState) -> None:
        """ Set the game to a given state """
        self.state = state
        self.wrong_guesses = 0  # Reset wrong guesses
        self.state.phase = GamePhase.RUNNING

    def print_state(self) -> None:
        """ Print the current game state (masked word and guesses) """
        masked_word = self.state.masked_word()
        print(f"Word: {masked_word}")
        print(f"Guesses: {', '.join(self.state.guesses)}")
        print(f"Wrong Guesses: {self.wrong_guesses}/{self.MAX_WRONG_GUESSES}")

    def get_list_action(self) -> List[GuessLetterAction]:
        """ Get a list of possible actions for the active player """
        all_letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        available_letters = all_letters - set(self.state.guesses)
        return [GuessLetterAction(letter) for letter in sorted(available_letters)]

    def apply_action(self, action: GuessLetterAction) -> None:
        """ Apply the given action to the game """
        guessed_letter = action.letter.upper()

        # Add the guessed letter to the guesses list
        self.state.guesses.append(guessed_letter)

        # Check if the guessed letter is in the word
        if guessed_letter not in self.state.word_to_guess:
            self.wrong_guesses += 1

        # Check for game over conditions
        if self.wrong_guesses >= self.MAX_WRONG_GUESSES:
            self.state.phase = GamePhase.FINISHED
            print("Game over! You've been hanged.")
        elif all(letter in self.state.guesses for letter in self.state.word_to_guess):
            self.state.phase = GamePhase.FINISHED
            print(f"Congratulations! You've guessed the word: {self.state.word_to_guess}")
        else:
            self.print_state()

    def get_player_view(self, idx_player: int) -> HangmanGameState:
        """ Get the masked state for the active player """
        return self.state


class RandomPlayer(Player):

    def select_action(self, state: HangmanGameState, actions: List[GuessLetterAction]) -> Optional[GuessLetterAction]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == "__main__":

    # Initialize the game
    game = Hangman()

    # Create the initial game state
    game_state = HangmanGameState(word_to_guess='DevOps', guesses=[], phase=GamePhase.SETUP)
    game.set_state(game_state)

    # Create a random player
    player = RandomPlayer()

    # Play the game
    while game.get_state().phase == GamePhase.RUNNING:
        # Get list of possible actions (letters to guess)
        actions = game.get_list_action()

        # Player selects an action
        action = player.select_action(game.get_state(), actions)

        if action:
            # Apply the selected action to the game
            game.apply_action(action)


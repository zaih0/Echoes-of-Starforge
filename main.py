# main.py
import pygame
import sys
from core.game_manager import GameManager

def main():
    pygame.init()
    
    # Set display mode
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Echoes of Starforge")
    
    # Initialize game
    game = GameManager(screen)
    game.run()

if __name__ == "__main__":
    main()
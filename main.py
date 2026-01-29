# main.py - FULLY UPDATED VERSION
import pygame
import sys
from core.settings import WIDTH, HEIGHT, FPS
from core.game_manager import GameManager

def main():
    # Initialize PyGame FIRST
    pygame.init()
    
    # Initialize font manager AFTER pygame.init() but BEFORE creating GameManager
    from core.font_manager import font_manager
    font_manager.initialize()  # This is the key line!
    
    # Get monitor dimensions for fullscreen
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    
    # Create screen with proper flags
    screen = pygame.display.set_mode(
        (screen_width, screen_height),
        pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    pygame.display.set_caption("Echoes of Starforge")
    
    # Initialize game
    game = GameManager(screen)
    
    try:
        game.run()
    except KeyboardInterrupt:
        print("\nGame terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
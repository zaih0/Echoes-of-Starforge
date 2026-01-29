# core/font_manager.py - UPDATED VERSION
import pygame
import os

# Font sizes
FONT_TITLE = 72
FONT_LARGE = 48
FONT_MEDIUM = 36
FONT_NORMAL = 24
FONT_SMALL = 18

class FontManager:
    def __init__(self):
        self.fonts = {}
        self.font_path = None
        self.using_pixel_font = False
        self.initialized = False
    
    def initialize(self):
        """Initialize fonts - should be called after pygame.init()"""
        if not self.initialized:
            self.load_fonts()
            self.initialized = True
    
    def load_fonts(self):
        """Load all fonts - with fallback to default pygame font"""
        # Initialize pygame.font if not already initialized
        if not pygame.font.get_init():
            print("WARNING: pygame.font not initialized, initializing now...")
            pygame.font.init()
        
        # Try to load pixel font from various possible locations
        possible_paths = [
            "fonts/pressstart2p.ttf",
            "../fonts/pressstart2p.ttf",
            "./fonts/pressstart2p.ttf",
            "core/../fonts/pressstart2p.ttf",
            os.path.join(os.path.dirname(__file__), "../fonts/pressstart2p.ttf"),
            os.path.join(os.path.dirname(__file__), "../../fonts/pressstart2p.ttf")
        ]
        
        self.font_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.font_path = path
                print(f"Found pixel font at: {path}")
                break
        
        if self.font_path:
            try:
                print(f"Loading pixel font from: {self.font_path}")
                # Load pixel font at different sizes
                self.fonts = {
                    "title": pygame.font.Font(self.font_path, FONT_TITLE),
                    "large": pygame.font.Font(self.font_path, FONT_LARGE),
                    "medium": pygame.font.Font(self.font_path, FONT_MEDIUM),
                    "normal": pygame.font.Font(self.font_path, FONT_NORMAL),
                    "small": pygame.font.Font(self.font_path, FONT_SMALL)
                }
                self.using_pixel_font = True
                print("Successfully loaded pixel font!")
            except Exception as e:
                print(f"Failed to load pixel font: {e}")
                self._load_default_fonts()
        else:
            print("Pixel font file not found in any expected location")
            self._load_default_fonts()
    
    def _load_default_fonts(self):
        """Load default pygame fonts as fallback"""
        print("Using default pygame fonts")
        try:
            self.fonts = {
                "title": pygame.font.Font(None, FONT_TITLE),
                "large": pygame.font.Font(None, FONT_LARGE),
                "medium": pygame.font.Font(None, FONT_MEDIUM),
                "normal": pygame.font.Font(None, FONT_NORMAL),
                "small": pygame.font.Font(None, FONT_SMALL)
            }
            print("Default fonts loaded successfully")
        except pygame.error as e:
            print(f"Error loading default fonts: {e}")
            # Try system fonts as last resort
            try:
                self.fonts = {
                    "title": pygame.font.SysFont("arial", FONT_TITLE),
                    "large": pygame.font.SysFont("arial", FONT_LARGE),
                    "medium": pygame.font.SysFont("arial", FONT_MEDIUM),
                    "normal": pygame.font.SysFont("arial", FONT_NORMAL),
                    "small": pygame.font.SysFont("arial", FONT_SMALL)
                }
                print("System fonts loaded as fallback")
            except:
                print("CRITICAL: Could not load any fonts!")
                # Create empty font dict to prevent crashes
                self.fonts = {}
    
    def get_font(self, size_name):
        """Get a font by size name"""
        if not self.initialized:
            self.initialize()
        return self.fonts.get(size_name, self.fonts.get("normal"))
    
    def render(self, text, size_name, color, antialias=True):
        """Render text with specified font size"""
        if not self.initialized:
            self.initialize()
        
        font = self.get_font(size_name)
        if font:
            try:
                return font.render(text, antialias, color)
            except Exception as e:
                print(f"Error rendering text '{text}': {e}")
                # Return a small surface as fallback
                surface = pygame.Surface((100, 20))
                surface.fill((0, 0, 0))
                return surface
        else:
            # Return empty surface if font loading failed
            print(f"WARNING: No font available for rendering")
            return pygame.Surface((10, 10))

# Create global instance
font_manager = FontManager()
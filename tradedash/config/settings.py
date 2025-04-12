"""Application settings and configuration"""

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "TradeDash - Stock Analysis"

# Chart settings
CHART_DPI = 100
CHART_WIDTH = 10
CHART_HEIGHT = 6

# Colors for dark theme - Improved Visibility
COLORS = {
    # Base colors
    "background": "#252535",  # Main background
    "background_secondary": "#313244",  # Secondary panels
    "secondary": "#3a3a4a",  # Darker elements
    "primary": "#7d67c5",  # Primary accent
    "accent": "#9b7aff",  # Brighter accent
    "accent_secondary": "#6457a2",  # Secondary accent
    "accent_tertiary": "#b490ff",  # Third accent
    "border": "#5a5a6a",  # Higher contrast border
    "hover": "#8673db",  # Hover state
    
    # Text colors
    "text": "#e0e0f0",  # Base text
    "text_bright": "#ffffff",  # Bright text
    "text_dim": "#b0b0c0",  # Dimmed text
    
    # Status colors
    "success": "#77dd77",  # Green for success/buy
    "error": "#ff6b6b",  # Red for error/sell
    "warning": "#ffcc66",  # Yellow for warnings
    
    # Chart colors
    "chart_bg": "#252535",  # Chart background
    "chart_grid": "#444454",  # Grid lines
    "chart_line": "#e0e0f0",  # Line charts
    "chart_candle_up": "#77dd77",
    "chart_candle_down": "#ff6b6b",
    "chart_volume": "#61afef",
    "chart_volume_up": "#77dd77",
    "chart_volume_down": "#ff6b6b"
}

# UI Styling Constants
BORDER_RADIUS = "8px"
ELEMENT_PADDING = "10px"
BUTTON_PADDING = "10px 16px"
GRADIENT_BACKGROUND = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #313244, stop:1 #252535)"

# Default values
DEFAULT_LOOKBACK_DAYS = 365 
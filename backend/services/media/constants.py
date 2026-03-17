from enum import Enum

class AspectRatio(float, Enum):
    SQUARE = 1.0          # 1:1
    BANNER = 16 / 9       # 16:9
    STORY = 9 / 16        # 9:16
    FEED = 4 / 5          # 4:5

PRESET_WIDTHS = 1080  # Chiều rộng chuẩn cho ảnh chất lượng cao
DEFAULT_QUALITY = 90

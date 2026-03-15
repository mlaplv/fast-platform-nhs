import pytest
from backend.services.media.utils import calculate_smart_crop

def test_square_crop_center():
    # 1000x500 image, target 1:1 (square)
    # Target crop size will be 500x500
    # Focal point at center (0.5, 0.5) -> (500, 250)
    # Desired box: (250, 0, 750, 500)
    res = calculate_smart_crop(1000, 500, 0.5, 0.5, 1.0)
    assert res == (250, 0, 750, 500)

def test_square_crop_left_edge():
    # 1000x500 image, target 1:1
    # Focal point at (0.1, 0.5) -> (100, 250)
    # Desired box: (100-250, 250-250, 100+250, 250+250) = (-150, 0, 350, 500)
    # Shifting: left is -150, so shift_x = 150
    # Result: (0, 0, 500, 500)
    res = calculate_smart_crop(1000, 500, 0.1, 0.5, 1.0)
    assert res == (0, 0, 500, 500)

def test_square_crop_right_edge():
    # 1000x500 image, target 1:1
    # Focal point at (0.9, 0.5) -> (900, 250)
    # Desired box: (900-250, 0, 900+250, 500) = (650, 0, 1150, 500)
    # Shifting: right is 1150, max is 1000. shift_x = 150.
    # Result: (500, 0, 1000, 500)
    res = calculate_smart_crop(1000, 500, 0.9, 0.5, 1.0)
    assert res == (500, 0, 1000, 500)

def test_tall_image_crop():
    # 500x1000 image, target 1:1
    # Target crop size 500x500
    # Focal point at (0.5, 0.1) -> (250, 100)
    # Desired box: (250-250, 100-250, 250+250, 100+250) = (0, -150, 500, 350)
    # Shifting: top is -150, so shift_y = 150
    # Result: (0, 0, 500, 500)
    res = calculate_smart_crop(500, 1000, 0.5, 0.1, 1.0)
    assert res == (0, 0, 500, 500)

def test_tall_image_bottom_edge():
    # 500x1000 image, target 1:1
    # Focal point at (0.5, 0.9) -> (250, 900)
    # Desired box: (0, 900-250, 500, 900+250) = (0, 650, 500, 1150)
    # Shifting: bottom is 1150, max 1000. shift_y = 150.
    # Result: (0, 400, 500, 900) - wait, if bottom=1150 and max=1000, shift is 150.
    # top = 650 - 150 = 500. bottom = 1150 - 150 = 1000.
    # Result: (0, 500, 500, 1000)
    res = calculate_smart_crop(500, 1000, 0.5, 0.9, 1.0)
    assert res == (0, 500, 500, 1000)

def test_banner_ratio_crop():
    # 1000x1000 image, target 16:9 (approx 1.777)
    # src_ratio = 1.0, target_ratio = 1.777. src_ratio < target_ratio.
    # crop_w = 1000, crop_h = 1000 / (16/9) = 562.5 -> 562
    # Focal point at center (0.5, 0.5) -> (500, 500)
    # Desired box: (500-500, 500-281, 500+500, 500+281) = (0, 219, 1000, 781)
    res = calculate_smart_crop(1000, 1000, 0.5, 0.5, 16/9)
    # 1000 / (16/9) = 562.5 -> int is 562.
    # top = 500 - 562/2 = 500 - 281 = 219.
    # bottom = 219 + 562 = 781.
    assert res == (0, 219, 1000, 781)

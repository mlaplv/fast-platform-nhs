import unittest
from backend.services.media.utils import calculate_smart_crop

class TestSmartCrop(unittest.TestCase):
    def test_square_crop_center(self):
        # Ảnh 1920x1080, focal point ở chính giữa (0.5, 0.5), crop Square (1:1)
        # Kỳ vọng: Crop box sẽ là 1080x1080, căn giữa theo chiều ngang
        # Center_x = 960, Crop_w = 1080 -> Left = 960 - 540 = 420, Right = 1500
        box = calculate_smart_crop(1920, 1080, 0.5, 0.5, 1.0)
        self.assertEqual(box, (420, 0, 1500, 1080))

    def test_focal_at_edge_left(self):
        # Focal point ở sát lề trái (0.1, 0.5)
        # Center_x = 192, Crop_w = 1080 -> Left = 192 - 540 = -348 -> Shifted to 0
        box = calculate_smart_crop(1920, 1080, 0.1, 0.5, 1.0)
        self.assertEqual(box[0], 0)
        self.assertEqual(box[2], 1080)
        self.assertEqual(box[1], 0)
        self.assertEqual(box[3], 1080)

    def test_focal_at_edge_right(self):
        # Focal point ở sát lề phải (0.9, 0.5)
        # Center_x = 1728, Crop_w = 1080 -> Right = 1728 + 540 = 2268 -> Shifted back to 1920
        box = calculate_smart_crop(1920, 1080, 0.9, 0.5, 1.0)
        self.assertEqual(box[2], 1920)
        self.assertEqual(box[0], 1920 - 1080)

    def test_tall_image_to_banner(self):
        # Ảnh dọc 1080x1920, crop Banner (16:9 ~ 1.77)
        # Kỳ vọng: Lấy full chiều rộng, tính toán chiều cao tương ứng
        target_ratio = 16/9
        box = calculate_smart_crop(1080, 1920, 0.5, 0.5, target_ratio)
        crop_w = 1080
        crop_h = int(1080 / target_ratio) # 1080 / 1.777 = 607
        self.assertEqual(box[2] - box[0], crop_w)
        self.assertEqual(box[3] - box[1], crop_h)

if __name__ == '__main__':
    unittest.main()

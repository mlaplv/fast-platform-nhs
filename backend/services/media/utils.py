from typing import Tuple

def calculate_smart_crop(
    src_w: int,
    src_h: int,
    focal_x: float,
    focal_y: float,
    target_ratio: float
) -> Tuple[int, int, int, int]:
    """
    Tính toán toạ độ crop (left, top, right, bottom) dựa trên điểm tụ (focal point).
    focal_x, focal_y: giá trị chuẩn hoá từ 0.0 đến 1.0.
    """
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Ảnh gốc rộng hơn mục tiêu -> Giới hạn bởi chiều cao
        crop_h = src_h
        crop_w = int(src_h * target_ratio)
    else:
        # Ảnh gốc cao hơn mục tiêu -> Giới hạn bởi chiều rộng
        crop_w = src_w
        crop_h = int(src_w / target_ratio)

    # Tâm điểm mong muốn (tính theo pixel)
    center_x = focal_x * src_w
    center_y = focal_y * src_h

    # Toạ độ dự kiến
    left = center_x - crop_w / 2
    top = center_y - crop_h / 2
    right = left + crop_w
    bottom = top + crop_h

    # Xử lý Shifting để clamp box vào trong ảnh gốc mà không làm thay đổi kích thước crop
    if left < 0:
        shift_x = -left
        left += shift_x
        right += shift_x
    elif right > src_w:
        shift_x = right - src_w
        left -= shift_x
        right -= shift_x

    if top < 0:
        shift_y = -top
        top += shift_y
        bottom += shift_y
    elif bottom > src_h:
        shift_y = bottom - src_h
        top -= shift_y
        bottom -= shift_y

    return (int(left), int(top), int(right), int(bottom))

#!/usr/bin/env python3
"""
Clypra Video Compiler (V1.0 - Headless 1-Click Production Engine)
Compiles exported video scripts (.md or .json) into finished MP4 videos locally using ffmpeg.
"""
import os
import sys
import json
import re
import urllib.parse
import urllib.request
import tempfile
import subprocess
import argparse
from pathlib import Path

# ANSI colors for premium console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Đường dẫn chạy ffmpeg và ffprobe cục bộ
SCRIPT_DIR = Path(__file__).parent.resolve()
FFMPEG_BIN = str(SCRIPT_DIR / "ffmpeg")
FFPROBE_BIN = str(SCRIPT_DIR / "ffprobe")

def log_info(msg):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def log_success(msg):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")

def log_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def log_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}", file=sys.stderr)

def wrap_text(text, max_chars=40):
    """Chia nhỏ câu thoại dài thành nhiều dòng để hiển thị phụ đề đẹp mắt"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > max_chars:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

def get_audio_duration(audio_path):
    """Truy vấn thời lượng thực tế của file âm thanh bằng ffprobe"""
    try:
        cmd = [
            FFPROBE_BIN, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        log_warn(f"Không thể đo thời lượng âm thanh bằng ffprobe: {e}. Sử dụng thời lượng mặc định.")
        return None

def download_file(url, local_path):
    """Tải tệp từ internet sử dụng lệnh curl hệ thống để đảm bảo độ tin cậy và tốc độ tối đa"""
    cmd = [
        "curl", "-s", "-f", "-L",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--connect-timeout", "10",
        "--max-time", "30",
        url, "-o", local_path
    ]
    subprocess.run(cmd, check=True)

def parse_script(file_path):
    """Đọc và trích xuất dữ liệu JSON từ file .md hoặc .json kịch bản"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        
    content = path.read_text(encoding="utf-8")
    
    # Nếu là file JSON thuần
    if path.suffix == ".json":
        return json.loads(content)
        
    # Nếu là file Markdown, tìm khối JSON ở cuối
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
        
    raise ValueError("Không tìm thấy dữ liệu kịch bản JSON hợp lệ trong file kịch bản.")

def compile_video(script_data, voice_choice, output_path, burn_subtitles):
    scenes = script_data.get("scenes", [])
    if not scenes:
        log_error("Kịch bản không có phân cảnh nào!")
        return False
        
    style_name = script_data.get("style_name", "").lower()
    
    # Xác định tỷ lệ khung hình
    is_vertical = any(kw in style_name for kw in ["tiktok", "shorts", "reels", "drama", "9:16"])
    width, height = (1080, 1920) if is_vertical else (1920, 1080)
    log_info(f"Độ phân giải video đích: {width}x{height} ({'Dọc' if is_vertical else 'Ngang'})")
    
    temp_dir = tempfile.mkdtemp(prefix="clypra_compile_")
    log_info(f"Khởi tạo thư mục tạm thời: {temp_dir}")
    
    scene_videos = []
    
    try:
        for idx, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", idx + 1)
            duration = float(scene.get("duration", 5.0))
            voiceover = scene.get("voiceover", "")
            
            log_info(f"--- Đang xử lý Phân cảnh {scene_num}/{len(scenes)} ---")
            
            # 1. Tải Audio Voiceover
            audio_url = scene.get(f"voiceover_audio_{voice_choice}")
            # Fallback nếu không có key cụ thể
            if not audio_url:
                audio_url = scene.get("voiceover_audio_hoaimy") or scene.get("voiceover_audio_namminh")
                
            local_audio_path = os.path.join(temp_dir, f"audio_{scene_num}.mp3")
            if audio_url:
                log_info(f"Tải giọng đọc AI: {audio_url[:60]}...")
                try:
                    download_file(audio_url, local_audio_path)
                except Exception as e:
                    log_warn(f"Không thể tải âm thanh, tạo tệp âm thanh trống: {e}")
                    # Tạo file im lặng bằng ffmpeg
                    subprocess.run([
                        FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", str(duration), local_audio_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Tạo file im lặng
                subprocess.run([
                    FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(duration), local_audio_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            # Cập nhật thời lượng dựa trên file âm thanh thực tế để không bị cắt lời thoại
            actual_audio_duration = get_audio_duration(local_audio_path)
            if actual_audio_duration:
                duration = max(duration, actual_audio_duration + 0.5) # Thêm 0.5s đệm cuối phân cảnh
                log_info(f"Thời lượng phân cảnh điều chỉnh theo âm thanh: {duration:.2f}s")

            # 2. Tải hình ảnh phân cảnh
            image_url = scene.get("image_url")
            local_image_path = os.path.join(temp_dir, f"image_{scene_num}.png")
            has_image = False
            
            if image_url:
                log_info(f"Tải ảnh storyboard: {image_url}")
                try:
                    download_file(image_url, local_image_path)
                    has_image = True
                except Exception as e:
                    log_warn(f"Không thể tải ảnh từ link: {e}")
                    
            if not has_image:
                # Tạo một ảnh màu đen làm nền
                log_info("Không có ảnh, tạo ảnh nền đen mặc định.")
                subprocess.run([
                    FFMPEG_BIN, "-y", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}",
                    "-vframes", "1", local_image_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            # 3. Dựng video phân cảnh bằng ffmpeg
            scene_output = os.path.join(temp_dir, f"scene_{scene_num}.mp4")
            
            # Xây dựng filter phức tạp của ffmpeg: scale ảnh giữ tỉ lệ khung hình + thêm phụ đề
            filter_parts = []
            # Scale và pad ảnh để khớp độ phân giải
            filter_parts.append(
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            )
            
            # Nếu sếp muốn chèn phụ đề trực tiếp lên video (Burn-in Subtitles)
            if burn_subtitles and voiceover:
                srt_path = os.path.join(temp_dir, f"sub_{scene_num}.srt")
                def format_timestamp(seconds):
                    h = int(seconds // 3600)
                    m = int((seconds % 3600) // 60)
                    s = int(seconds % 60)
                    ms = int(round((seconds - int(seconds)) * 1000))
                    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(f"1\n{format_timestamp(0.0)} --> {format_timestamp(duration)}\n{voiceover}\n\n")
                
                escaped_srt_path = srt_path.replace("\\", "/").replace(":", "\\:")
                font_size = 20 if is_vertical else 16
                sub_filter = f"subtitles='{escaped_srt_path}':force_style='Fontname=DejaVu Sans,Fontsize={font_size},PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2'"
                filter_parts.append(sub_filter)
                
            video_filter = ",".join(filter_parts)
            
            # Lệnh ffmpeg dựng phân cảnh
            cmd = [
                FFMPEG_BIN, "-y",
                "-loop", "1", "-i", local_image_path,
                "-i", local_audio_path,
                "-vf", video_filter,
                "-c:v", "libx264", "-t", f"{duration:.2f}",
                "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
                "-shortest", scene_output
            ]
            
            log_info(f"Đang render phân cảnh {scene_num}...")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode != 0:
                log_error(f"Render phân cảnh {scene_num} thất bại! Lỗi:\n{res.stderr.decode('utf-8', errors='ignore')}")
                return False
                
            scene_videos.append(scene_output)
            log_success(f"Render phân cảnh {scene_num} thành công!")
            
        # 4. Ghép nối (Concat) tất cả các phân cảnh thành video cuối cùng
        log_info("--- Đang ghép nối tất cả các phân cảnh ---")
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for video in scene_videos:
                f.write(f"file '{video}'\n")
                
        concat_cmd = [
            FFMPEG_BIN, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        
        log_info("Đang ghép xuất video thành phẩm...")
        res = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            log_error(f"Ghép nối video thất bại! Lỗi:\n{res.stderr.decode('utf-8', errors='ignore')}")
            return False
            
        log_success(f"Video thành phẩm đã xuất bản tại: {output_path}")
        return True
        
    finally:
        # Dọn dẹp tệp tạm
        log_info("Đang dọn dẹp các tệp tạm thời...")
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_dir)

def main():
    parser = argparse.ArgumentParser(
        description="Biên dịch kịch bản AI xuất ra từ hệ thống SmartShop thành video MP4 hoàn chỉnh bằng ffmpeg."
    )
    parser.add_argument("input", help="Đường dẫn đến file kịch bản (.md hoặc .json)")
    parser.add_argument("-o", "--output", help="Đường dẫn xuất video .mp4 (mặc định: video_output.mp4)", default="video_output.mp4")
    parser.add_argument("-v", "--voice", help="Giọng đọc: hoaimy (Nữ) hoặc namminh (Nam)", choices=["hoaimy", "namminh"], default="namminh")
    parser.add_argument("--no-subs", help="Tắt tính năng vẽ phụ đề lên video", action="store_true")
    
    args = parser.parse_args()
    
    log_info(f"Khởi chạy Clypra Video Compiler cho tệp: {args.input}")
    
    try:
        script_data = parse_script(args.input)
        log_success("Phân giải thông tin kịch bản thành công!")
        
        success = compile_video(
            script_data=script_data,
            voice_choice=args.voice,
            output_path=args.output,
            burn_subtitles=not args.no_subs
        )
        
        if success:
            log_success(f"Chúc mừng sếp! Video đã được tạo xong: {args.output}")
            sys.exit(0)
        else:
            log_error("Tiến trình tạo video thất bại.")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Đã xảy ra lỗi ngoài ý muốn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import win32gui
import win32con
import numpy as np
#  Pillow (PIL) 现在是核心功能的一部分
from PIL import Image, ImageGrab
import cv2
from plyer import notification
import keyboard
import threading
import time
import os
import winsound

# ... (之前的所有函数: get_visible_windows, capture_window, show_notification_thread, play_sound_async, setup_hotkey, remove_hotkey 都保持不变) ...
# 为了代码简洁，这里省略了未改动的旧代码，请将新函数添加到文件末尾即可。

def get_visible_windows():
    windows = {}
    def enum_windows_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip() != "" and "Program Manager" not in title:
                windows[title] = hwnd
    win32gui.EnumWindows(enum_windows_callback, None)
    return windows

def capture_window(hwnd):
    try:
        if win32gui.IsIconic(hwnd): return None
        rect = win32gui.GetWindowRect(hwnd)
        img = ImageGrab.grab(bbox=rect, all_screens=True)
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return frame
    except Exception:
        return None

def show_notification_thread(title, message):
    def run():
        notification.notify(title=title, message=message, app_name='PPTSlicer', timeout=4)
    threading.Thread(target=run, daemon=True).start()

def play_sound_async(sound_path):
    def run():
        if os.path.exists(sound_path):
            try:
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            except Exception as e:
                print(f"[-] 播放声音失败: {e}")
        else:
            print(f"[!] 声音文件未找到: {sound_path}")
    threading.Thread(target=run, daemon=True).start()

_current_hotkey = None
def setup_hotkey(key, callback):
    global _current_hotkey
    try:
        if _current_hotkey:
            try: keyboard.remove_hotkey(_current_hotkey)
            except KeyError: pass
        keyboard.add_hotkey(key, callback)
        _current_hotkey = key
        print(f"[+] 快捷键 '{key}' 已注册。")
        return True
    except Exception as e:
        print(f"[-] 注册快捷键 '{key}' 失败: {e}")
        return False

def remove_hotkey():
    global _current_hotkey
    if _current_hotkey:
        try: keyboard.remove_hotkey(_current_hotkey)
        except KeyError: pass
        finally: _current_hotkey = None

# ---------------------------------------------------
#  vvv 这是本次更新的核心 vvv
# ---------------------------------------------------
def export_images_to_pdf(image_folder, output_pdf_path):
    """
    将指定文件夹中的图片导出为单个PDF文件。
    :param image_folder: 包含图片的文件夹路径。
    :param output_pdf_path: 输出的PDF文件完整路径。
    """
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    image_files = sorted([
        os.path.join(image_folder, f) 
        for f in os.listdir(image_folder) 
        if f.lower().endswith(valid_extensions)
    ])

    if not image_files:
        raise FileNotFoundError("在指定文件夹中未找到任何有效的图片文件。")

    # 打开第一张图片以开始
    try:
        first_image = Image.open(image_files[0]).convert("RGB")
    except Exception as e:
        raise IOError(f"无法打开第一张图片: {image_files[0]}\n错误: {e}")

    # 打开剩余的图片
    other_images = []
    for image_path in image_files[1:]:
        try:
            img = Image.open(image_path).convert("RGB")
            other_images.append(img)
        except Exception as e:
            print(f"[警告] 跳过无法打开的图片: {image_path}, 错误: {e}")

    # 保存为PDF
    try:
        first_image.save(
            output_pdf_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=other_images
        )
    except Exception as e:
        raise IOError(f"保存PDF文件失败。\n错误: {e}")
# ---------------------------------------------------
#  ^^^ 这是本次更新的核心 ^^^
# ---------------------------------------------------

import threading
import time
import os
import cv2
import numpy as np
import utils
import logging

class MonitorThread(threading.Thread):
    def __init__(self, hwnd, save_path, threshold, hotkey, hotkey_timeout, is_auto_mode, status_callback, saved_callback):
        super().__init__(daemon=True, name="MonitorThread")
        self.hwnd = hwnd
        self.save_path = save_path
        self.hotkey = hotkey
        self.hotkey_timeout = hotkey_timeout
        # ---------------------------------------------------
        #  vvv 新增参数 vvv
        # ---------------------------------------------------
        self.is_auto_mode = is_auto_mode 
        # ---------------------------------------------------
        
        self.status_callback = status_callback
        self.saved_callback = saved_callback
        
        logging.info(f"MonitorThread 初始化... (全自动模式: {self.is_auto_mode})")
        
        initial_frame = utils.capture_window(self.hwnd)
        if initial_frame is None:
             error_msg = "无法捕获目标窗口，请确保窗口可见且未最小化。"
             logging.error(error_msg)
             raise ValueError(error_msg)
        
        height, width, _ = initial_frame.shape
        total_pixels_value = height * width * 255
        
        self.trigger_threshold = (threshold / 100.0) * total_pixels_value
        self.stable_threshold = 0.005 * total_pixels_value
        
        self.stop_event = threading.Event()
        self.previous_frame_gray = None
        self.pending_screenshot = None
        self.lock = threading.Lock()
        
        self.prompt_sound_path = os.path.join("notify", "10.wav")
        self.success_sound_path = os.path.join("notify", "22.wav")

    def run(self):
        """线程主循环"""
        logging.info("监控线程启动。")
        self.status_callback("状态：监控中..." + (" [全自动]" if self.is_auto_mode else ""))
        
        frame = utils.capture_window(self.hwnd)
        if frame is not None:
            self.previous_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        while not self.stop_event.is_set():
            time.sleep(0.5)
            
            frame = utils.capture_window(self.hwnd)
            if frame is None:
                self._handle_window_loss()
                break

            current_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if self.previous_frame_gray is not None:
                diff = cv2.absdiff(self.previous_frame_gray, current_frame_gray)
                diff_sum = np.sum(diff)

                if diff_sum > self.trigger_threshold:
                    if self.pending_screenshot is None:
                        logging.info(f"[!] 检测到翻页 (差异: {diff_sum:.0f})，等待静止...")
                        
                        stable_frame = self._wait_for_stable(current_frame_gray)
                        
                        if stable_frame is not None:
                            self._trigger_screenshot_process(stable_frame)
                            self.previous_frame_gray = cv2.cvtColor(stable_frame, cv2.COLOR_BGR2GRAY)
                        else:
                            logging.warning("等待超时。")
                            self.previous_frame_gray = current_frame_gray
                else:
                    self.previous_frame_gray = current_frame_gray

    def _wait_for_stable(self, last_gray_frame):
        start_time = time.time()
        max_wait_time = 4.0
        stable_count = 0
        required_stable_count = 2
        current_gray = last_gray_frame
        
        while time.time() - start_time < max_wait_time:
            time.sleep(0.1)
            frame = utils.capture_window(self.hwnd)
            if frame is None: return None
            new_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(current_gray, new_gray)
            diff_sum = np.sum(diff)
            
            if diff_sum < self.stable_threshold:
                stable_count += 1
                if stable_count >= required_stable_count:
                    logging.info("画面已稳定。")
                    return frame
            else:
                stable_count = 0
            current_gray = new_gray
            
        return frame

    def _trigger_screenshot_process(self, stable_frame):
        """根据模式决定是直接保存还是等待按键"""
        with self.lock:
            self.pending_screenshot = stable_frame.copy()

        # ---------------------------------------------------
        #  vvv 核心分流逻辑 vvv
        # ---------------------------------------------------
        if self.is_auto_mode:
            logging.info("全自动模式：直接保存截图。")
            # 直接调用保存，无需声音提示等待
            self.save_pending_screenshot()
        else:
            logging.info("手动模式：等待按键确认。")
            # 播放“请按键”的提示音
            utils.play_sound_async(self.prompt_sound_path)
            utils.setup_hotkey(self.hotkey, self.save_pending_screenshot)
            threading.Timer(self.hotkey_timeout, self.cancel_pending_screenshot).start()
        # ---------------------------------------------------

    def _handle_window_loss(self):
        logging.warning("窗口丢失。")
        self.status_callback("状态：目标窗口丢失，监控已停止。")
        utils.remove_hotkey()
        self.stop_event.set()

    def save_pending_screenshot(self):
        img_to_save = None
        with self.lock:
            if self.pending_screenshot is not None:
                img_to_save = self.pending_screenshot
                self.pending_screenshot = None
        
        utils.remove_hotkey()

        if img_to_save is not None:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.normpath(os.path.join(self.save_path, filename))

                is_success, buffer = cv2.imencode(".png", img_to_save)
                if is_success:
                    with open(filepath, 'wb') as f:
                        f.write(buffer)
                    logging.info(f"保存成功: {filepath}")
                    self.saved_callback()
                    # 无论自动还是手动，保存成功都播放成功音效
                    utils.play_sound_async(self.success_sound_path)
                else:
                    raise IOError("编码失败")
            except Exception as e:
                logging.error(f"保存失败: {e}")
                self.status_callback("状态：保存失败！")

    def cancel_pending_screenshot(self):
        with self.lock:
            if self.pending_screenshot is not None:
                logging.info("超时取消。")
                self.pending_screenshot = None
                utils.remove_hotkey()

    def stop(self):
        self.stop_event.set()
        utils.remove_hotkey()
import threading
import time
import os
import cv2
import numpy as np
import utils
import logging # 导入日志模块

class MonitorThread(threading.Thread):
    def __init__(self, hwnd, save_path, threshold, hotkey, hotkey_timeout, status_callback, saved_callback):
        super().__init__(daemon=True, name="MonitorThread") # 给线程命名
        self.hwnd = hwnd
        self.save_path = save_path
        self.hotkey = hotkey
        self.hotkey_timeout = hotkey_timeout
        self.status_callback = status_callback
        self.saved_callback = saved_callback
        
        logging.info("MonitorThread 初始化...")
        initial_frame = utils.capture_window(self.hwnd)
        if initial_frame is None:
             error_msg = "无法捕获目标窗口，请确保窗口可见且未最小化。"
             logging.error(error_msg)
             raise ValueError(error_msg)
        
        height, width, _ = initial_frame.shape
        total_pixels_value = height * width * 255
        self.threshold_value = (threshold / 100.0) * total_pixels_value
        logging.info(f"窗口尺寸: {width}x{height}。计算出的像素差异阈值: {self.threshold_value:.2f}")
        
        self.stop_event = threading.Event()
        self.previous_frame_gray = None
        self.pending_screenshot = None
        self.lock = threading.Lock()
        
        self.prompt_sound_path = os.path.join("notify", "10.wav")
        self.success_sound_path = os.path.join("notify", "22.wav")

    def run(self):
        """线程主循环"""
        logging.info("监控线程 'run' 方法开始执行。")
        self.status_callback("状态：监控中...")
        
        frame = utils.capture_window(self.hwnd)
        if frame is not None:
            self.previous_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.previous_frame_color = frame
        
        loop_count = 0
        while not self.stop_event.is_set():
            time.sleep(0.1)
            loop_count += 1
            logging.info(f"--- 监控循环 第 {loop_count} 次 ---")
            
            frame = utils.capture_window(self.hwnd)
            if frame is None:
                logging.warning("截图失败，可能窗口已关闭或最小化。正在停止线程...")
                self.status_callback("状态：目标窗口丢失，监控已停止。")
                utils.remove_hotkey()
                self.stop_event.set()
                continue

            current_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if self.previous_frame_gray is not None:
                # 核心计算
                diff = cv2.absdiff(self.previous_frame_gray, current_frame_gray)
                diff_sum = np.sum(diff)

                # 记录核心诊断信息
                logging.info(f"计算出的像素差异值 (diff_sum): {diff_sum}")
                
                # 检查条件
                if diff_sum > self.threshold_value:
                    if self.pending_screenshot is None:
                        logging.info(f"检测到显著变化！差异值 {diff_sum} > 阈值 {self.threshold_value:.2f}。触发截图流程！")
                        
                        with self.lock:
                            self.pending_screenshot = self.previous_frame_color.copy()

                        utils.play_sound_async(self.prompt_sound_path)
                        utils.setup_hotkey(self.hotkey, self.save_pending_screenshot)
                        threading.Timer(self.hotkey_timeout, self.cancel_pending_screenshot).start()
                    else:
                        logging.info("检测到变化，但有截图待处理，本次跳过。")
                else:
                    logging.info("画面无显著变化。")


            self.previous_frame_gray = current_frame_gray
            self.previous_frame_color = frame.copy()

        logging.info("监控线程主循环结束。")

    def save_pending_screenshot(self):
        logging.info("快捷键被按下，执行 save_pending_screenshot。")
        # ... (此函数内部逻辑不变, 但可以把print换成logging) ...
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
                    logging.info(f"截图已成功保存至: {filepath}")
                    self.saved_callback()
                    utils.play_sound_async(self.success_sound_path)
                else:
                    raise IOError("cv2.imencode 编码失败")
            except Exception as e:
                logging.error(f"保存截图失败: {e}", exc_info=True)
                self.status_callback("状态：保存失败！")

    def stop(self):
        logging.info("接收到停止信号，正在停止线程...")
        self.stop_event.set()
        utils.remove_hotkey()

    # 其他未改动的函数为了简洁省略
    def cancel_pending_screenshot(self):
        if self.pending_screenshot is not None:
             with self.lock:
                if self.pending_screenshot is not None:
                    logging.info("截图操作超时，已自动取消。")
                    self.pending_screenshot = None
                    utils.remove_hotkey()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import ctypes
import logging  # 导入日志模块

# ---------------------------------------------------
#  vvv 这是本次更新的核心 vvv
# ---------------------------------------------------
# --- 配置日志记录 ---
log_file = 'PPTSlicer.log'
# 如果日志文件已存在，先清空它，方便每次运行都得到干净的日志
if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(
    level=logging.INFO, # 设置日志级别为INFO，可以改为DEBUG获取更详细的信息
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        # 如果你希望在终端也看到日志（仅在非windowed模式下有用），可以取消下面一行的注释
        # logging.StreamHandler() 
    ]
)

logging.info("程序启动，日志系统已配置。")
# ---------------------------------------------------
#  ^^^ 这是本次更新的核心 ^^^
# ---------------------------------------------------

import utils
from monitor import MonitorThread
from config import load_settings, save_settings

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    logging.info("DPI感知设置成功。")
except Exception as e:
    logging.warning(f"DPI感知设置失败 (可能在旧版Windows上运行): {e}")

class MainApplication(tk.Tk):
    """主应用程序窗口 (v1.5-debug)"""
    def __init__(self):
        super().__init__()
        logging.info("MainApplication 初始化开始。")

        self.settings = load_settings()
        
        self.title("PPTSlicer v1.5 (Debug Mode)")
        self.geometry("480x420")
        self.resizable(False, False)

        self.window_handles = {}
        self.monitor_thread = None
        self.saved_count = 0
        self.hotkey = "ctrl"

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self._create_menu()

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill="both")

        self._create_widgets(main_frame)
        self._apply_settings()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        logging.info("MainApplication 初始化完成。")

    # ... 其他所有函数都保持不变，除了 _start_monitoring 和 _on_closing 中用 logging 替换 print ...

    def _start_monitoring(self):
        # ... (前置检查代码不变) ...
        selected_title = self.window_combo.get()
        save_path = self.path_var.get()
        if not selected_title or "请点击" in selected_title or "未找到" in selected_title:
            messagebox.showwarning("警告", "请先选择一个要监控的目标窗口！")
            return
        if not save_path or not os.path.isdir(save_path):
            messagebox.showwarning("警告", "请设置一个有效的截图保存路径！")
            return

        self.saved_count = 0
        try:
            hwnd = self.window_handles[selected_title]
            threshold = self.threshold_var.get()
            timeout = self.timeout_var.get()
            
            logging.info(f"准备启动监控线程。目标窗口: '{selected_title}' (HWND: {hwnd})")
            logging.info(f"保存路径: {save_path}, 灵敏度: {threshold}%, 超时: {timeout}s")
            
            self.monitor_thread = MonitorThread(
                hwnd, save_path, threshold, self.hotkey, timeout,
                self.update_status, self.increment_saved_count
            )
            self.monitor_thread.start()
            self._set_ui_state(monitoring=True)
        except Exception as e:
            logging.error(f"启动监控线程失败: {e}", exc_info=True) # exc_info=True 会记录完整的错误堆栈
            messagebox.showerror("启动失败", f"无法启动监控线程：\n{e}")

    def _on_closing(self):
        logging.info("接收到窗口关闭事件。")
        if self.monitor_thread and self.monitor_thread.is_alive():
            if messagebox.askokcancel("退出", "监控正在进行中，确定要退出吗？"):
                logging.info("用户确认退出，正在停止监控线程...")
                self.monitor_thread.stop()
                self.monitor_thread.join(timeout=1.2)
                save_settings(self._collect_settings())
                logging.info("配置已保存，正在销毁窗口。")
                self.destroy()
            else:
                logging.info("用户取消退出。")
        else:
            save_settings(self._collect_settings())
            logging.info("配置已保存，正在销毁窗口。")
            self.destroy()

    # 其他所有未改动的函数为了简洁省略，请保留您文件中的原样
    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出图片为PDF...", command=self._export_to_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)

    def _export_to_pdf(self):
        self.update_status("状态：请选择包含图片的文件夹...")
        image_folder = filedialog.askdirectory(title="选择包含图片的文件夹", initialdir=self.path_var.get() or os.path.expanduser("~"))
        if not image_folder:
            self.update_status("状态：导出已取消。")
            return
        self.update_status("状态：请指定要保存的PDF文件...")
        output_pdf_path = filedialog.asksaveasfilename(title="保存PDF文件为...", initialdir=image_folder, defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if not output_pdf_path:
            self.update_status("状态：导出已取消。")
            return
        self.update_status("状态：正在导出PDF，请稍候...")
        self.update_idletasks()
        try:
            utils.export_images_to_pdf(image_folder, output_pdf_path)
            self.update_status(f"状态：PDF导出成功！")
            messagebox.showinfo("成功", f"所有图片已成功导出为：\n{os.path.basename(output_pdf_path)}")
        except Exception as e:
            self.update_status("状态：导出失败！")
            messagebox.showerror("导出失败", str(e))

    def _create_widgets(self, parent_frame):
        parent_frame.columnconfigure(1, weight=1)
        ttk.Label(parent_frame, text="目标窗口:").grid(row=0, column=0, sticky="w", pady=5)
        self.window_combo = ttk.Combobox(parent_frame, state="readonly")
        self.window_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(5, 0))
        self.refresh_button = ttk.Button(parent_frame, text="刷新", command=self._refresh_window_list)
        self.refresh_button.grid(row=0, column=2, sticky="e", pady=5, padx=(5, 0))
        self.window_combo['values'] = ["请点击刷新获取窗口列表..."]
        self.window_combo.current(0)
        ttk.Label(parent_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=5)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(parent_frame, state="readonly", textvariable=self.path_var)
        self.path_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(5, 0))
        self.browse_button = ttk.Button(parent_frame, text="浏览...", command=self._browse_save_path)
        self.browse_button.grid(row=1, column=2, sticky="e", pady=5, padx=(5, 0))
        ttk.Label(parent_frame, text="检测灵敏度:").grid(row=2, column=0, sticky="w", pady=(15, 5))
        thresh_frame = ttk.Frame(parent_frame)
        thresh_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(15, 5), padx=(5, 0))
        thresh_frame.columnconfigure(0, weight=1)
        self.threshold_var = tk.DoubleVar()
        self.threshold_scale = ttk.Scale(thresh_frame, from_=0.1, to=20.0, orient="horizontal", variable=self.threshold_var, command=self._update_threshold_label)
        self.threshold_scale.grid(row=0, column=0, sticky="ew")
        self.threshold_label = ttk.Label(thresh_frame, text="", width=6)
        self.threshold_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
        ttk.Label(parent_frame, text="快捷键超时(秒):").grid(row=3, column=0, sticky="w", pady=5)
        self.timeout_var = tk.IntVar()
        self.timeout_spinbox = ttk.Spinbox(parent_frame, from_=1, to=10, width=5, textvariable=self.timeout_var)
        self.timeout_spinbox.grid(row=3, column=1, sticky="w", pady=5, padx=(5, 0))
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(20, 10))
        self.start_button = ttk.Button(button_frame, text="开始监控", command=self._start_monitoring)
        self.start_button.pack(side="left", padx=10, ipadx=10, ipady=5)
        self.stop_button = ttk.Button(button_frame, text="停止监控", command=self._stop_monitoring, state="disabled")
        self.stop_button.pack(side="right", padx=10, ipadx=10, ipady=5)
        self.status_var = tk.StringVar(value="状态：待机中")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=5)
        status_bar.pack(side="bottom", fill="x")

    def _apply_settings(self):
        self.path_var.set(self.settings.get("save_path", ""))
        self.threshold_var.set(self.settings.get("threshold", 5.0))
        self.timeout_var.set(self.settings.get("hotkey_timeout", 5))
        self._update_threshold_label(self.threshold_var.get())

    def _collect_settings(self):
        return {"save_path": self.path_var.get(), "threshold": self.threshold_var.get(), "hotkey_timeout": self.timeout_var.get()}

    def _refresh_window_list(self):
        self.update_status("状态：正在刷新窗口列表...")
        self.update_idletasks()
        self.window_handles = utils.get_visible_windows()
        window_titles = list(self.window_handles.keys())
        if window_titles:
            self.window_combo['values'] = window_titles
            self.window_combo.current(0)
            self.update_status(f"状态：找到 {len(window_titles)} 个窗口。")
        else:
            self.window_combo['values'] = ["未找到可用窗口"]
            self.window_combo.current(0)
            self.update_status("状态：未找到可用窗口。")

    def _browse_save_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get() or os.path.expanduser("~"))
        if path:
            self.path_var.set(path)
            self.update_status(f"状态：保存路径已设置。")

    def _update_threshold_label(self, value):
        self.threshold_label.config(text=f"{float(value):.1f}%")

    def _stop_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
        self._set_ui_state(monitoring=False)

    def _set_ui_state(self, monitoring: bool):
        state = "disabled" if monitoring else "normal"
        self.start_button.config(state="disabled" if monitoring else "normal")
        self.stop_button.config(state="normal" if monitoring else "disabled")
        for widget in [self.refresh_button, self.browse_button, self.threshold_scale, self.timeout_spinbox]:
            widget.config(state=state)
        self.menu_bar.entryconfig("文件", state=state)
        if not monitoring:
            self.after(200, lambda: self.update_status("状态：监控已停止。"))

    def update_status(self, message):
        self.status_var.set(message)
        
    def increment_saved_count(self):
        self.saved_count += 1
        self.update_status(f"状态：已保存 {self.saved_count} 张截图。")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
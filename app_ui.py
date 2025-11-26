import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import ctypes
import logging
import utils
from monitor import MonitorThread
from config import load_settings, save_settings

# --- 配置日志 ---
log_file = 'PPTSlicer.log'
# 每次启动前清空旧日志，保持清爽
if os.path.exists(log_file): 
    try:
        os.remove(log_file)
    except Exception:
        pass # 如果文件被占用则跳过

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file, encoding='utf-8')])

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception: pass

class MainApplication(tk.Tk):
    """主应用程序窗口 (v1.7-UI-Fix)"""
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        
        self.title("PPTSlicer v1.7 (Auto Mode)")
        
        # ---------------------------------------------------
        #  vvv 修复点：增加宽度，允许水平拉伸 vvv
        # ---------------------------------------------------
        self.geometry("620x460") # 宽度从480增加到620，高度微调
        self.resizable(True, False) # 允许水平调整大小(True)，禁止垂直调整(False)
        # ---------------------------------------------------

        self.window_handles = {}
        self.monitor_thread = None
        self.saved_count = 0
        self.hotkey = "ctrl"

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self._create_menu()

        main_frame = ttk.Frame(self, padding="20") # 增加一点边距让界面更舒展
        main_frame.pack(expand=True, fill="both")

        self._create_widgets(main_frame)
        self._apply_settings()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self, parent_frame):
        # 关键：配置第1列（中间列）权重为1，让其自动填充剩余空间
        parent_frame.columnconfigure(1, weight=1)
        
        # 1. 窗口选择区域
        ttk.Label(parent_frame, text="目标窗口:").grid(row=0, column=0, sticky="w", pady=8)
        self.window_combo = ttk.Combobox(parent_frame, state="readonly")
        # sticky="ew" 确保控件横向填满单元格
        self.window_combo.grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 10))
        self.refresh_button = ttk.Button(parent_frame, text="刷新列表", width=10, command=self._refresh_window_list)
        self.refresh_button.grid(row=0, column=2, sticky="e", pady=8)
        self.window_combo['values'] = ["请点击刷新..."]
        self.window_combo.current(0)
        
        # 2. 保存路径区域
        ttk.Label(parent_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=8)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(parent_frame, state="readonly", textvariable=self.path_var)
        self.path_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 10))
        self.browse_button = ttk.Button(parent_frame, text="浏览...", width=10, command=self._browse_save_path)
        self.browse_button.grid(row=1, column=2, sticky="e", pady=8)
        
        # 3. 灵敏度区域
        ttk.Label(parent_frame, text="检测灵敏度:").grid(row=2, column=0, sticky="w", pady=(20, 8))
        thresh_frame = ttk.Frame(parent_frame)
        thresh_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(20, 8), padx=(10, 0))
        thresh_frame.columnconfigure(0, weight=1)
        self.threshold_var = tk.DoubleVar()
        self.threshold_scale = ttk.Scale(thresh_frame, from_=0.1, to=20.0, orient="horizontal", variable=self.threshold_var, command=self._update_threshold_label)
        self.threshold_scale.grid(row=0, column=0, sticky="ew")
        self.threshold_label = ttk.Label(thresh_frame, text="", width=6)
        self.threshold_label.grid(row=0, column=1, sticky="e", padx=(10, 0))
        
        # 4. 超时 & 自动模式
        ttk.Label(parent_frame, text="快捷键超时(秒):").grid(row=3, column=0, sticky="w", pady=8)
        
        # 创建一个小框架来放超时设置和自动模式勾选框，以便布局更整齐
        settings_sub_frame = ttk.Frame(parent_frame)
        settings_sub_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=8, padx=(10, 0))
        
        self.timeout_var = tk.IntVar()
        self.timeout_spinbox = ttk.Spinbox(settings_sub_frame, from_=1, to=10, width=5, textvariable=self.timeout_var)
        self.timeout_spinbox.pack(side="left")

        self.auto_mode_var = tk.BooleanVar()
        self.auto_mode_check = ttk.Checkbutton(
            settings_sub_frame, 
            text="全自动模式 (无需确认)", 
            variable=self.auto_mode_var,
            command=self._toggle_auto_mode_ui
        )
        self.auto_mode_check.pack(side="left", padx=(20, 0))

        # 5. 底部大按钮区域
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(30, 10))
        
        # 加大按钮尺寸
        self.start_button = ttk.Button(button_frame, text="开始监控", command=self._start_monitoring)
        self.start_button.pack(side="left", padx=20, ipadx=20, ipady=8)
        self.stop_button = ttk.Button(button_frame, text="停止监控", command=self._stop_monitoring, state="disabled")
        self.stop_button.pack(side="right", padx=20, ipadx=20, ipady=8)
        
        self.status_var = tk.StringVar(value="状态：待机中")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=8)
        status_bar.pack(side="bottom", fill="x")

    def _toggle_auto_mode_ui(self):
        """当勾选全自动模式时，禁用超时设置"""
        is_auto = self.auto_mode_var.get()
        state = "disabled" if is_auto else "normal"
        self.timeout_spinbox.config(state=state)

    def _apply_settings(self):
        self.path_var.set(self.settings.get("save_path", ""))
        self.threshold_var.set(self.settings.get("threshold", 5.0))
        self.timeout_var.set(self.settings.get("hotkey_timeout", 5))
        self.auto_mode_var.set(self.settings.get("auto_mode", False)) 
        self._update_threshold_label(self.threshold_var.get())
        self._toggle_auto_mode_ui() 

    def _collect_settings(self):
        return {
            "save_path": self.path_var.get(),
            "threshold": self.threshold_var.get(),
            "hotkey_timeout": self.timeout_var.get(),
            "auto_mode": self.auto_mode_var.get() 
        }

    def _start_monitoring(self):
        selected_title = self.window_combo.get()
        save_path = self.path_var.get()
        if not selected_title or "请点击" in selected_title:
            messagebox.showwarning("警告", "请选择目标窗口！")
            return
        if not save_path or not os.path.isdir(save_path):
            messagebox.showwarning("警告", "路径无效！")
            return

        self.saved_count = 0
        try:
            hwnd = self.window_handles[selected_title]
            self.monitor_thread = MonitorThread(
                hwnd, save_path, 
                self.threshold_var.get(), 
                self.hotkey, 
                self.timeout_var.get(),
                self.auto_mode_var.get(), 
                self.update_status, 
                self.increment_saved_count
            )
            self.monitor_thread.start()
            self._set_ui_state(monitoring=True)
        except Exception as e:
            logging.error(f"启动失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"无法启动监控: {e}")

    def _stop_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
        self._set_ui_state(monitoring=False)

    def _set_ui_state(self, monitoring: bool):
        state = "disabled" if monitoring else "normal"
        self.start_button.config(state="disabled" if monitoring else "normal")
        self.stop_button.config(state="normal" if monitoring else "disabled")
        
        for widget in [self.refresh_button, self.browse_button, self.threshold_scale, self.auto_mode_check]:
            widget.config(state=state)
            
        if not monitoring and not self.auto_mode_var.get():
             self.timeout_spinbox.config(state="normal")
        else:
             self.timeout_spinbox.config(state="disabled")

        self.menu_bar.entryconfig("文件", state=state)
        if not monitoring:
            self.after(200, lambda: self.update_status("状态：监控已停止。"))

    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出图片为PDF...", command=self._export_to_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)

    def _export_to_pdf(self):
        image_folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if not image_folder: return
        output_pdf = filedialog.asksaveasfilename(initialdir=image_folder, defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not output_pdf: return
        self.update_status("正在导出PDF...")
        self.update_idletasks()
        try:
            utils.export_images_to_pdf(image_folder, output_pdf)
            messagebox.showinfo("成功", "PDF导出成功！")
            self.update_status("导出成功。")
        except Exception as e:
            messagebox.showerror("失败", str(e))
            self.update_status("导出失败。")

    def _refresh_window_list(self):
        self.update_idletasks()
        self.window_handles = utils.get_visible_windows()
        titles = list(self.window_handles.keys())
        if titles:
            self.window_combo['values'] = titles
            self.window_combo.current(0)
            self.update_status(f"找到 {len(titles)} 个窗口。")
        else:
            self.window_combo['values'] = ["未找到"]
            self.update_status("未找到窗口。")

    def _browse_save_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get() or os.path.expanduser("~"))
        if path: self.path_var.set(path)

    def _update_threshold_label(self, value):
        self.threshold_label.config(text=f"{float(value):.1f}%")

    def _on_closing(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            if messagebox.askokcancel("退出", "监控中，确定退出？"):
                self.monitor_thread.stop()
                self.monitor_thread.join(timeout=1)
                save_settings(self._collect_settings())
                self.destroy()
        else:
            save_settings(self._collect_settings())
            self.destroy()

    def update_status(self, message):
        self.status_var.set(message)
        
    def increment_saved_count(self):
        self.saved_count += 1
        self.update_status(f"已保存 {self.saved_count} 张。")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
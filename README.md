
# 📝 PPTSlicer

**适用于 Windows 的智能 PPT 自动截图与笔记整理工具。**

PPTSlicer 是一个轻量级的 Python 桌面应用程序，专为学生、教师和会议记录者设计。它能在后台静默监控 PPT 演示窗口，自动识别幻灯片翻页，智能去除动画过渡干扰，并自动截取清晰的静态画面保存到本地，甚至支持一键导出为 PDF。

---

## ✨ 核心功能

*   **🧠 智能监控**: 自动识别指定窗口（如 PowerPoint 放映窗口）的画面变化。
*   **⚖️ 视觉稳定机制**: 独创的“静止检测”算法，自动忽略 PPT 翻页动画和过渡效果，仅在画面完全静止时截图，确保图片清晰无残影。
*   **🚀 全自动模式**: 勾选后无需人工干预，翻页即自动保存截图，彻底解放双手。
*   **🎹 手动确认模式**: 支持快捷键（`Ctrl`）确认截图，提供音效反馈（提示音/成功音），避免误触。
*   **📂 PDF 一键导出**: 内置工具可将截取的图片文件夹一键合并为 PDF 文档，方便复习与分享。
*   **🖥️ 高 DPI 支持**: 完美适配 Windows 高分辨率屏幕，截图不模糊、不残缺。
*   **💾 配置记忆**: 自动保存上次的保存路径、灵敏度阈值等设置。

---

## ⚠️ 系统要求

*   **操作系统**: **Windows 11**
    *   *注意：本项目依赖于特定的 Windows API 和 DPI 缩放行为，仅在 Windows 11 环境下经过完整测试。*
*   **运行环境**: 无需安装 Python，直接运行 Release 中的 `.exe` 文件即可。

---

## 📥 下载与安装

1.  访问本仓库的 [**Releases**](https://github.com/您的用户名/PPTSlicer/releases) 页面（*请替换为您实际的仓库链接*）。
2.  下载最新的 `PPTSlicer.zip` 压缩包。
3.  解压到任意文件夹。
4.  双击 `PPTSlicer.exe` 即可运行。

---

## 📖 使用指南

### 1. 准备工作
*   打开您的 PPT 文件并开始放映（推荐使用“阅读视图”或“幻灯片放映”模式）。
*   运行 `PPTSlicer.exe`。

### 2. 软件设置
*   **目标窗口**: 点击“刷新列表”，在下拉菜单中选择您的 PPT 放映窗口。
*   **保存路径**: 点击“浏览”选择截图的保存文件夹。
*   **检测灵敏度**: 默认为 5.0%，通常无需调整。如果 PPT 背景变化极小，可适当调低数值。

### 3. 模式选择
*   **全自动模式 (推荐)**: 勾选界面上的“全自动模式”。软件检测到翻页并等待动画结束后，会自动保存截图并播放成功音效。
*   **手动模式**: 不勾选全自动模式。翻页后软件会播放提示音（`notify/10.wav`），此时按下 `Ctrl` 键确认保存，保存成功后播放成功音效（`notify/22.wav`）。

### 4. 导出 PDF
*   截图完成后，点击菜单栏的 **文件 -> 导出图片为PDF...**。
*   选择包含截图的文件夹，即可生成包含所有幻灯片的 PDF 文件。

---

## 🛠️ 开发与构建

如果您希望从源码运行或自行修改代码，请参考以下步骤：

### 环境依赖
*   Python 3.10+
*   建议使用 Conda 或 venv 创建虚拟环境

### 安装依赖库
```bash
pip install opencv-python numpy pillow plyer keyboard pywin32
项目结构
Text
PPTSlicer/
├── app_ui.py           # GUI 主入口
├── monitor.py          # 核心监控线程与图像处理逻辑
├── utils.py            # 辅助工具函数 (截图、PDF导出、路径处理)
├── config.py           # 配置文件管理
├── assets/             # 图标资源
│   └── icon.ico
├── notify/             # 音效文件
│   ├── 10.wav          # 提示音
│   └── 22.wav          # 成功音
├── PPTSlicer.spec      # PyInstaller 打包配置文件
└── settings.json       # 用户配置文件 (自动生成)
源码运行
bash
python app_ui.py
打包为 Exe
本项目使用 PyInstaller 进行打包，并已配置好 .spec 文件以处理 OpenCV 和 Numpy 的依赖问题。

bash
# 确保已安装 pyinstaller
pip install pyinstaller

# 清理旧构建 (可选)
# rm -rf build dist

# 执行打包
pyinstaller PPTSlicer.spec
📄 许可证
MIT License
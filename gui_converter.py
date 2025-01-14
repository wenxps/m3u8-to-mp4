import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QProgressBar, 
                           QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import ffmpeg
from m3u8_to_mp4 import download_m3u8_to_mp4  # 导入实际的转换函数

# 添加全局缓存
_ffmpeg_initialized = False

class ConversionThread(QThread):
    progress = pyqtSignal(float)  # 进度信号
    status = pyqtSignal(str)      # 状态信息信号
    finished = pyqtSignal(bool, str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            self.status.emit("开始转换...")
            # 使用导入的转换函数
            download_m3u8_to_mp4(self.input_path, self.output_path, self.update_progress)
            self.finished.emit(True, "转换完成！")
        except Exception as e:
            self.finished.emit(False, str(e))

    def update_progress(self, progress_value):
        self.progress.emit(progress_value)

class M3U8Converter(QMainWindow):
    def __init__(self):
        super().__init__()
        # 延迟初始化UI
        QTimer.singleShot(0, self.initUI)
        self.conversion_thread = None
        
    def initUI(self):
        self.setWindowTitle('M3U8转MP4工具')
        self.setFixedSize(500, 350)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # M3U8输入
        self.input_label = QLabel('M3U8文件路径或URL:')
        layout.addWidget(self.input_label)
        
        self.input_path = QLineEdit()
        layout.addWidget(self.input_path)
        
        self.browse_input = QPushButton('浏览文件...')
        self.browse_input.clicked.connect(self.browse_input_file)
        layout.addWidget(self.browse_input)

        # MP4输出
        self.output_label = QLabel('MP4输出路径:')
        layout.addWidget(self.output_label)
        
        self.output_path = QLineEdit()
        layout.addWidget(self.output_path)
        
        self.browse_output = QPushButton('选择保存位置...')
        self.browse_output.clicked.connect(self.browse_output_file)
        layout.addWidget(self.browse_output)

        # 转换按钮
        self.convert_btn = QPushButton('开始转换')
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.convert_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel('就绪')
        layout.addWidget(self.status_label)

        self.show()

    def browse_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择M3U8文件", "", "M3U8文件 (*.m3u8);;所有文件 (*.*)")
        if file_name:
            self.input_path.setText(file_name)
            # 自动设置输出文件名
            if not self.output_path.text():
                output_name = os.path.splitext(file_name)[0] + '.mp4'
                self.output_path.setText(output_name)

    def browse_output_file(self):
        default_name = ''
        if self.input_path.text():
            input_name = os.path.basename(self.input_path.text())
            default_name = os.path.splitext(input_name)[0] + '.mp4'
            
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存MP4文件", default_name, "MP4文件 (*.mp4)")
        if file_name:
            self.output_path.setText(file_name)

    def start_conversion(self):
        input_path = self.input_path.text().strip()
        output_path = self.output_path.text().strip()

        if not input_path or not output_path:
            QMessageBox.warning(self, '错误', '请填写输入和输出路径')
            return

        # 检查输出目录是否存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法创建输出目录: {str(e)}')
                return

        # 禁用按钮
        self.browse_input.setEnabled(False)
        self.browse_output.setEnabled(False)
        self.convert_btn.setEnabled(False)
        self.input_path.setEnabled(False)
        self.output_path.setEnabled(False)

        # 创建并启动转换线程
        self.conversion_thread = ConversionThread(input_path, output_path)
        self.conversion_thread.progress.connect(self.update_progress)
        self.conversion_thread.status.connect(self.update_status)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))
        self.status_label.setText(f'转换进度: {value:.1f}%')

    def update_status(self, message):
        self.status_label.setText(message)

    def conversion_finished(self, success, message):
        # 重新启用按钮
        self.browse_input.setEnabled(True)
        self.browse_output.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.input_path.setEnabled(True)
        self.output_path.setEnabled(True)

        if success:
            QMessageBox.information(self, '完成', message)
            self.progress_bar.setValue(100)
            # 清空输入框，保留输出目录
            self.input_path.clear()
            last_dir = os.path.dirname(self.output_path.text())
            self.output_path.clear()
            if last_dir:
                self.output_path.setText(last_dir + '/')
        else:
            QMessageBox.critical(self, '错误', f'转换失败: {message}')
            self.progress_bar.setValue(0)
        
        self.status_label.setText('就绪')

def main():
    # 设置高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格，更现代的外观
    
    # 设置应用程序范围的样式表
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QLabel {
            font-size: 12px;
        }
        QLineEdit {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
            background-color: white;
        }
        QPushButton {
            padding: 5px 10px;
            border: none;
            border-radius: 3px;
            background-color: #2196F3;
            color: white;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:disabled {
            background-color: #ccc;
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
    """)
    
    ex = M3U8Converter()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

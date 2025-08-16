import sys
import os
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QRadioButton, 
                            QLineEdit, QProgressBar, QTextEdit, QHBoxLayout, 
                            QMessageBox, QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal

class CommandWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)

    def __init__(self, params, script_dir):
        super().__init__()
        self.params = params
        self.script_dir = script_dir

    def run(self):
        try:
            mode = self.params["mode"]
            process_method = self.params["process_method"]
            path = self.params["path"]
            
            if mode in ["install", "install_vs"]:
                # 安装模式
                version = self.params["version"]
                console_type = "2" if mode == "install_vs" else ("0" if mode == "install_noconsole" else "1")
                
                if process_method == "batch":
                    self.log_message.emit("开始批量处理地图文件夹...")
                    self.progress.emit(20, "扫描地图文件")
                    
                    # 找到所有地图文件
                    map_files = self.find_maps(path)
                    total = len(map_files)
                    
                    if not map_files:
                        raise ValueError("在指定文件夹中找不到地图文件")
                        
                    for i, map_file in enumerate(map_files):
                        progress = 20 + int(70 * i / total)
                        self.progress.emit(progress, f"处理地图: {map_file.name}")
                        self.execute_bat("install.bat", version, console_type, str(map_file))
                
                else:  # 单个地图处理
                    self.progress.emit(20, "处理单个地图文件")
                    self.execute_bat("install.bat", version, console_type, path)
            
            elif mode == "uninstall_console":
                # 卸载控制台
                if process_method == "batch":
                    map_files = self.find_maps(path)
                    total = len(map_files)
                    
                    for i, map_file in enumerate(map_files):
                        progress = int(100 * i / total)
                        self.progress.emit(progress, f"从 {map_file.name} 移除控制台")
                        self.execute_bat("uninstall_console.bat", str(map_file))
                else:
                    self.progress.emit(50, "从单个地图移除控制台")
                    self.execute_bat("uninstall_console.bat", path)
            
            elif mode == "uninstall_all":
                # 完全卸载
                if process_method == "batch":
                    map_files = self.find_maps(path)
                    total = len(map_files)
                    
                    for i, map_file in enumerate(map_files):
                        progress = int(100 * i / total)
                        self.progress.emit(progress, f"从 {map_file.name} 完全卸载AMAI")
                        self.execute_bat("uninstall_all.bat", str(map_file))
                else:
                    self.progress.emit(50, "从单个地图完全卸载AMAI")
                    self.execute_bat("uninstall_all.bat", path)
            
            self.progress.emit(100, "操作完成")
            self.finished.emit(True, "操作成功完成!")
            
        except Exception as e:
            self.finished.emit(False, f"错误: {str(e)}")

    def find_maps(self, folder):
        """在指定文件夹中查找所有地图文件"""
        maps = []
        for ext in ("*.w3x", "*.w3m"):
            maps.extend(Path(folder).glob(ext))
        return maps

    def execute_bat(self, bat_name, *args):
        """执行外部批处理脚本"""
        bat_path = os.path.join(self.script_dir, bat_name)
        
        if not os.path.exists(bat_path):
            raise FileNotFoundError(f"脚本文件不存在: {bat_path}")
        
        command = [bat_path]
        command.extend(args)
        
        self.log_message.emit(f"执行命令: {' '.join(command)}")
        
        try:
            # 执行批处理脚本
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 记录输出
            if result.stdout:
                self.log_message.emit(result.stdout)
            if result.stderr:
                self.log_message.emit(f"错误: {result.stderr}")
                
            # 检查返回码
            if result.returncode != 0:
                raise RuntimeError(f"脚本执行失败, 返回码: {result.returncode}")
                
        except Exception as e:
            raise RuntimeError(f"执行脚本失败: {str(e)}")

class AMAIInstaller(QMainWindow):
    def __init__(self, script_dir):
        super().__init__()
        self.setWindowTitle("AMAI 安装工具")
        self.setGeometry(100, 100, 600, 500)
        
        # 设置窗口图标
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.script_dir = script_dir
        self.setup_ui()
        self.params = {
            "mode": "install",
            "process_method": "batch",
            "version": "REFORGED",
            "path": ""
        }

    def setup_ui(self):
        # 创建表单布局
        form_layout = QVBoxLayout()
        
        # 操作模式
        form_layout.addWidget(QLabel("操作模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "安装 AMAI (标准控制台)",
            "安装 AMAI (对战暴雪AI控制台)",
            "安装 AMAI (不安装控制台)",
            "移除 AMAI 控制台",
            "完全卸载 AMAI"
        ])
        self.mode_combo.currentIndexChanged.connect(self.update_mode)
        form_layout.addWidget(self.mode_combo)
        
        # 处理方式
        form_layout.addWidget(QLabel("处理方式:"))
        
        method_layout = QHBoxLayout()
        self.batch_radio = QRadioButton("批量处理 (文件夹)")
        self.single_radio = QRadioButton("单个地图")
        self.batch_radio.setChecked(True)
        method_layout.addWidget(self.batch_radio)
        method_layout.addWidget(self.single_radio)
        form_layout.addLayout(method_layout)
        
        # 魔兽版本 (只在安装模式下显示)
        self.version_layout = QVBoxLayout()
        self.version_layout.addWidget(QLabel("魔兽版本:"))
        self.version_combo = QComboBox()
        self.version_combo.addItems([
            "重制版 (1.33+)",
            "经典版: 冰封王座 (1.24e+)",
            "经典版: 混乱之治 (1.24e-1.31)"
        ])
        self.version_layout.addWidget(self.version_combo)
        form_layout.addLayout(self.version_layout)
        
        # 路径选择
        form_layout.addWidget(QLabel("地图位置:"))
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_button = QPushButton("浏览...")
        self.path_button.clicked.connect(self.select_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_button)
        form_layout.addLayout(path_layout)
        
        # 脚本位置显示
        form_layout.addWidget(QLabel(f"脚本位置: {self.script_dir}"))
        
        # 进度条
        self.progress_bar = QProgressBar()
        form_layout.addWidget(self.progress_bar)
        
        # 日志区域
        form_layout.addWidget(QLabel("操作日志:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        form_layout.addWidget(self.log_output)
        
        # 执行按钮
        self.execute_button = QPushButton("执行")
        self.execute_button.clicked.connect(self.execute)
        self.execute_button.setMinimumHeight(40)
        form_layout.addWidget(self.execute_button)
        
        # 添加到主布局
        self.main_layout.addLayout(form_layout)
        
        self.worker = None
        self.update_mode(0)  # 初始化模式

    def update_mode(self, index):
        modes = ["install", "install_vs", "install_noconsole", "uninstall_console", "uninstall_all"]
        self.params["mode"] = modes[index]
        
        # 只在安装模式下显示版本选择
        if index < 3:  # 安装模式
            for i in range(self.version_layout.count()):
                widget = self.version_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
        else:  # 卸载模式
            for i in range(self.version_layout.count()):
                widget = self.version_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)

    def select_path(self):
        if self.batch_radio.isChecked():
            folder = QFileDialog.getExistingDirectory(self, "选择地图文件夹")
            if folder:
                self.path_input.setText(folder)
                self.params["path"] = folder
        else:
            file, _ = QFileDialog.getOpenFileName(
                self, "选择地图文件", "", "魔兽地图文件 (*.w3x *.w3m)"
            )
            if file:
                self.path_input.setText(file)
                self.params["path"] = file

    def validate(self):
        # 检查路径是否有效
        if not self.params["path"]:
            QMessageBox.warning(self, "路径无效", "请选择有效的地图文件或文件夹路径")
            return False
        
        if self.batch_radio.isChecked():
            if not os.path.isdir(self.params["path"]):
                QMessageBox.warning(self, "文件夹无效", "批量处理需要选择有效的文件夹")
                return False
        else:
            if not os.path.isfile(self.params["path"]):
                QMessageBox.warning(self, "文件无效", "请选择有效的地图文件")
                return False
            if not self.params["path"].lower().endswith(('.w3x', '.w3m')):
                QMessageBox.warning(self, "文件类型错误", "所选文件不是魔兽地图文件 (.w3x 或 .w3m)")
                return False
        
        # 处理方式
        self.params["process_method"] = "batch" if self.batch_radio.isChecked() else "single"
        
        # 安装模式下需要版本
        if self.params["mode"] in ["install", "install_vs", "install_noconsole"]:
            version_map = ["REFORGED", "TFT", "ROC"]
            self.params["version"] = version_map[self.version_combo.currentIndex()]
        
        return True

    def execute(self):
        if not self.validate():
            return
            
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "操作进行中", "当前已有操作在执行中，请等待完成")
            return
            
        # 重置界面
        self.progress_bar.reset()
        self.log_output.clear()
        self.log_output.append("开始操作...")
        self.set_ui_enabled(False)
        
        # 创建工作线程
        self.worker = CommandWorker(self.params, self.script_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.log_message.connect(self.add_log_message)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.log_output.append(message)

    def add_log_message(self, message):
        self.log_output.append(message)

    def operation_finished(self, success, message):
        self.log_output.append(message)
        self.set_ui_enabled(True)
        
        if success:
            QMessageBox.information(self, "操作成功", "操作已成功完成")
        else:
            QMessageBox.critical(self, "操作失败", f"操作遇到错误:\n{message}")

    def set_ui_enabled(self, enabled):
        self.mode_combo.setEnabled(enabled)
        self.batch_radio.setEnabled(enabled)
        self.single_radio.setEnabled(enabled)
        self.version_combo.setEnabled(enabled)
        self.path_input.setEnabled(enabled)
        self.path_button.setEnabled(enabled)
        self.execute_button.setEnabled(enabled)

def get_script_directory():
    """获取脚本目录（与主程序相同）"""
    # 如果程序被打包成单文件，使用可执行文件所在目录
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # 否则使用脚本文件所在目录
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 使用简洁风格
    app.setStyle("Fusion")
    
    # 获取脚本目录（与主程序相同）
    script_dir = get_script_directory()
    
    # 创建并显示窗口
    window = AMAIInstaller(script_dir)
    window.show()
    
    # 主循环
    sys.exit(app.exec_())

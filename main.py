import sys
import os
import subprocess
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox, QComboBox, 
                            QLabel, QPushButton, QFileDialog, QRadioButton, QButtonGroup,
                            QLineEdit, QProgressBar, QTextEdit, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal

class CommandWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            # 实现Git工作流
            repo_path = Path(".amai_temp")
            if repo_path.exists():
                shutil.rmtree(repo_path)
            
            self.progress.emit(10, "Cloning AI repository...")
            subprocess.run(["git", "clone", "https://github.com/amai-repository", ".amai_temp"], check=True)
            
            self.progress.emit(30, "Preparing files...")
            os.chdir(".amai_temp")
            
            # 根据用户选择执行操作
            mode = self.params["mode"]
            if mode in ["install", "install_vs"]:
                version = self.params["version"]
                console = "vs" if mode == "install_vs" else "regular"
                
                if self.params["process_method"] == "batch":
                    self.progress.emit(40, "Processing batch folder...")
                    for map_file in self.find_maps(self.params["path"]):
                        self.process_map(map_file, version, console)
                else:
                    self.progress.emit(40, "Processing single map...")
                    self.process_map(self.params["path"], version, console)
            
            elif mode == "uninstall_console":
                # 控制台卸载逻辑
                pass
                
            elif mode == "uninstall_all":
                # 完全卸载逻辑
                pass
                
            self.progress.emit(90, "Cleaning up...")
            os.chdir("..")
            shutil.rmtree(repo_path)
            
            self.finished.emit(True, "Operation completed successfully!")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

    def find_maps(self, folder):
        maps = []
        for ext in ["*.w3x", "*.w3m"]:
            maps.extend(Path(folder).glob(ext))
        return maps

    def process_map(self, map_path, version, console):
        map_path = Path(map_path)
        self.progress.emit(50, f"Processing {map_path.name}...")
        # 这里添加实际的地图处理逻辑
        # 例如: subprocess.run(["./install_script", version, console, str(map_path)])
        pass

class AMAIInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMAI Installation Tool")
        self.setGeometry(100, 100, 800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()
        self.params = {
            "mode": "install",
            "process_method": "batch",
            "version": "REFORGED",
            "path": ""
        }
        
        self.check_git()

    def check_git(self):
        try:
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            QMessageBox.critical(self, "Git Not Found", 
                                 "Git is required for this application but was not found. "
                                 "Please install Git and restart the application.")
            self.close()

    def setup_ui(self):
        # Mode Selection
        mode_group = QGroupBox("Installation Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Install AMAI (Standard Console)",
            "Install AMAI (VS Blizzard AI Console)",
            "Install AMAI (No Console)",
            "Remove AMAI Console",
            "Uninstall AMAI and Console"
        ])
        self.mode_combo.currentIndexChanged.connect(self.update_mode)
        mode_layout.addWidget(QLabel("Select Operation Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        
        # Process Method
        method_group = QGroupBox("Processing Method")
        method_layout = QVBoxLayout()
        
        self.batch_radio = QRadioButton("Process Maps in Batch (Whole Folder)")
        self.single_radio = QRadioButton("Process Single Map")
        self.batch_radio.setChecked(True)
        
        self.method_group = QButtonGroup()
        self.method_group.addButton(self.batch_radio, 0)
        self.method_group.addButton(self.single_radio, 1)
        
        method_layout.addWidget(self.batch_radio)
        method_layout.addWidget(self.single_radio)
        method_group.setLayout(method_layout)
        
        # Version Selection
        self.version_group = QGroupBox("Warcraft III Version")
        version_layout = QVBoxLayout()
        
        self.version_combo = QComboBox()
        self.version_combo.addItems([
            "Reforged Edition (1.33+)",
            "Classic: The Frozen Throne (1.24e+)",
            "Classic: Reign of Chaos (1.24e-1.31)"
        ])
        version_layout.addWidget(QLabel("Select Warcraft III Version:"))
        version_layout.addWidget(self.version_combo)
        self.version_group.setLayout(version_layout)
        
        # Path Selection
        path_group = QGroupBox("Map Location")
        path_layout = QVBoxLayout()
        
        self.path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_button = QPushButton("Browse...")
        self.path_button.clicked.connect(self.select_path)
        self.path_layout.addWidget(self.path_input)
        self.path_layout.addWidget(self.path_button)
        
        path_layout.addLayout(self.path_layout)
        path_group.setLayout(path_layout)
        
        # Progress and Log
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(QLabel("Operation Log:"))
        progress_layout.addWidget(self.log_output)
        progress_group.setLayout(progress_layout)
        
        # Execute Button
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self.execute)
        
        # Assemble UI
        self.main_layout.addWidget(mode_group)
        self.main_layout.addWidget(method_group)
        self.main_layout.addWidget(self.version_group)
        self.main_layout.addWidget(path_group)
        self.main_layout.addWidget(progress_group)
        self.main_layout.addWidget(self.execute_button)
        
        self.worker = None

    def update_mode(self, index):
        modes = ["install", "install_vs", "install_noconsole", "uninstall_console", "uninstall_all"]
        self.params["mode"] = modes[index]
        
        # Show/hide version selection based on mode
        if index in [0, 1, 2]:
            self.version_group.show()
        else:
            self.version_group.hide()

    def select_path(self):
        if self.batch_radio.isChecked():
            folder = QFileDialog.getExistingDirectory(self, "Select Maps Folder")
            if folder:
                self.path_input.setText(folder)
                self.params["path"] = folder
        else:
            file, _ = QFileDialog.getOpenFileName(
                self, "Select Map File", "", "Warcraft III Maps (*.w3x *.w3m)"
            )
            if file:
                self.path_input.setText(file)
                self.params["path"] = file

    def validate(self):
        # Check if path is valid
        if not self.params["path"]:
            QMessageBox.warning(self, "Invalid Path", "Please select a valid map or folder path.")
            return False
        
        if self.batch_radio.isChecked():
            if not os.path.isdir(self.params["path"]):
                QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder for batch processing.")
                return False
            if not any(Path(self.params["path"]).glob(pattern) for pattern in ["*.w3x", "*.w3m"]):
                QMessageBox.warning(self, "No Maps Found", "No Warcraft maps found in the selected folder.")
                return False
        else:
            if not os.path.isfile(self.params["path"]):
                QMessageBox.warning(self, "Invalid File", "Please select a valid map file.")
                return False
            if not self.params["path"].lower().endswith(('.w3x', '.w3m')):
                QMessageBox.warning(self, "Invalid Map File", "Selected file is not a Warcraft III map (.w3x or .w3m).")
                return False
        
        # Handle version
        version_map = [
            "REFORGED",
            "TFT",
            "ROC"
        ]
        self.params["version"] = version_map[self.version_combo.currentIndex()]
        self.params["process_method"] = "batch" if self.batch_radio.isChecked() else "single"
        
        return True

    def execute(self):
        if not self.validate():
            return
            
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Operation in Progress", "An operation is already in progress.")
            return
            
        # Clear logs and reset progress
        self.progress_bar.reset()
        self.log_output.clear()
        self.log_output.append("Starting operation...")
        
        # Disable UI during operation
        self.set_ui_enabled(False)
        
        # Create and start worker thread
        self.worker = CommandWorker(self.params)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.log_output.append(message)

    def operation_finished(self, success, message):
        self.log_output.append(message)
        self.progress_bar.setValue(100)
        self.set_ui_enabled(True)
        
        if success:
            QMessageBox.information(self, "Success", "Operation completed successfully!")
        else:
            QMessageBox.critical(self, "Error", "Operation failed!\n" + message)

    def set_ui_enabled(self, enabled):
        self.mode_combo.setEnabled(enabled)
        self.batch_radio.setEnabled(enabled)
        self.single_radio.setEnabled(enabled)
        self.version_combo.setEnabled(enabled)
        self.path_input.setEnabled(enabled)
        self.path_button.setEnabled(enabled)
        self.execute_button.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AMAIInstaller()
    window.show()
    sys.exit(app.exec_())

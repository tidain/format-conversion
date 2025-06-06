import os
import subprocess
import sys
from pathlib import Path

def build_resources():
    # 获取 pyside6-rcc 的路径
    if sys.platform == 'win32':
        rcc_path = str(Path(sys.executable).parent / 'Scripts' / 'pyside6-rcc.exe')
    else:
        rcc_path = 'pyside6-rcc'
        
    # 编译图标资源
    qrc_file = "app/resource/icons.qrc"
    py_file = "app/resource/icons_rc.py"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(py_file), exist_ok=True)
    
    # 编译资源
    subprocess.run([rcc_path, qrc_file, "-o", py_file], check=True)
    print(f"Resource file compiled: {py_file}")

if __name__ == "__main__":
    build_resources() 
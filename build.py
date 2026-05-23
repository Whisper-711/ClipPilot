"""
ClipPilot 打包脚本

用法:
    python build.py

依赖（pip install）:
    pyinstaller
"""
import os
import shutil
import subprocess
import sys

APP_NAME = "ClipPilot"
ENTRY_POINT = "main.py"
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
SPEC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{APP_NAME}.spec")

# 排除不需要的大库，减小体积
_EXCLUDE_LIBS = [
    "pandas", "numpy", "scipy", "matplotlib", "PIL",
    "PyQt5", "PyQt6", "PySide2", "PySide6",
    "notebook", "ipython", "jupyter",
    "sqlalchemy", "alembic",
    "openpyxl", "xlrd", "xlsxwriter",
    "bokeh", "plotly", "dash",
    "zmq", "tornado", "flask",
    "numba", "llvmlite",
    "fsspec", "s3fs", "gcsfs",
    "dask", "distributed",
    "gensim", "sklearn", "scikit_learn",
    "tensorflow", "torch", "keras",
    "cv2", "opencv",
    "pytest", "nose",
    "dns", "dnspython",
    "cloudpickle",
]


def clean():
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)


def build():
    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        pyinstaller = "pyinstaller"

    opts = [
        pyinstaller,
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"assets{os.pathsep}assets",
    ]
    for lib in _EXCLUDE_LIBS:
        opts += ["--exclude-module", lib]
    opts.append(ENTRY_POINT)

    print("=" * 60)
    print(f"  正在打包 {APP_NAME} …")
    print("=" * 60)
    sys.stdout.flush()

    ret = subprocess.run(opts, cwd=os.path.dirname(os.path.abspath(__file__)))
    if ret.returncode != 0:
        print(f"打包失败，返回码 {ret.returncode}")
        sys.exit(1)

    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n打包成功！")
        print(f"  输出: {exe_path}")
        print(f"  大小: {size_mb:.1f} MB")
    else:
        print(f"\n打包完成，但未找到 {exe_path}？")
        print(f"请检查 {DIST_DIR} 目录。")


if __name__ == "__main__":
    clean()
    build()

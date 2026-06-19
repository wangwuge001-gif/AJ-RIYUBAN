# config.py
from pathlib import Path
import sys
import platform


def resource_path(relative_path: str) -> Path:
    """
    获取资源文件路径。
    兼容普通 Python 运行和 PyInstaller 打包后的运行。
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent / relative_path


def app_root_dir() -> Path:
    """
    获取程序外部运行目录。

    普通运行：
        main.py 所在目录

    Windows exe：
        exe 所在目录

    macOS app：
        xxx.app 所在目录的外层目录
        例如：
        /Users/xxx/Downloads/AJ口コミ管理ツール.app
        返回：
        /Users/xxx/Downloads
    """
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()

        if platform.system() == "Darwin":
            for parent in exe_path.parents:
                if parent.suffix == ".app":
                    return parent.parent

        return exe_path.parent

    return Path(__file__).resolve().parent


# === 共用 Chrome Profile ===
# 不再使用 D 盘路径。
# 三个岛共用一个 profile。
# 程序首次运行时会自动创建 chrome_profile 文件夹。
BASE_DIR = app_root_dir()
COMMON_PROFILE_DIR = BASE_DIR / "chrome_profile"


# === 商品名称库文件 ===
MIYAKO_KEYWORD_FILE = resource_path("宫古岛商品名称库.txt")
IRIOMOTE_KEYWORD_FILE = resource_path("西表岛商品名称库.txt")
ISHIGAKI_KEYWORD_FILE = resource_path("石垣岛商品名称库.txt")


# === 账号信息 ===
ACCOUNT_MAP = {
    "1": {
        "name": "宮古島",
        "dir_path": str(COMMON_PROFILE_DIR),
        "keyword_file": str(MIYAKO_KEYWORD_FILE),
        "user": "miyakopipi",
        "pass": "这里填原来的宫古岛密码"
    },
    "2": {
        "name": "西表島",
        "dir_path": str(COMMON_PROFILE_DIR),
        "keyword_file": str(IRIOMOTE_KEYWORD_FILE),
        "user": "iriomotepipi",
        "pass": "这里填原来的西表岛密码"
    },
    "3": {
        "name": "石垣島",
        "dir_path": str(COMMON_PROFILE_DIR),
        "keyword_file": str(ISHIGAKI_KEYWORD_FILE),
        "user": "nashpipi",
        "pass": "这里填原来的石垣岛密码"
    }
}


# === 搜索设置 ===
START_PAGE = 1
MAX_PAGE = 500


# === 判定标准 ===
MIN_RATING = 4.5
MIN_LENGTH = 100
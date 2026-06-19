# config.py
from pathlib import Path
import sys
import platform


def resource_path(relative_path: str) -> Path:
    """
    获取 PyInstaller 内部资源路径。
    这里只作为备用路径使用。
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent / relative_path


def app_root_dir() -> Path:
    """
    获取 APP 外部所在目录。

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


def keyword_file_path(filename: str) -> Path:
    """
    商品名称库 txt 的读取路径。

    设计目标：
    1. 用户可以直接修改 APP 旁边的 txt 文件
    2. 不需要打开 APP 内部
    3. txt 不需要打包进 APP

    因此优先读取：
        AJ口コミ管理ツール.app 同一层目录下的 txt

    如果外部没有，再尝试读取内部资源路径作为备用。
    """
    external_file = app_root_dir() / filename

    if external_file.exists():
        return external_file

    return resource_path(filename)


# === 共用 Chrome Profile ===
# 不再使用 D 盘路径。
# 三个岛共用一个 profile。
# 程序首次运行时会自动在 APP 同级目录创建 chrome_profile 文件夹。
BASE_DIR = app_root_dir()
COMMON_PROFILE_DIR = BASE_DIR / "chrome_profile"


# === 商品名称库文件 ===
# 注意：
# 这些 txt 不打包进 APP。
# 使用者需要把 txt 放在 APP 同一层目录。
MIYAKO_KEYWORD_FILE = keyword_file_path("宫古岛商品名称库.txt")
IRIOMOTE_KEYWORD_FILE = keyword_file_path("西表岛商品名称库.txt")
ISHIGAKI_KEYWORD_FILE = keyword_file_path("石垣岛商品名称库.txt")


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
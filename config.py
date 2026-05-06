# config.py
import os

# === 基础路径配置 ===
BASE_PROFILE_DIR = r"D:\PythonProject\三岛区分浏览器指纹库"
BASE_PROJECT_DIR = r"D:\PythonProject\AJ评论操作分模块版"

# === 账号信息 ===
ACCOUNT_MAP = {
    "1": {
        "name": "gonggu (宫古)",
        "dir_path": os.path.join(BASE_PROFILE_DIR, "宫古岛"),
        "keyword_file": os.path.join(BASE_PROJECT_DIR, "宫古岛商品名称库.txt"),
        "user": "miyakopipi",  # <--- 请在这里修改
        "pass": "5363M!yak0"   # <--- 请在这里修改
    },
    "2": {
        "name": "xibiao (西表)",
        "dir_path": os.path.join(BASE_PROFILE_DIR, "西表岛"),
        "keyword_file": os.path.join(BASE_PROJECT_DIR, "西表岛商品名称库.txt"),
        "user": "iriomotepipi",
        "pass": "5363iriomote"
    },
    "3": {
        "name": "shiyuan (石垣)",
        "dir_path": os.path.join(BASE_PROFILE_DIR, "石垣岛"),
        "keyword_file": os.path.join(BASE_PROJECT_DIR, "石垣岛商品名称库.txt"),
        "user": "nashpipi",
        "pass": "5363ishigaki"
    }
}

# === 搜索设置 ===
START_PAGE = 1
MAX_PAGE = 500

# === 判定标准 ===
MIN_RATING = 4.5
MIN_LENGTH = 100
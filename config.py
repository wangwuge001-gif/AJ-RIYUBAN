# config.py

# === 账号信息 ===
ACCOUNT_MAP = {
    "1": {"name": "gonggu (宫古)", "file": "gonggu.json"},
    "2": {"name": "xibiao (西表)", "file": "xibiao.json"},
    "3": {"name": "shiyuan (石垣)", "file": "shiyuan.json"}
}

# === 搜索设置 ===
START_PAGE = 1
MAX_PAGE = 500

# === 判定标准 ===
MIN_RATING = 4.5       # 最低星级（小于这个会被过滤或取消）
MIN_LENGTH = 100       # 最低字数（小于这个会被过滤或取消）
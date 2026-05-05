from playwright.sync_api import sync_playwright


def save_login():
    with sync_playwright() as p:
        print("🚀 正在启动浏览器...")

        # --- 👇 修改重点：增强浏览器伪装能力 👇 ---
        browser = p.chromium.launch(
            headless=False,
            # 关键 1: 强制使用你电脑上安装的 Chrome，而不是 Playwright 自带的旧版 Chromium
            # 这能解决“重装 Chrome 后不匹配”的问题
            channel="chrome",

            # 关键 2: 禁用 Blink 引擎的自动化特征
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ],

            # 关键 3: 隐藏浏览器顶部“Chrome 正受到自动测试软件控制”的提示条
            ignore_default_args=["--enable-automation"]
        )
        # --- 👆 修改结束 👆 ---

        context = browser.new_context(
            # 设置正常的 User-Agent（保持你原来的设置）
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # 设置视口大小为 0 (no_viewport=True) 可以让页面自适应窗口，更像真人操作
            no_viewport=True
        )

        # 额外保险：通过 JS 注入彻底移除 webdriver 属性（防止被 JS 检测到）
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("👉 浏览器已打开，请前往 ActivityJapan 并手动登录账号...")

        # 你的目标网址
        try:
            page.goto("https://ptn.activityjapan.com/")
        except Exception as e:
            print(f"⚠️ 页面加载可能超时，但不影响后续手动操作。错误信息: {e}")

        # 等待用户操作
        input("\n✅ 登录成功并看到后台首页后，请务必回到这里按【回车】，我将保存你的登录状态...")

        # 核心：保存 Cookies 和 LocalStorage 到文件
        context.storage_state(path="auth.json")
        print("🎉 成功！登录凭证已保存为 'auth.json'。")
        print("现在你可以关闭这个窗口，去运行主程序了。")

        browser.close()


if __name__ == "__main__":
    save_login()
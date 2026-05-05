import os
import time
from playwright.sync_api import sync_playwright
import config
import logic


def run():
    print("=================================")
    print("   ActivityJapan 智能管理系统")
    print("   (v24.0 - 经典详情版)")
    print("=================================")

    # 1. 账号选择
    target_auth_file = ""
    current_account_name = ""

    while True:
        print("\n请选择要登录的账号：")
        for key, info in config.ACCOUNT_MAP.items():
            print(f"  [{key}] {info['name']}")

        choice = input("\n请输入序号: ").strip()
        if choice in config.ACCOUNT_MAP:
            target_auth_file = config.ACCOUNT_MAP[choice]["file"]
            current_account_name = config.ACCOUNT_MAP[choice]["name"]
            break
        else:
            print("❌ 输入错误")

    if not os.path.exists(target_auth_file):
        print(f"❌ 找不到文件: {target_auth_file}")
        return

    print(f"\n🚀 正在启动 [{current_account_name}] ...")
    time.sleep(1)

    with sync_playwright() as p:
        # === 👇 核心修改区域开始 👇 ===
        print("   ⚙️  正在应用反爬虫伪装补丁...")

        browser = p.chromium.launch(
            headless=False,
            # [关键点1] 强制使用本机 Chrome (解决重装后版本不匹配问题)
            channel="chrome",

            # [关键点2] 隐藏“Chrome正受到自动测试软件控制”的横幅
            ignore_default_args=["--enable-automation"],

            args=[
                # [关键点3] 禁用 Blink 引擎的自动化特征 (防止乱码的核心)
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--start-maximized"  # 启动时最大化窗口
            ]
        )

        context = browser.new_context(
            storage_state=target_auth_file,
            # [关键点4] 必须伪装 User-Agent，否则默认会带有 "HeadlessChrome" 字样
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # [关键点5] 让视口自适应，看起来像真人操作
            no_viewport=True
        )

        # [关键点6] 再次注入 JS 补丁，双重保险 (无论 logic.py 里有没有，这里再加一次)
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # 如果你的 logic.py 里有其他补丁，保留它
        try:
            logic.inject_js_patches(context)
        except:
            pass

        page = context.new_page()
        # === 👆 核心修改区域结束 👆 ===

        print(f"👉 正在加载首页...")
        try:
            page.goto(f"https://ptn.activityjapan.com/review?page={config.START_PAGE}", timeout=60000)
        except:
            print("⚠️ 页面加载较慢...")

        while True:
            # 输入关键词
            raw_target = input(f"\n[{current_account_name}] 请输入【方案名称】关键词 (直接回车退出): ").strip()
            if not raw_target: break

            # 强力清洗（去空格去换行）
            target_clean = logic.normalize_text(raw_target)
            print(f"   ℹ️ 搜索词(清洗后): [{target_clean}]")

            page_num = config.START_PAGE
            stop_search = False

            while True:
                if page_num > config.MAX_PAGE or stop_search: break

                print(f"\n🔍 正在扫描第 {page_num} 页...")
                try:
                    page.goto(f"https://ptn.activityjapan.com/review?page={page_num}", timeout=60000)
                except:
                    print("   ⚠️ 超时，重试...")

                rows = page.locator("tr.date-url-target")
                count = rows.count()

                print(f"   📊 本页共读取到 {count} 行数据")

                if count == 0 and "404" in page.content():
                    print("   🏁 已到达最后一页")
                    break

                page_needs_save = False

                for i in range(count):
                    row = rows.nth(i)
                    try:
                        data = logic.parse_review_data(row)
                    except:
                        continue

                    if target_clean not in data['plan_name_clean']:
                        continue

                    print(f"   ✅ [第{i + 1}行] 方案名命中！")

                    # [分支 A] 建议置顶
                    if logic.is_qualified_for_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                        print(f"      ⚡ 发现优质评论 (建议置顶): {data['title']}")
                        print(f"      📏 字数: {data['length']} | ⭐ 评分: {data['rating']}")

                        logic.highlight_row(row, color='yellow', border='5px solid red')

                        cmd = input("      👉 确认置顶? (y=是, q=退出, 回车=跳过): ")
                        if cmd.lower() == 'y':
                            print("      🆗 已标记 (稍后统一提交)")
                            logic.perform_check_action(data['checkbox'])
                            page_needs_save = True
                        elif cmd == 'q':
                            stop_search = True
                            break
                        logic.reset_style(row)

                    # [分支 B] 建议取消
                    elif logic.should_cancel_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                        print(f"      🗑️ 发现不合格置顶 (建议取消): {data['title']}")
                        print(f"      📏 字数: {data['length']} | ⭐ 评分: {data['rating']}")
                        print(f"      ❌ 原因: 字数<{config.MIN_LENGTH} 或 评分<{config.MIN_RATING}")

                        logic.highlight_row(row, color='#e6f7ff', border='5px solid blue')

                        cmd = input("      👉 确认取消? (y=是, q=退出, 回车=跳过): ")
                        if cmd.lower() == 'y':
                            print("      🆗 已标记 (稍后统一提交)")
                            logic.perform_uncheck_action(data['checkbox'])
                            page_needs_save = True
                        elif cmd == 'q':
                            stop_search = True
                            break
                        logic.reset_style(row)

                if page_needs_save:
                    print("💾 检测到变动，正在提交...", end=" ")
                    if logic.submit_changes(page):
                        print("✅ 保存成功！页面已刷新。")
                    else:
                        print("❌ 失败：提交按钮无响应")

                if stop_search: break
                if page.locator("a[rel='next']").count() == 0: break
                page_num += 1

        print("👋 程序结束")
        browser.close()


if __name__ == "__main__":
    run()
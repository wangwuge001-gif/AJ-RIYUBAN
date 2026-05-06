# main.py
import os
import time
from playwright.sync_api import sync_playwright
import config
import logic


def run_auto_manage(page, target_config):
    """模式1：整页批处理模式 (动态匹配池极速版)"""
    with open(target_config["keyword_file"], 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]

    if not keywords:
        print("❌ 关键词库为空！")
        return

    target_limit = 5
    keyword_counts = {kw: 0 for kw in keywords}
    active_keywords = keywords.copy()

    print(f"\n" + "=" * 50)
    print(f"▶️ 开启【自动管理模式】(动态匹配池)")
    print(f"   (共 {len(keywords)} 个关键词，每个上限 {target_limit} 条)")
    print(f"==================================================")

    page_num = config.START_PAGE

    while page_num <= config.MAX_PAGE:
        if not active_keywords:
            print(f"\n🎯 完美！匹配池已清空，所有目标均已达成！提前结束。")
            break

        print(f"  🔍 正在扫描第 {page_num} 页... (匹配池剩余: {len(active_keywords)}个词)")
        try:
            page.goto(f"https://ptn.activityjapan.com/review?page={page_num}", timeout=60000)
        except:
            print("   ⚠️ 页面加载超时，尝试强行读取...")

        rows = page.locator("tr.date-url-target")
        count = rows.count()
        if count == 0:
            print("   🏁 似乎已翻到最后一页，无更多数据。")
            break

        page_needs_save = False

        for i in range(count):
            if not active_keywords:
                break

            row = rows.nth(i)
            try:
                data = logic.parse_review_data(row)
            except:
                continue

            matched_kw = None
            for kw in active_keywords:
                if logic.normalize_text(kw) in data['plan_name_clean']:
                    matched_kw = kw
                    break

            if matched_kw:
                action_taken = False

                if logic.is_qualified_for_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                    print(f"      ⚡ [置顶] 命中: '{matched_kw}' -> {data['title'][:15]}...")
                    logic.perform_check_action(data['checkbox'])
                    action_taken = True

                elif logic.should_cancel_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                    print(f"      🗑️ [取消] 命中: '{matched_kw}' -> {data['title'][:15]}...")
                    logic.perform_uncheck_action(data['checkbox'])
                    action_taken = True

                if action_taken:
                    keyword_counts[matched_kw] += 1
                    page_needs_save = True

                    if keyword_counts[matched_kw] >= target_limit:
                        print(f"      🎯 关键词 '{matched_kw}' 已满 {target_limit} 条，移出匹配池！")
                        active_keywords.remove(matched_kw)

        if page_needs_save:
            print("   💾 本页处理完毕，正在提交变更...")
            logic.submit_changes(page)

        if page.locator("a[rel='next']").count() == 0:
            print("   🏁 翻遍了全站所有页面。")
            break

        page_num += 1

    print("\n📊 运行结果统计：")
    for kw, c in keyword_counts.items():
        if c > 0:
            print(f"  - [{kw}]: 处理了 {c} 条")

    if active_keywords:
        print(f"  ⚠️ 以下 {len(active_keywords)} 个关键词未能达标（已找遍全站）：")
        print(f"      {', '.join(active_keywords[:5])}" + ("..." if len(active_keywords) > 5 else ""))


def run_clear_all(page):
    """模式2：一键取消所有当前勾选的置顶 (死磕第一页模式)"""
    print("\n" + "!" * 50)
    print(" 🔥 进入【全量清空模式】：将取消所有已勾选的置顶")
    print("!" * 50)

    total_cleared = 0
    loop_count = 1

    while True:
        print(f"  🔍 正在进行第 {loop_count} 轮清理 (始终扫描第 1 页)...")
        try:
            page.goto("https://ptn.activityjapan.com/review?page=1", timeout=60000)
        except:
            print("   ⚠️ 页面加载较慢...")

        rows = page.locator("tr.date-url-target")
        count = rows.count()
        if count == 0:
            print("   🏁 页面无数据，清理结束。")
            break

        page_needs_save = False
        round_cleared = 0

        for i in range(count):
            row = rows.nth(i)
            try:
                data = logic.parse_review_data(row)
            except:
                continue

            if data['is_checked']:
                print(f"      🗑️ 取消勾选 -> {data['title'][:20]}...")
                logic.perform_uncheck_action(data['checkbox'])
                page_needs_save = True
                round_cleared += 1
                total_cleared += 1

        if page_needs_save:
            print(f"   💾 本轮发现了 {round_cleared} 个置顶，正在提交保存...")
            logic.submit_changes(page)
            loop_count += 1
            time.sleep(1)
        else:
            print(f"\n✅ 清理任务圆满结束！总共取消了 {total_cleared} 个置顶。")
            break


def run():
    print("=================================")
    print("   ActivityJapan 智能管理系统")
    print("   (v28.0 - 最终完全体)")
    print("=================================")

    # 1. 账号选择
    target_config = None
    while True:
        print("\n请选择要操作的账号：")
        for key, info in config.ACCOUNT_MAP.items():
            print(f"  [{key}] {info['name']}")

        choice = input("\n请输入序号: ").strip()
        if choice in config.ACCOUNT_MAP:
            target_config = config.ACCOUNT_MAP[choice]
            break
        else:
            print("❌ 输入错误")

    # 2. 模式选择
    print("\n请选择运行模式：")
    print("  [1] 自动管理模式 (根据清单限额5条置顶)")
    print("  [2] 全量清空模式 (死磕第一页，清空所有置顶)")
    mode = input("\n请输入模式序号: ").strip()

    print(f"\n🚀 正在启动 [{target_config['name']}]...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=target_config["dir_path"],
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--start-maximized"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            no_viewport=True
        )

        logic.inject_js_patches(context)
        page = context.pages[0] if context.pages else context.new_page()

        # 3. 自动登录与轮询检测
        print("👉 尝试访问后台管理页面...")
        page.goto("https://ptn.activityjapan.com/review", timeout=60000)
        time.sleep(2)

        if "/login" in page.url:
            print("🔑 检测到登录页，尝试自动填充账号密码...")
            try:
                page.locator('input[name="id"]').fill(target_config["user"])
                page.locator('input[name="pass"]').fill(target_config["pass"])
                if page.locator('input[type="checkbox"]').count() > 0:
                    page.locator('input[type="checkbox"]').first.check()

                print("点击登录按钮...")
                page.locator('button:has-text("ログインする"), input[type="submit"]').first.click()

                print("⏳ 正在轮询登录状态，请稍候（若有滑块/验证码请手动完成）...")
                success = False
                for _ in range(60):
                    if "/review" in page.url:
                        success = True
                        break
                    time.sleep(1)

                if not success:
                    print("\n⚠️ 自动登录未在预时内完成。")
                    input("✅ 请手动完成验证并登录到首页后，回到这里按【回车】继续...")
                else:
                    print("✅ 登录成功，自动跳转作业页！")
            except Exception as e:
                print(f"❌ 自动填充失败: {e}")
                input("✅ 请手动输入账号密码并登录后，按【回车】继续...")

        # 4. 执行对应模式
        if mode == "2":
            run_clear_all(page)
        else:
            run_auto_manage(page, target_config)

        print("\n🎉 程序执行完毕")
        context.close()


if __name__ == "__main__":
    run()
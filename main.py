# main.py
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from playwright.sync_api import sync_playwright

import config
import logic


def run_auto_manage(page, target_config, log):
    """模式1：商品リストに基づく自動管理モード"""

    keyword_file = Path(target_config["keyword_file"])

    if not keyword_file.exists():
        log(f"❌ キーワードファイルが見つかりません：{keyword_file}")
        log("以下の txt ファイルがプログラムに同梱されているか確認してください。")
        log("  - 宫古岛商品名称库.txt")
        log("  - 西表岛商品名称库.txt")
        log("  - 石垣岛商品名称库.txt")
        return

    with open(keyword_file, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]

    if not keywords:
        log("❌ キーワードリストが空です。")
        return

    target_limit = 5
    keyword_counts = {kw: 0 for kw in keywords}
    active_keywords = keywords.copy()

    log("")
    log("=" * 50)
    log("▶️ 自動管理モードを開始します")
    log(f"   商品数：{len(keywords)} 件 / 各商品最大 {target_limit} 件まで")
    log("=" * 50)

    page_num = config.START_PAGE

    while page_num <= config.MAX_PAGE:
        if not active_keywords:
            log("")
            log("🎯 すべての商品が上限に達しました。処理を終了します。")
            break

        log(f"🔍 {page_num} ページ目を確認中...（残り商品数：{len(active_keywords)}）")

        try:
            page.goto(f"https://ptn.activityjapan.com/review?page={page_num}", timeout=60000)
        except Exception:
            log("⚠️ ページの読み込みに時間がかかっています。続行します。")

        rows = page.locator("tr.date-url-target")
        count = rows.count()

        if count == 0:
            log("🏁 データが見つかりません。最終ページの可能性があります。")
            break

        page_needs_save = False

        for i in range(count):
            if not active_keywords:
                break

            row = rows.nth(i)

            try:
                data = logic.parse_review_data(row)
            except Exception:
                continue

            matched_kw = None

            for kw in active_keywords:
                if logic.normalize_text(kw) in data["plan_name_clean"]:
                    matched_kw = kw
                    break

            if matched_kw:
                action_taken = False

                if logic.is_qualified_for_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                    log(f"⚡ [ピックアップ追加] {matched_kw} -> {data['title'][:15]}...")
                    logic.perform_check_action(data["checkbox"])
                    action_taken = True

                elif logic.should_cancel_pickup(data, config.MIN_RATING, config.MIN_LENGTH):
                    log(f"🗑️ [ピックアップ解除] {matched_kw} -> {data['title'][:15]}...")
                    logic.perform_uncheck_action(data["checkbox"])
                    action_taken = True

                if action_taken:
                    keyword_counts[matched_kw] += 1
                    page_needs_save = True

                    if keyword_counts[matched_kw] >= target_limit:
                        log(f"🎯 {matched_kw} は {target_limit} 件に達しました。対象リストから外します。")
                        active_keywords.remove(matched_kw)

        if page_needs_save:
            log("💾 このページの変更を保存しています...")
            logic.submit_changes(page)

        if page.locator("a[rel='next']").count() == 0:
            log("🏁 すべてのページを確認しました。")
            break

        page_num += 1

    log("")
    log("📊 処理結果：")

    for kw, c in keyword_counts.items():
        if c > 0:
            log(f"  - {kw}：{c} 件処理しました")

    if active_keywords:
        log(f"⚠️ 以下 {len(active_keywords)} 件の商品は条件を満たす口コミが不足しています。")
        log(f"   {', '.join(active_keywords[:5])}" + ("..." if len(active_keywords) > 5 else ""))


def run_clear_all(page, log):
    """模式2：現在ピックアップ中の口コミをすべて解除する"""

    log("")
    log("!" * 50)
    log("🔥 全件解除モードを開始します")
    log("現在ピックアップ中の口コミをすべて解除します")
    log("!" * 50)

    total_cleared = 0
    loop_count = 1

    while True:
        log(f"🔍 第 {loop_count} 回目の確認を行っています...")

        try:
            page.goto("https://ptn.activityjapan.com/review?page=1", timeout=60000)
        except Exception:
            log("⚠️ ページの読み込みに時間がかかっています。続行します。")

        rows = page.locator("tr.date-url-target")
        count = rows.count()

        if count == 0:
            log("🏁 データが見つかりません。処理を終了します。")
            break

        page_needs_save = False
        round_cleared = 0

        for i in range(count):
            row = rows.nth(i)

            try:
                data = logic.parse_review_data(row)
            except Exception:
                continue

            if data["is_checked"]:
                log(f"🗑️ ピックアップ解除 -> {data['title'][:20]}...")
                logic.perform_uncheck_action(data["checkbox"])
                page_needs_save = True
                round_cleared += 1
                total_cleared += 1

        if page_needs_save:
            log(f"💾 {round_cleared} 件を解除しました。変更を保存しています...")
            logic.submit_changes(page)
            loop_count += 1
            time.sleep(1)
        else:
            log("")
            log(f"✅ 全件解除が完了しました。合計 {total_cleared} 件を解除しました。")
            break


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ActivityJapan 口コミ管理ツール")
        self.root.geometry("760x560")

        self.worker_thread = None
        self.continue_event = threading.Event()

        self.account_var = tk.StringVar(value="1")
        self.mode_var = tk.StringVar(value="1")

        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            main_frame,
            text="ActivityJapan 口コミ管理ツール",
            font=("Arial", 18, "bold")
        )
        title.pack(anchor=tk.W, pady=(0, 12))

        account_frame = ttk.LabelFrame(main_frame, text="操作するアカウント")
        account_frame.pack(fill=tk.X, pady=(0, 10))

        for key, info in config.ACCOUNT_MAP.items():
            ttk.Radiobutton(
                account_frame,
                text=f"[{key}] {info['name']}",
                variable=self.account_var,
                value=key
            ).pack(side=tk.LEFT, padx=12, pady=8)

        mode_frame = ttk.LabelFrame(main_frame, text="実行モード")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(
            mode_frame,
            text="自動管理モード（商品リストに基づき、各商品最大5件までピックアップ）",
            variable=self.mode_var,
            value="1"
        ).pack(anchor=tk.W, padx=12, pady=5)

        ttk.Radiobutton(
            mode_frame,
            text="全件解除モード（現在ピックアップ中の口コミをすべて解除）",
            variable=self.mode_var,
            value="2"
        ).pack(anchor=tk.W, padx=12, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_button = ttk.Button(
            button_frame,
            text="実行開始",
            command=self.start
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))

        self.continue_button = ttk.Button(
            button_frame,
            text="手動ログイン完了後に続行",
            command=self.continue_after_manual_login,
            state=tk.DISABLED
        )
        self.continue_button.pack(side=tk.LEFT, padx=(0, 8))

        self.quit_button = ttk.Button(
            button_frame,
            text="終了",
            command=self.root.quit
        )
        self.quit_button.pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(main_frame, text="実行ログ")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log("準備完了。")
        self.log("Macで使用する場合は、事前にGoogle Chromeをインストールしてください。")

    def log(self, message):
        def _append():
            self.log_text.insert(tk.END, str(message) + "\n")
            self.log_text.see(tk.END)

        self.root.after(0, _append)

    def set_running_state(self, running: bool):
        def _set():
            self.start_button.config(state=tk.DISABLED if running else tk.NORMAL)

        self.root.after(0, _set)

    def enable_continue_button(self):
        def _enable():
            self.continue_button.config(state=tk.NORMAL)

        self.root.after(0, _enable)

    def disable_continue_button(self):
        def _disable():
            self.continue_button.config(state=tk.DISABLED)

        self.root.after(0, _disable)

    def continue_after_manual_login(self):
        self.continue_event.set()
        self.disable_continue_button()
        self.log("✅ 手動ログイン完了として処理を続行します。")

    def wait_for_manual_login(self, message):
        self.continue_event.clear()
        self.log(message)
        self.log("ブラウザ上で手動ログインを完了してから、画面上の「手動ログイン完了後に続行」を押してください。")
        self.enable_continue_button()
        self.continue_event.wait()

    def start(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("実行中", "現在処理中です。完了までお待ちください。")
            return

        account_key = self.account_var.get()
        mode = self.mode_var.get()

        target_config = config.ACCOUNT_MAP[account_key]

        self.log("")
        self.log("=" * 60)
        self.log(f"🚀 {target_config['name']} の処理を開始します。")
        self.log("=" * 60)

        self.worker_thread = threading.Thread(
            target=self.run_worker,
            args=(target_config, mode),
            daemon=True
        )
        self.worker_thread.start()

    def run_worker(self, target_config, mode):
        self.set_running_state(True)

        context = None

        try:
            profile_dir = Path(config.COMMON_PROFILE_DIR)
            profile_dir.mkdir(parents=True, exist_ok=True)

            self.log(f"📁 Chrome profile フォルダ：{profile_dir}")

            with sync_playwright() as p:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=target_config["dir_path"],
                        headless=False,
                        channel="chrome",
                        ignore_default_args=["--enable-automation"],
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--start-maximized"
                        ],
                        no_viewport=True
                    )
                except Exception as e:
                    self.log("")
                    self.log("❌ Google Chrome の起動に失敗しました。")
                    self.log("この PC に Google Chrome がインストールされているか確認してください。")
                    self.log(f"エラー内容：{e}")
                    return

                logic.inject_js_patches(context)

                page = context.pages[0] if context.pages else context.new_page()

                self.log("👉 管理画面にアクセスしています...")

                try:
                    page.goto("https://ptn.activityjapan.com/review", timeout=60000)
                except Exception:
                    self.log("⚠️ 初回ページ読み込みに時間がかかっています。続行します。")

                time.sleep(2)

                if "/login" in page.url:
                    self.log("🔑 ログイン画面を検出しました。自動ログインを試行します。")

                    try:
                        page.locator('input[name="id"]').fill(target_config["user"])
                        page.locator('input[name="pass"]').fill(target_config["pass"])

                        if page.locator('input[type="checkbox"]').count() > 0:
                            page.locator('input[type="checkbox"]').first.check()

                        self.log("ログインボタンをクリックします...")

                        page.locator(
                            'button:has-text("ログインする"), input[type="submit"]'
                        ).first.click()

                        self.log("⏳ ログイン状態を確認しています。認証画面が表示された場合は手動で対応してください。")

                        success = False

                        for _ in range(60):
                            if "/review" in page.url:
                                success = True
                                break

                            time.sleep(1)

                        if not success:
                            self.wait_for_manual_login("⚠️ 自動ログインが時間内に完了しませんでした。")
                        else:
                            self.log("✅ ログインに成功しました。")

                    except Exception as e:
                        self.log(f"❌ 自動入力に失敗しました：{e}")
                        self.wait_for_manual_login("手動ログインが必要です。")

                if mode == "2":
                    run_clear_all(page, self.log)
                else:
                    run_auto_manage(page, target_config, self.log)

                self.log("")
                self.log("🎉 処理が完了しました。")

        except Exception as e:
            self.log("")
            self.log("❌ 予期しないエラーが発生しました。")
            self.log(f"エラー内容：{e}")

        finally:
            try:
                if context:
                    context.close()
            except Exception:
                pass

            self.set_running_state(False)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
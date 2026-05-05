# logic.py
import re
import time


def inject_js_patches(context):
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.confirm = () => true;
        window.alert = () => true;
        document.addEventListener('click', function(e) {
            const selection = window.getSelection().toString();
            if (selection.length > 0) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
    """)


def normalize_text(text):
    """
    【强力清洗】剔除所有空格、换行、制表符，统一全角半角
    """
    if not text: return ""
    # 替换全角空格为半角，然后去除所有空白字符
    text = text.replace("　", " ").replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
    return text


def parse_review_data(row):
    data = {}

    # 1. 复选框
    checkbox = row.locator("input[type='checkbox']").first
    data['checkbox'] = checkbox
    data['is_checked'] = checkbox.is_checked()

    # 2. 方案名称 (增强版提取)
    try:
        # 获取第3个 click-tr (index=2)
        plan_cell = row.locator("td.click-tr").nth(2)

        # 尝试获取文本：优先取 <small>，没有则取全部
        small_tag = plan_cell.locator("small").first
        if small_tag.count() > 0:
            raw_text = small_tag.inner_text()
        else:
            raw_text = plan_cell.inner_text()

        data['plan_name_raw'] = raw_text.strip()  # 保留原始文本用于显示
        data['plan_name_clean'] = normalize_text(raw_text)  # 清洗后文本用于匹配

    except Exception as e:
        data['plan_name_raw'] = f"提取失败: {e}"
        data['plan_name_clean'] = ""

    # 3. 评分
    full = row.locator("i.fa-star").count()
    half = row.locator("i.fa-star-half-o").count()
    data['rating'] = full + 0.5 * half

    # 4. 评论正文
    review_cell = row.locator("td.click-tr").nth(4)

    title_el = review_cell.locator("p").nth(0)
    data['title'] = title_el.inner_text().strip() if title_el.count() > 0 else "(无标题)"

    detail_el = review_cell.locator("p.review-detail")
    if detail_el.count() > 0:
        data['body'] = detail_el.inner_text().strip()
        data['length'] = len(data['body'])
    else:
        data['body'] = ""
        data['length'] = 0

    return data


# === 核心判断逻辑 ===

def is_qualified_for_pickup(data, min_rating, min_len):
    """值得置顶吗？(未选 + 高分 + 长文)"""
    if data['is_checked']: return False
    if data['rating'] < min_rating: return False
    if data['length'] <= min_len: return False
    return True


def should_cancel_pickup(data, min_rating, min_len):
    """应该取消吗？(已选 + (低分 OR 短文))"""
    if not data['is_checked']: return False

    # 只要有一个指标不达标，就建议取消
    if data['rating'] < min_rating: return True
    if data['length'] < min_len: return True

    return False


# === 动作逻辑 ===

def highlight_row(row, color='yellow', border='5px solid red'):
    row.scroll_into_view_if_needed()
    row.evaluate(f"e => e.style.backgroundColor = '{color}'")
    row.evaluate(f"e => e.style.border = '{border}'")


def reset_style(row):
    try:
        row.evaluate("e => e.style.backgroundColor = ''")
        row.evaluate("e => e.style.border = ''")
    except:
        pass


def perform_check_action(checkbox):
    if not checkbox.is_checked():
        try:
            checkbox.check(timeout=1000)
        except:
            checkbox.click(force=True)


def perform_uncheck_action(checkbox):
    if checkbox.is_checked():
        try:
            checkbox.uncheck(timeout=1000)
        except:
            checkbox.click(force=True)


def submit_changes(page):
    btn = page.locator("button").filter(has_text="ピックアップを更新").first
    if btn.count() > 0:
        page.once("dialog", lambda dialog: dialog.accept())
        btn.click(force=True)
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        return True
    return False
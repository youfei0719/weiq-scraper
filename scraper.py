import time
import random
import os
import sys
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# 配置与全局变量定义区
# ==========================================
INPUT_EXCEL = "accounts.xlsx"
OUTPUT_EXCEL = "weiq_results.xlsx"
STATE_JSON = "state.json"

global_request_count = 0

def init_env():
    if os.path.exists(OUTPUT_EXCEL):
        try:
            df_old = pd.read_excel(OUTPUT_EXCEL)
            # 校验是否包含修正后的“粉丝数”字段
            if "粉丝数" not in df_old.columns or "最低阅读量" not in df_old.columns:
                backup_name = f"weiq_results_旧版备份_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
                os.rename(OUTPUT_EXCEL, backup_name)
                print(f"[系统保护] 检测到旧版本或结构不匹配的表格，已自动重命名为: {backup_name}")
                print(f"[系统保护] 本次运行将创建一张包含15项全量指标的全新结果表。\n")
        except Exception:
            os.remove(OUTPUT_EXCEL)

def init_browser(p):
    print("[初始化] 正在启动浏览器...")
    browser = p.chromium.launch(headless=False)
    
    if os.path.exists(STATE_JSON):
        print(f"[初始化] 检测到凭证文件 {STATE_JSON}，尝试以已登录状态恢复会话。")
        context = browser.new_context(storage_state=STATE_JSON)
    else:
        print(f"[警告] 未检测到凭证文件，将以未登录状态启动！")
        context = browser.new_context()
        
    page = context.new_page()
    return browser, context, page

def extract_metrics(page):
    # 【已修正】将“粉丝数量”更正为“粉丝数”
    target_keys = [
        "粉丝数", "直发CPM", "阅读中位数", "直发阅读中位数", "转发阅读中位数",
        "互动中位数", "直发互动中位数", "转发互动中位数", "发布博文数", 
        "转发中位数", "评论中位数", "点赞中位数", 
        "最低阅读量", "最高阅读量", "阅读量均值"
    ]
    
    results = {k: "空" for k in target_keys}
    
    js_extract_logic = r"""
    (keyword) => {
        const target = keyword.toUpperCase();
        let elements = Array.from(document.querySelectorAll('*'))
            .filter(el => el.childElementCount === 0 && el.textContent.trim().toUpperCase() === target);
            
        if (elements.length === 0) {
            elements = Array.from(document.querySelectorAll('*'))
                .filter(el => el.childElementCount === 0 && el.textContent.toUpperCase().includes(target));
        }
        
        if (elements.length === 0) return "空_无标签";
        
        const labelEl = elements[0];
        
        let parent = labelEl.parentElement;
        for (let i = 0; i < 4; i++) {
            if (parent) {
                let textContent = parent.innerText || '';
                let lines = textContent.split(/[\n\r]+/).map(s => s.trim()).filter(Boolean);
                let idx = lines.findIndex(s => s.toUpperCase() === target);
                
                if (idx !== -1 && idx + 1 < lines.length) {
                    let candidate = lines[idx + 1];
                    if (/^[\d,.]+[万wWkK]?$/.test(candidate) || candidate === '-' || candidate.includes('%')) {
                        return candidate;
                    }
                }
            }
            parent = parent ? parent.parentElement : null;
        }
        
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let currentNode = walker.nextNode();
        let found = false;
        while (currentNode) {
            if (currentNode.parentElement === labelEl || currentNode.nodeValue.toUpperCase().includes(target)) {
                found = true;
                break;
            }
            currentNode = walker.nextNode();
        }
        
        if (found) {
            currentNode = walker.nextNode();
            let attempt = 0;
            while(currentNode && attempt < 15) {
                let txt = currentNode.nodeValue.trim();
                if (txt && !['¥', '￥', ':', '：', '-', '/'].includes(txt) && txt.toUpperCase() !== target) {
                    return txt;
                }
                currentNode = walker.nextNode();
                attempt++;
            }
        }
        return "空_无数据";
    }
    """
    
    for key in target_keys:
        try:
            val = page.evaluate(js_extract_logic, key)
            if val:
                results[key] = val
        except Exception:
            pass
            
    return results

def check_anti_spider(page):
    needs_manual = False
    current_url = page.url.lower()
    
    if "login" in current_url or "passport" in current_url:
        print("\n\a[风控警告] 当前页面被重定向到了登录页！")
        needs_manual = True
        
    try:
        anti_keywords = ["滑动验证", "安全访问验证", "请输入验证码", "访问过于频繁"]
        page_text = page.locator("body").inner_text(timeout=2000)
        if any(kw in page_text for kw in anti_keywords):
            print(f"\n\a[风控警告] 页面命中风控拦截！当前 URL: {page.url}")
            needs_manual = True
    except Exception:
        pass

    if needs_manual:
        print(">>>>> 请立即在弹出的浏览器视窗中手动登录或滑块验证 <<<<<")
        input("请在手动处理完毕（并确保页面已加载出正常数据面板）后，按回车键继续...")
        print("[恢复] 继续执行爬虫流程。\n")
        time.sleep(3)

def append_to_excel(row_dict):
    df_new = pd.DataFrame([row_dict])
    
    if not os.path.exists(OUTPUT_EXCEL):
        df_new.to_excel(OUTPUT_EXCEL, index=False)
    else:
        with pd.ExcelWriter(OUTPUT_EXCEL, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            start_row = writer.sheets["Sheet1"].max_row
            df_new.to_excel(writer, index=False, header=False, startrow=start_row)

def process_account_url(page, account_id, url, current_idx, total_accounts):
    global global_request_count
    progress = f"[{current_idx}/{total_accounts}]"
    
    print(f"\n{progress} ----------------------------------------------------")
    print(f"{progress} [ID: {account_id}] 正在访问页面...")
    
    global_request_count += 1
    if global_request_count > 1 and global_request_count % 50 == 0:
        print(f"\n{progress} [机制] 触发防封锁休眠保护！")
        for remaining in range(180, 0, -1):
            sys.stdout.write(f"\r{progress} [冷却倒计时] 还需休眠 {remaining:3d} 秒...")
            sys.stdout.flush()
            time.sleep(1)
        print(f"\n{progress} [机制] 冷却结束，恢复执行。\n")

    default_keys = [
        "粉丝数", "直发CPM", "阅读中位数", "直发阅读中位数", "转发阅读中位数",
        "互动中位数", "直发互动中位数", "转发互动中位数", "发布博文数", 
        "转发中位数", "评论中位数", "点赞中位数", 
        "最低阅读量", "最高阅读量", "阅读量均值"
    ]
    extracted_data = {k: "空" for k in default_keys}
    
    try:
        response = page.goto(url, timeout=45000, wait_until="domcontentloaded")
        
        if response is None or response.status >= 400:
            print(f"{progress} ❌ 页面拦截，状态码: {response.status if response else 'Null'}")
            return {k: "异常_阻断" for k in default_keys}
            
        sys.stdout.write(f"\r{progress} 页面抵达，正在执行深度滚动触发懒加载...")
        sys.stdout.flush()
        page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    let totalHeight = 0;
                    let distance = 500;
                    let timer = setInterval(() => {
                        let scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            window.scrollTo(0, 0); 
                            resolve();
                        }
                    }, 250);
                });
            }
        """)
        print("")
            
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
            
        sleep_t2 = random.randint(2, 4)
        for remaining in range(sleep_t2, 0, -1):
            sys.stdout.write(f"\r{progress} 数据装配等待中: {remaining} 秒...")
            sys.stdout.flush()
            time.sleep(1)
        print("")
        
        check_anti_spider(page)
        extracted_data = extract_metrics(page)
        
        valid_count = sum(1 for v in extracted_data.values() if "空" not in str(v))
        
        # 增加无效页面诊断提示
        if valid_count == 0:
            print(f"{progress} ⚠️ 页面似乎为空白，博主可能已下架、换号或未被收录。")
            extracted_data = {k: "账号失效/未收录" for k in default_keys}
        else:
            print(f"{progress} ✅ 成功提取 {valid_count} 项核心指标。")
        
    except PlaywrightTimeoutError:
        print(f"{progress} ❌ 页面响应超时。")
        extracted_data = {k: "超时" for k in default_keys}
    except Exception as e:
        print(f"{progress} ❌ 读取报错: {str(e)}")
        extracted_data = {k: "挂起" for k in default_keys}
        
    return extracted_data

def main():
    init_env()
    
    if not os.path.exists(INPUT_EXCEL):
        print(f"[错误] 无法定位到输入表: {INPUT_EXCEL}")
        return

    try:
        df = pd.read_excel(INPUT_EXCEL)
    except Exception as e:
        print(f"[错误] Excel 读取失败: {str(e)}")
        return
        
    total_accounts = len(df)
    print(f"[系统] 准备执行 {total_accounts} 个任务，全量 15 项数据监控启动。")

    with sync_playwright() as p:
        browser, context, page = init_browser(p)
        
        if not os.path.exists(STATE_JSON):
            print("\n============================================")
            page.goto("https://www.weiq.com/", timeout=60000)
            print(">>>>> 请在派出的浏览器窗口中完成登录 <<<<<")
            input("====> 等你【确定登录成功】且进到操作大厅了，再点击终端并在键盘敲【回车键】发车：")
            context.storage_state(path=STATE_JSON)
            print("============================================\n")

        for index, row in df.iterrows():
            current_idx = index + 1
            aid = row.get("账号ID")
            uid = row.get("uid")
            
            if pd.isna(uid) or str(uid).strip() == "":
                print(f"\n[{current_idx}/{total_accounts}] ⚠️ [ID: {aid}] 丢失 uid 链接参数，路过。")
                continue
            
            aid = str(aid).strip()
            uid = str(uid).strip()
            url = f"https://weiq.com/client/product/weibo/detail?account_uid={uid}"
            
            metrics_dict = process_account_url(page, aid, url, current_idx, total_accounts)
            
            result_row = {"账号ID": aid, "uid": uid, "主页链接": url}
            result_row.update(metrics_dict)
            
            try:
                append_to_excel(result_row)
            except Exception as e:
                print(f"[{current_idx}/{total_accounts}] ❌ 写入磁盘失败: {str(e)}")
                
        context.storage_state(path=STATE_JSON)
        print("\n============================================")
        print(f"[系统] 全部任务运行结束！请查看 {OUTPUT_EXCEL} 文件。")
        print("============================================")
        browser.close()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
韭研公社产业库信息抓取脚本 - 使用 Playwright 处理动态加载
支持抓取行业列表、行业详情和个股明细，输出为 Markdown 格式
"""

import argparse
import json
import sys
import re
import os
import requests
from urllib.parse import urljoin, parse_qs, urlparse

from playwright.sync_api import sync_playwright

# 尝试导入OCR库
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


BASE_URL = "https://www.jiuyangongshe.com"
INDUSTRY_CHAIN_URL = f"{BASE_URL}/industryChain"


def parse_cookie(cookie_str):
    """解析 cookie 字符串为字典"""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def fetch_industry_list(cookie_str):
    """使用 Playwright 抓取行业列表"""
    cookies = parse_cookie(cookie_str)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # 设置 cookie
        context.add_cookies([
            {'name': k, 'value': v, 'domain': '.jiuyangongshe.com', 'path': '/'}
            for k, v in cookies.items()
        ])
        
        page = context.new_page()
        
        print("正在加载页面...", file=sys.stderr)
        page.goto(INDUSTRY_CHAIN_URL, wait_until='networkidle', timeout=60000)
        
        # 等待页面加载完成
        page.wait_for_timeout(3000)
        
        # 尝试多种选择器来获取行业列表
        industries = []
        seen_names = set()
        
        # 方法1: 从页面文本中提取行业名称和ID
        all_text = page.inner_text('body')
        lines = all_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # 匹配行业名称模式："美、以-伊朗冲突(260301)" 或 "AI HALO公司梳理机构版（260302）"
            if (re.search(r'[\u4e00-\u9fa5]+[（\(][0-9]+[）\)]', line) or 
                re.search(r'[\u4e00-\u9fa5]+[\u3001/\-]', line)) and len(line) < 100:
                # 过滤掉无效的行业名称
                if '可在搜索框内搜索更多行业' in line:
                    continue
                
                # 去重：基于行业名称
                name_key = line
                if name_key and name_key not in seen_names:
                    seen_names.add(name_key)
                    
                    # 尝试从文本中提取行业ID
                    industry_id = None
                    # 尝试匹配括号中的数字
                    id_match = re.search(r'[（\(](\d+)[）\)]', line)
                    if id_match:
                        industry_id = id_match.group(1)
                    
                    # 构建行业URL
                    url = f"{BASE_URL}/industryChain/{industry_id}" if industry_id else ''
                    
                    industries.append({
                        'name': line,
                        'url': url,
                        'industry_id': industry_id
                    })
        
        # 方法2: 尝试从链接中提取
        link_elements = page.query_selector_all('a')
        for elem in link_elements:
            text = elem.inner_text().strip()
            href = elem.get_attribute('href') or ''
            
            # 过滤掉通知类内容和功能链接
            if '广播消息' in text or '公社通知' in text or '涨停简图' in text:
                continue
            if '发长文' in text or '发文档' in text or '发链接' in text or '提问' in text or '短文' in text or '发生活' in text:
                continue
            
            if '/industryChain/' in href and text:
                # 从 URL 中提取行业 ID
                industry_id = None
                match = re.search(r'/industryChain/([^/?]+)', href)
                if match:
                    industry_id = match.group(1)
                
                # 去重
                if text not in seen_names:
                    seen_names.add(text)
                    if not href.startswith('http'):
                        href = urljoin(BASE_URL, href)
                    industries.append({
                        'name': text,
                        'url': href,
                        'industry_id': industry_id
                    })
        
        browser.close()
        return industries


def extract_stocks_from_text(text):
    """从文本中提取个股信息"""
    stocks = []
    
    # 按行分割文本
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 尝试匹配股票代码和名称
        # 模式1: 6位数字 + 名称
        match = re.search(r'(\d{6})\s+([^\d]+)', line)
        if match:
            code = match.group(1)
            name = match.group(2).strip()
            # 过滤掉非股票代码
            if not code.startswith('202') and not code.startswith('203'):
                stocks.append({'code': code, 'name': name, 'price': '', 'change': ''})
            continue
        
        # 模式2: 名称 + 6位数字
        match = re.search(r'([^\d]+)\s+(\d{6})', line)
        if match:
            name = match.group(1).strip()
            code = match.group(2)
            # 过滤掉非股票代码
            if not code.startswith('202') and not code.startswith('203'):
                stocks.append({'code': code, 'name': name, 'price': '', 'change': ''})
            continue
        
        # 模式3: 单独的6位数字
        match = re.search(r'\b(\d{6})\b', line)
        if match:
            code = match.group(1)
            # 过滤掉非股票代码
            if not code.startswith('202') and not code.startswith('203'):
                stocks.append({'code': code, 'name': '', 'price': '', 'change': ''})
    
    return stocks


def recognize_image(image_path):
    """识别图片中的文字"""
    if not OCR_AVAILABLE:
        return ""
    
    try:
        # 打开图片
        image = Image.open(image_path)
        
        # 使用OCR识别
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        
        return text
    except Exception as e:
        print(f"识别图片失败 {image_path}: {e}", file=sys.stderr)
        return ""


def download_image(url, save_path):
    """下载图片到本地"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"下载图片失败 {url}: {e}", file=sys.stderr)
    return False


def extract_stocks_from_images(page):
    """从页面中的图片提取个股信息"""
    stocks = []
    
    if not OCR_AVAILABLE:
        print("  警告: OCR不可用，无法识别图片中的个股", file=sys.stderr)
        return stocks
    
    # 创建临时目录保存图片
    temp_dir = 'temp_stock_images'
    os.makedirs(temp_dir, exist_ok=True)
    
    # 查找所有图片
    images = page.query_selector_all('img')
    
    for i, img in enumerate(images):
        try:
            src = img.get_attribute('src') or ''
            
            # 只处理包含个股信息的图片
            if src and ('import' in src or 'industry' in src or 'stock' in src.lower()):
                # 下载图片
                img_filename = os.path.join(temp_dir, f'stock_{i}.png')
                if download_image(src, img_filename):
                    # 识别图片
                    text = recognize_image(img_filename)
                    if text:
                        # 提取个股信息
                        image_stocks = extract_stocks_from_text(text)
                        stocks.extend(image_stocks)
        except Exception as e:
            print(f"处理图片失败: {e}", file=sys.stderr)
    
    # 清理临时文件
    try:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            os.remove(file_path)
        os.rmdir(temp_dir)
    except:
        pass
    
    return stocks


def fetch_industry_detail_with_stocks(industry_id, cookie_str):
    """使用 Playwright 抓取行业详情和个股明细"""
    cookies = parse_cookie(cookie_str)
    
    detail_url = f"{BASE_URL}/industryChain/{industry_id}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # 设置 cookie
        context.add_cookies([
            {'name': k, 'value': v, 'domain': '.jiuyangongshe.com', 'path': '/'}
            for k, v in cookies.items()
        ])
        
        # 存储 API 响应
        api_data = {}
        
        def handle_response(response):
            # 捕获更多可能的 API 端点
            if any(keyword in response.url for keyword in ['industry', 'stock', 'detail', 'chain']):
                try:
                    data = response.json()
                    api_data[response.url] = data
                except:
                    pass
        
        page = context.new_page()
        page.on('response', handle_response)
        
        print(f"正在加载行业详情页: {detail_url}", file=sys.stderr)
        page.goto(detail_url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        
        # 尝试点击"添加产业图表或个股"按钮
        try:
            add_button = page.query_selector('text=添加产业图表或个股')
            if add_button:
                print("  点击'添加产业图表或个股'按钮...", file=sys.stderr)
                add_button.click()
                page.wait_for_timeout(5000)
        except Exception as e:
            print(f"  点击按钮失败: {e}", file=sys.stderr)
        
        # 尝试滚动页面加载更多内容
        for i in range(10):
            page.evaluate("window.scrollBy(0, 400)")
            page.wait_for_timeout(800)
        
        # 获取页面标题
        title_elem = page.query_selector('h1')
        title = title_elem.inner_text().strip() if title_elem else "未知标题"
        
        # 获取页面内容
        content = ""
        content_selectors = ['article', '.content', '.detail-content', 'main', 'div[class*="content"]']
        for selector in content_selectors:
            elem = page.query_selector(selector)
            if elem:
                content = elem.inner_text().strip()
                if len(content) > 50:
                    break
        
        # 如果没有找到内容，获取 body 文本
        if not content:
            body = page.query_selector('body')
            if body:
                content = body.inner_text().strip()
        
        # 提取个股信息
        stocks = []
        
        # 1. 尝试从 API 响应中提取
        for url, data in api_data.items():
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
                # 尝试不同的数据结构
                if isinstance(data, dict):
                    stock_list = data.get('stocks') or data.get('stock_list') or data.get('list') or []
                    if stock_list:
                        for stock in stock_list:
                            if isinstance(stock, dict):
                                stocks.append({
                                    'code': stock.get('code', ''),
                                    'name': stock.get('name', ''),
                                    'price': stock.get('price', ''),
                                    'change': stock.get('change', ''),
                                })
        
        # 2. 尝试从图片中提取个股信息（OCR）
        if not stocks:
            print("  尝试从图片中识别个股...", file=sys.stderr)
            image_stocks = extract_stocks_from_images(page)
            if image_stocks:
                print(f"  从图片中识别到 {len(image_stocks)} 个个股", file=sys.stderr)
                stocks.extend(image_stocks)
        
        # 3. 尝试从页面文本中提取
        if not stocks:
            all_text = page.inner_text('body')
            # 匹配股票代码模式 (6位数字)
            stock_codes = re.findall(r'\b(\d{6})\b', all_text)
            # 去重并过滤掉非股票代码（如日期等）
            seen_codes = set()
            for code in stock_codes:
                # 过滤掉明显不是股票代码的数字（如日期）
                if code not in seen_codes and not (code.startswith('202') or code.startswith('203')):
                    seen_codes.add(code)
                    stocks.append({'code': code, 'name': '', 'price': '', 'change': ''})
        
        # 4. 尝试从图片 alt 文本中提取
        if not stocks:
            images = page.query_selector_all('img')
            for img in images:
                alt = img.get_attribute('alt') or ''
                if alt:
                    # 从 alt 文本中提取股票代码
                    alt_codes = re.findall(r'\b(\d{6})\b', alt)
                    for code in alt_codes:
                        if code not in seen_codes:
                            seen_codes.add(code)
                            stocks.append({'code': code, 'name': '', 'price': '', 'change': ''})
        
        # 5. 尝试从页面中的表格或列表提取
        if not stocks:
            # 查找可能包含股票信息的元素
            potential_stock_elements = page.query_selector_all('tr, td, li, div[class*="item"]')
            for elem in potential_stock_elements:
                try:
                    text = elem.inner_text().strip()
                    if text:
                        # 查找股票代码和名称
                        code_match = re.search(r'\b(\d{6})\b', text)
                        if code_match:
                            code = code_match.group(1)
                            # 提取股票名称
                            name_match = re.search(r'\d{6}\s*([^\d]+)', text)
                            name = name_match.group(1).strip() if name_match else ''
                            if code not in seen_codes:
                                seen_codes.add(code)
                                stocks.append({'code': code, 'name': name, 'price': '', 'change': ''})
                except:
                    pass
        
        # 去重
        unique_stocks = []
        seen_codes = set()
        for stock in stocks:
            if stock['code'] and stock['code'] not in seen_codes:
                seen_codes.add(stock['code'])
                unique_stocks.append(stock)
        
        browser.close()
        
        return {
            'title': title,
            'content': content,
            'url': detail_url,
            'industry_id': industry_id,
            'stocks': unique_stocks
        }


def fetch_all_industries_with_stocks(cookie_str):
    """抓取所有行业及其个股明细"""
    # 首先获取行业列表
    industries = fetch_industry_list(cookie_str)
    
    if not industries:
        return []
    
    print(f"\n开始抓取 {len(industries)} 个行业的个股明细...", file=sys.stderr)
    
    results = []
    for idx, industry in enumerate(industries, 1):
        industry_id = industry.get('industry_id')
        if industry_id:
            print(f"[{idx}/{len(industries)}] 抓取: {industry['name']}", file=sys.stderr)
            try:
                detail = fetch_industry_detail_with_stocks(industry_id, cookie_str)
                results.append({
                    'industry': industry,
                    'detail': detail
                })
            except Exception as e:
                print(f"  错误: {e}", file=sys.stderr)
                results.append({
                    'industry': industry,
                    'detail': {'title': industry['name'], 'stocks': [], 'error': str(e)}
                })
        else:
            # 对于没有行业ID的情况，尝试从名称中提取信息
            print(f"[{idx}/{len(industries)}] 分析: {industry['name']}", file=sys.stderr)
            results.append({
                'industry': industry,
                'detail': {'title': industry['name'], 'stocks': [], 'error': '无行业ID'}
            })
    
    return results


def industries_to_markdown(industries):
    """将行业列表转换为 Markdown 格式"""
    md = "# 韭研公社产业库 - 行业列表\n\n"
    md += f"来源: [{INDUSTRY_CHAIN_URL}]({INDUSTRY_CHAIN_URL})\n\n"
    md += f"共找到 {len(industries)} 个行业\n\n"
    md += "| 序号 | 行业名称 | 行业ID | 链接 |\n"
    md += "|------|----------|--------|------|\n"
    
    for idx, industry in enumerate(industries, 1):
        name = industry['name'].replace('|', '\\|')
        url = industry['url']
        industry_id = industry.get('industry_id', '-')
        link_text = f"[链接]({url})" if url else "-"
        md += f"| {idx} | {name} | {industry_id} | {link_text} |\n"
    
    return md


def industries_with_stocks_to_markdown(results):
    """将行业及个股明细转换为 Markdown 格式"""
    md = "# 韭研公社产业库 - 行业及个股明细\n\n"
    md += f"来源: [{INDUSTRY_CHAIN_URL}]({INDUSTRY_CHAIN_URL})\n\n"
    md += f"共 {len(results)} 个行业\n\n"
    md += "---\n\n"
    
    for idx, result in enumerate(results, 1):
        industry = result['industry']
        detail = result['detail']
        
        md += f"## {idx}. {industry['name']}\n\n"
        md += f"- **行业ID**: {industry.get('industry_id', '-')}\n"
        md += f"- **链接**: [{detail.get('url', '-')}]({detail.get('url', '#')})\n\n"
        
        stocks = detail.get('stocks', [])
        if stocks:
            md += "### 个股明细\n\n"
            md += "| 股票代码 | 股票名称 | 价格 | 涨跌幅 |\n"
            md += "|----------|----------|------|--------|\n"
            for stock in stocks[:50]:  # 最多显示50只
                code = stock.get('code', '-')
                name = stock.get('name', '-')
                price = stock.get('price', '-')
                change = stock.get('change', '-')
                md += f"| {code} | {name} | {price} | {change} |\n"
            if len(stocks) > 50:
                md += f"| ... | 共 {len(stocks)} 只个股 | ... | ... |\n"
            md += "\n"
        else:
            md += "*暂无个股数据*\n\n"
        
        md += "---\n\n"
    
    return md


def detail_to_markdown(data):
    """将详情内容转换为 Markdown 格式"""
    md = f"# {data['title']}\n\n"
    md += f"- **行业ID**: {data.get('industry_id', '-')}\n"
    md += f"- **来源**: [{data['url']}]({data['url']})\n\n"
    md += "---\n\n"
    
    stocks = data.get('stocks', [])
    if stocks:
        md += "## 个股明细\n\n"
        md += "| 股票代码 | 股票名称 | 价格 | 涨跌幅 |\n"
        md += "|----------|----------|------|--------|\n"
        for stock in stocks:
            code = stock.get('code', '-')
            name = stock.get('name', '-')
            price = stock.get('price', '-')
            change = stock.get('change', '-')
            md += f"| {code} | {name} | {price} | {change} |\n"
        md += "\n"
    
    md += "## 内容\n\n"
    md += data['content']
    
    return md


def main():
    parser = argparse.ArgumentParser(description='韭研公社产业库信息抓取工具')
    parser.add_argument('--cookie', '-c', help='登录 Cookie（必需）')
    parser.add_argument('--url', '-u', help='指定要抓取的详情页 URL')
    parser.add_argument('--list', '-l', action='store_true', help='抓取行业列表')
    parser.add_argument('--all', '-a', action='store_true', help='抓取所有行业及其个股明细')
    parser.add_argument('--industry-id', '-i', help='指定行业ID抓取详情和个股')
    parser.add_argument('--output', '-o', help='输出文件路径（默认为 stdout）')
    parser.add_argument('--json', '-j', action='store_true', help='同时输出 JSON 格式')
    
    args = parser.parse_args()
    
    if not args.cookie:
        print("错误: 需要提供登录 Cookie。请使用 --cookie 参数提供。", file=sys.stderr)
        print("提示: 在浏览器中登录后，从开发者工具中获取 Cookie。", file=sys.stderr)
        sys.exit(1)
    
    result = None
    data = None
    
    if args.list:
        # 抓取行业列表
        print("正在抓取行业列表...", file=sys.stderr)
        industries = fetch_industry_list(args.cookie)
        if industries:
            result = industries_to_markdown(industries)
            data = industries
            print(f"成功抓取 {len(industries)} 个行业", file=sys.stderr)
        else:
            print("警告: 未找到任何行业数据，请检查 Cookie 是否有效。", file=sys.stderr)
            sys.exit(1)
    
    elif args.all:
        # 抓取所有行业及其个股明细
        print("正在抓取所有行业及其个股明细...", file=sys.stderr)
        results = fetch_all_industries_with_stocks(args.cookie)
        if results:
            result = industries_with_stocks_to_markdown(results)
            data = results
            print(f"\n成功抓取 {len(results)} 个行业的数据", file=sys.stderr)
        else:
            print("警告: 未找到任何数据，请检查 Cookie 是否有效。", file=sys.stderr)
            sys.exit(1)
    
    elif args.industry_id:
        # 抓取指定行业详情和个股
        print(f"正在抓取行业 {args.industry_id} 的详情...", file=sys.stderr)
        detail_data = fetch_industry_detail_with_stocks(args.industry_id, args.cookie)
        result = detail_to_markdown(detail_data)
        data = detail_data
    
    elif args.url:
        # 从 URL 提取 industry_id
        parsed = urlparse(args.url)
        # 匹配 https://www.jiuyangongshe.com/industryChain/{industry_id}
        match = re.search(r'/industryChain/([^/?]+)', parsed.path)
        if match:
            industry_id = match.group(1)
            print(f"正在抓取行业 {industry_id} 的详情...", file=sys.stderr)
            detail_data = fetch_industry_detail_with_stocks(industry_id, args.cookie)
            result = detail_to_markdown(detail_data)
            data = detail_data
        else:
            print("错误: 无法从 URL 提取行业ID", file=sys.stderr)
            sys.exit(1)
    
    else:
        print("错误: 请指定操作类型：", file=sys.stderr)
        print("  --list    抓取行业列表", file=sys.stderr)
        print("  --all     抓取所有行业及其个股明细", file=sys.stderr)
        print("  --industry-id  抓取指定行业详情", file=sys.stderr)
        print("  --url     抓取指定详情页", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
        
        # 同时输出 JSON
        if args.json and data:
            json_path = args.output.replace('.md', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON 数据已保存到: {json_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == '__main__':
    main()

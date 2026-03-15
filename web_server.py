# -*- coding: utf-8 -*-
"""
基金估值与K线监控系统 - Web服务器
提供可视化的基金管理、持仓编辑、估值监控等功能
作者：基于项目需求开发
日期：2026-02-08
"""

from flask import Flask, render_template, request, jsonify, send_file
from api.FundValuationAPI import FundValuationAPI
from database.FundDatabase import FundDatabase
from scripts.txt2str import file2json
from utils.Logger import Logger
from utils.errors import api_endpoint, success_response, error_response, NotFoundError, APIError, ValidationError
from utils.IndexDescription import (
    initialize_descriptions, 
    load_descriptions_from_config, 
    save_descriptions_to_config,
    auto_fetch_missing_descriptions
)
from datetime import datetime
import json
import os
import time

# 初始化日志
log = Logger('logs/web_server.log', level='info').logger

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


# 全局模板上下文处理器 - 确保所有模板都能访问推广配置
@app.context_processor
def inject_promotion_config():
    return {'promotion_config': load_promotion_config()}


# 配置文件路径（现在只存UI配置）
UI_CONFIG_FILE = 'data/zs_fund_online_ui.json'
DB_FILE = 'data/funds.db'
CONFIG_FILE = UI_CONFIG_FILE  # 兼容旧代码
PROMOTION_CONFIG_FILE = 'config/promotion.json'

# 创建数据库实例
db = FundDatabase(DB_FILE)

# 创建 API实例（传入数据库路径）
fund_api = FundValuationAPI(db_path=DB_FILE)


def ensure_descriptions_initialized():
    """确保板块描述已初始化，自动获取缺失的描述"""
    try:
        # 加载现有配置
        ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
        zs_all = ui_config.get('zs_all', {})
        
        if not zs_all:
            return
        
        # 检查是否已有描述数据
        existing_desc = ui_config.get('zs_descriptions', {})
        
        # 检查是否需要初始化（首次运行或新增板块）
        missing_count = 0
        for code in zs_all:
            if code not in existing_desc or not existing_desc.get(code):
                missing_count += 1
        
        if missing_count > 0:
            log.info(f"[描述初始化] 检测到 {missing_count}/{len(zs_all)} 个板块缺少描述，自动获取中...")
            # 使用自动获取功能（会优先使用预定义，然后联网，最后默认）
            descriptions = auto_fetch_missing_descriptions(UI_CONFIG_FILE, zs_all)
            log.info(f"[描述初始化] 完成，共 {len(descriptions)} 个板块描述")
        else:
            log.info(f"[描述初始化] 所有板块描述已存在，共 {len(existing_desc)} 个")
            
    except Exception as e:
        log.error(f"[描述初始化] 初始化失败: {e}")


def check_and_fetch_missing_descriptions():
    """检查并获取新添加板块的描述"""
    try:
        # 加载现有配置
        ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
        zs_all = ui_config.get('zs_all', {})
        
        if not zs_all:
            return
        
        # 自动获取缺失的描述
        auto_fetch_missing_descriptions(UI_CONFIG_FILE, zs_all)
            
    except Exception as e:
        log.error(f"[描述检查] 检查失败: {e}")


# 启动时初始化板块描述
ensure_descriptions_initialized()


def load_promotion_config():
    """加载推广配置"""
    try:
        if os.path.exists(PROMOTION_CONFIG_FILE):
            with open(PROMOTION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"加载推广配置失败: {e}")
    return {
        "qq_groups": [],
        "show_qq_groups": False,
        "button_text": "👥 加群交流",
        "button_style": {"background": "#12B7F5", "color": "white"}
    }


def generate_monitor_html():
    """生成监控页面HTML"""
    try:
        # 从数据库获取基金列表
        fund_list = db.get_fund_codes()
        
        # 从UI配置文件获取K线设置
        ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
        dict_zs_all = ui_config.get('zs_all', {})
        list_type = ui_config.get('type_all', ['D', 'W', 'M'])
        list_formula = ui_config.get('formula_all', ['MACD'])
        int_unitWidth = ui_config.get('unitWidth', -5)
        zs_descriptions = ui_config.get('zs_descriptions', {})
        
        # 加载推广配置
        promotion_config = load_promotion_config()
        
        # 生成HTML
        return render_template(
            'monitor.html',
            fund_list=fund_list,
            dict_zs_all=dict_zs_all,
            list_type=list_type,
            list_formula=list_formula,
            int_unitWidth=int_unitWidth,
            zs_descriptions=zs_descriptions,
            promotion_config=promotion_config,
            update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        return f'错误: {str(e)}', 500


@app.route('/')
def index():
    """主页 - 显示监控页面"""
    return generate_monitor_html()


@app.route('/admin')
def admin():
    """管理页面 - 显示控制面板"""
    return render_template('admin.html')


@app.route('/api/config', methods=['GET'])
@api_endpoint
def get_config():
    """获取配置信息（混合模式：数据库+UI配置）"""
    # 1. 使用JOIN查询批量获取所有基金核心数据
    funds_with_holdings = db.get_funds_with_holdings()
    

    fund_list = list(funds_with_holdings.keys())
    user_positions = {
        fund_code: fund_data.get('user_position', 0)
        for fund_code, fund_data in funds_with_holdings.items()
    }
    fund_holdings_formatted = {
        fund_code: {'holdings': fund_data.get('holdings', [])}
        for fund_code, fund_data in funds_with_holdings.items()
        if fund_data.get('holdings')
    }
    
    # 2. 从UI配置文件获取K线设置
    ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
    
    # 3. 合并返回
    config = {
        'fund_list': fund_list,
        'user_positions': user_positions,
        'fund_holdings': fund_holdings_formatted,
        'zs_all': ui_config.get('zs_all', {}),
        'zs_descriptions': ui_config.get('zs_descriptions', {}),
        'type_all': ui_config.get('type_all', ['D', 'W', 'M']),
        'formula_all': ui_config.get('formula_all', ['MACD']),
        'unitWidth': ui_config.get('unitWidth', -5)
    }
    
    return success_response(config)


@app.route('/api/config', methods=['POST'])
@api_endpoint
def save_config():
    """保存配置信息（只保存UI配置），自动获取新增板块的描述"""
    data = request.json
    
    # 加载现有配置以保留描述信息
    existing_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
    
    # 新的板块配置
    new_zs_all = data.get('zs_all', {})
    existing_descriptions = existing_config.get('zs_descriptions', {})
    
    # 只保存UI相关配置
    ui_config = {
        'zs_all': new_zs_all,
        'zs_descriptions': existing_descriptions,  # 保留描述信息
        'type_all': data.get('type_all', ['D', 'W', 'M']),
        'formula_all': data.get('formula_all', ['MACD']),
        'unitWidth': data.get('unitWidth', -5)
    }
    
    with open(UI_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(ui_config, f, ensure_ascii=False, indent=2)
    
    log.info("UI配置保存成功")
    
    # 检查是否有新增板块需要获取描述
    # 在后台线程中执行，避免阻塞响应
    import threading
    def fetch_descriptions_async():
        time.sleep(1)  # 延迟1秒，确保文件写入完成
        try:
            check_and_fetch_missing_descriptions()
        except Exception as e:
            log.error(f"[异步描述获取] 失败: {e}")
    
    threading.Thread(target=fetch_descriptions_async, daemon=True).start()
    
    return success_response(None, '配置保存成功，后台自动获取新增板块描述中')


@app.route('/api/index/descriptions', methods=['GET'])
@api_endpoint
def get_index_descriptions():
    """获取所有板块指数描述"""
    ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
    descriptions = ui_config.get('zs_descriptions', {})
    return success_response(descriptions)


@app.route('/api/index/description/<index_code>', methods=['GET'])
@api_endpoint
def get_single_index_description(index_code):
    """获取单个板块指数描述（如果不存在会自动获取）"""
    ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
    zs_all = ui_config.get('zs_all', {})
    descriptions = ui_config.get('zs_descriptions', {})
    
    # 如果描述不存在，尝试自动获取
    if index_code not in descriptions or not descriptions.get(index_code):
        if index_code in zs_all:
            log.info(f"[API] 板块 {index_code} 描述不存在，尝试自动获取...")
            # 创建一个只包含该板块的字典
            single_zs = {index_code: zs_all[index_code]}
            new_descriptions = auto_fetch_missing_descriptions(UI_CONFIG_FILE, single_zs)
            descriptions = new_descriptions
    
    if index_code in descriptions and descriptions[index_code]:
        return success_response({
            'code': index_code,
            'description': descriptions[index_code]
        })
    else:
        return error_response(NotFoundError('板块描述', index_code))


@app.route('/api/index/description/<index_code>/fetch', methods=['POST'])
@api_endpoint
def fetch_single_index_description(index_code):
    """手动触发获取单个板块指数描述（强制联网获取）"""
    try:
        ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
        zs_all = ui_config.get('zs_all', {})
        
        if index_code not in zs_all:
            return error_response(NotFoundError('板块', index_code))
        
        # 强制重新获取该板块的描述
        from utils.IndexDescription import get_index_description_from_eastmoney, fetch_index_info_from_eastmoney, generate_default_description
        
        info = zs_all[index_code]
        index_name = info[0] if isinstance(info, list) else str(info)
        
        log.info(f"[API] 手动获取板块 {index_name}({index_code}) 描述...")
        
        # 尝试联网获取
        description = get_index_description_from_eastmoney(index_code, index_name)
        
        if not description:
            # 尝试获取详细信息
            info_data = fetch_index_info_from_eastmoney(index_code, index_name)
            if info_data:
                description = f"{index_name}是{info_data.get('name', '指数')}，反映相关板块的整体表现。"
        
        if not description:
            # 使用默认描述
            description = generate_default_description(index_code, index_name)
        
        # 保存到配置
        if 'zs_descriptions' not in ui_config:
            ui_config['zs_descriptions'] = {}
        
        ui_config['zs_descriptions'][index_code] = description
        
        with open(UI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(ui_config, f, ensure_ascii=False, indent=2)
        
        log.info(f"[API] 板块 {index_code} 描述获取成功")
        return success_response({
            'code': index_code,
            'name': index_name,
            'description': description,
            'source': 'online' if '是' in description and '指数' in description else 'default'
        }, '描述获取成功')
        
    except Exception as e:
        log.error(f"[API] 获取描述失败: {e}")
        return error_response(APIError(f'获取描述失败: {str(e)}', 500, 'FETCH_ERROR'))


@app.route('/api/index/description/<index_code>', methods=['PUT'])
@api_endpoint
def update_index_description(index_code):
    """更新单个板块指数描述"""
    data = request.json
    description = data.get('description', '')
    
    # 加载现有配置
    ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
    
    # 更新描述
    if 'zs_descriptions' not in ui_config:
        ui_config['zs_descriptions'] = {}
    
    ui_config['zs_descriptions'][index_code] = description
    
    # 保存配置
    with open(UI_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(ui_config, f, ensure_ascii=False, indent=2)
    
    log.info(f"更新板块 {index_code} 描述: {description[:50]}...")
    return success_response(None, '描述更新成功')


@app.route('/api/index/descriptions/refresh', methods=['POST'])
@api_endpoint
def refresh_index_descriptions():
    """强制刷新所有板块指数描述"""
    try:
        ui_config = file2json(UI_CONFIG_FILE) if os.path.exists(UI_CONFIG_FILE) else {}
        zs_all = ui_config.get('zs_all', {})
        
        if not zs_all:
            return error_response(APIError('没有可刷新的板块数据', 400, 'NO_DATA'))
        
        # 检查是否有缺失的描述
        existing_desc = ui_config.get('zs_descriptions', {})
        missing_codes = [code for code in zs_all if code not in existing_desc or not existing_desc.get(code)]
        
        if missing_codes:
            # 自动获取缺失的描述
            descriptions = auto_fetch_missing_descriptions(UI_CONFIG_FILE, zs_all)
            return success_response({
                'count': len(descriptions),
                'missing_fetched': len(missing_codes),
                'descriptions': descriptions
            }, f'描述刷新成功，新增 {len(missing_codes)} 个板块描述')
        else:
            return success_response({
                'count': len(existing_desc),
                'descriptions': existing_desc
            }, '所有板块描述已存在，无需刷新')
    except Exception as e:
        log.error(f"刷新描述失败: {e}")
        return error_response(APIError(f'刷新描述失败: {str(e)}', 500, 'REFRESH_ERROR'))


@app.route('/api/fund/holdings/<fund_code>', methods=['GET'])
@api_endpoint
def get_fund_holdings(fund_code):
    """获取基金持仓信息"""
    start_time = time.time()
    
    force_update = request.args.get('force_update', 'false').lower() == 'true'
    print(f"[监控] 开始获取基金 {fund_code} 持仓数据 (强制更新: {force_update})")
    
    holdings = fund_api.get_fund_top_holdings(fund_code, force_update=force_update)
    elapsed_time = time.time() - start_time
    
    if not holdings:
        print(f"[监控] 基金 {fund_code} 持仓获取失败，耗时 {elapsed_time:.2f}秒")
        return error_response(NotFoundError('基金持仓', fund_code))
    
    total_ratio = sum(h.get('持仓比例', 0) for h in holdings)
    
    print(f"[监控] 基金 {fund_code} 持仓获取成功，耗时 {elapsed_time:.2f}秒")
    print(f"[监控] 共 {len(holdings)} 只股票，持仓比例合计: {total_ratio:.2f}%")
    
    # 显示前3只股票详情用于调试
    for i, h in enumerate(holdings[:3]):
        stock_code = h.get('股票代码', '未知')
        stock_name = h.get('股票名称', '未知')[:10]
        ratio = h.get('持仓比例', 0)
        print(f"[监控]   {i+1:2d}. {stock_code} {stock_name:<10} 持仓比例: {ratio:6.2f}%")
    if len(holdings) > 3:
        print(f"[监控]   ... 还有 {len(holdings)-3} 只股票")
    
    warning = None
    if total_ratio > 100:
        warning = f'警告：持仓总比例超过100% ({total_ratio:.2f}%)，可能存在数据错误！'
        print(f"[监控] ⚠️ 警告: {warning}")
    
    # 构造响应数据
    response_data = {
        'fund_code': fund_code,
        'holdings': holdings,
        'total_ratio': total_ratio
    }
    if warning:
        response_data['warning'] = warning
    
    return success_response(response_data)


@app.route('/api/fund/holdings/<fund_code>', methods=['PUT'])
@api_endpoint
def update_fund_holdings(fund_code):
    """更新基金持仓信息"""
    holdings = request.json.get('holdings', [])
    fund_api._save_fund_holdings(fund_code, holdings)
    
    return success_response(None, '持仓信息已更新')


@app.route('/api/fund/valuation/<fund_code>', methods=['GET'])
@api_endpoint
def get_fund_valuation(fund_code):
    """计算单个基金估值"""
    import time
    start_time = time.time()
    
    log.info(f"[性能] 开始计算基金 [{fund_code}] 估值")
    result = fund_api.calculate_fund_valuation(fund_code)
    
    elapsed_time = time.time() - start_time
    log.info(f"[性能] API层总耗时 [{fund_code}]: {elapsed_time:.2f}秒")
    
    if not result:
        return error_response(APIError('基金估值计算失败', 500, 'VALUATION_ERROR'))
    
    # 将耗时信息添加到结果中
    result['elapsed_time'] = round(elapsed_time, 2)
    return success_response(result)


@app.route('/api/fund/valuation/batch', methods=['POST'])
@api_endpoint
def batch_fund_valuation():
    """批量计算基金估值，并返回用户持仓信息"""
    import time
    start_time = time.time()
    
    fund_codes = request.json.get('fund_codes', [])
    
    log.info(f"[性能] 开始批量计算 {len(fund_codes)} 个基金估值")
    results = fund_api.batch_calculate_valuations(fund_codes)
    
    elapsed_time = time.time() - start_time
    log.info(f"[性能] 批量计算总耗时: {elapsed_time:.2f}秒, 平均每个: {elapsed_time/len(fund_codes):.2f}秒")
    
    # 从数据库获取用户持仓配置
    user_positions = db.get_user_positions()
    
    # 计算总持仓金额
    total_position = sum(user_positions.values())
    
    # 添加用户持仓信息
    for code, val in results.items():
        position_amount = user_positions.get(code, 0)
        if not isinstance(position_amount, (int, float)):
            position_amount = 0
        
        # 持仓比例 = 当前基金持仓 / 总持仓
        position_ratio = (position_amount / total_position * 100) if total_position > 0 else 0
        
        # 单日盈亏 = 持仓金额 * 估算涨跌幅%
        change_pct = val.get('估算涨跌幅', 0)
        if not isinstance(change_pct, (int, float)):
            change_pct = 0
        daily_profit = position_amount * (change_pct / 100)
        
        val['持仓金额'] = position_amount
        val['持仓比例'] = position_ratio
        val['单日盈亏'] = daily_profit
    
    # 构造响应数据
    response_data = {
        'results': results,
        'total_position': total_position,
        'elapsed_time': round(elapsed_time, 2),
        'avg_time_per_fund': round(elapsed_time / len(fund_codes), 2) if fund_codes else 0
    }
    
    return success_response(response_data)


# 已移除旧版静态HTML生成功能，现已使用Flask动态页面替代
# 如需静态HTML功能，请参考文档中的说明


@app.route('/api/fund/list', methods=['GET'])
@api_endpoint
def get_fund_list():
    """获取基金列表（从数据库）"""
    # 使用JOIN查询批量获取所有基金及其持仓信息
    funds_with_holdings = db.get_funds_with_holdings()
    

    funds = []
    for fund_code, fund_data in funds_with_holdings.items():
        fund_info = {
            'code': fund_code,
            'name': fund_data.get('fund_name', ''),
            'has_holdings': len(fund_data.get('holdings', [])) > 0,
            'holdings_count': len(fund_data.get('holdings', []))
        }
        
        # 如果数据库没有基金名称，尝试从API获取（保持向后兼容）
        if not fund_info['name']:
            try:
                basic_info = fund_api.get_fund_basic_info(fund_code)
                if basic_info:
                    fund_info['name'] = basic_info.get('基金名称', '')
            except:
                fund_info['name'] = ''
        
        funds.append(fund_info)
    
    return success_response(funds)


@app.route('/api/fund/preview/<fund_code>', methods=['GET'])
@api_endpoint
def preview_fund(fund_code):
    """预览基金持仓（不添加到监控列表）"""
    # 验证基金代码格式
    if not fund_code.isdigit() or len(fund_code) != 6:
        return error_response(ValidationError('基金代码必须为6位数字'))
    
    # 验证基金是否存在
    fund_info = fund_api.get_fund_basic_info(fund_code)
    if not fund_info:
        return error_response(NotFoundError('基金', fund_code))
    
    fund_name = fund_info.get('基金名称', fund_code)
    
    # 检查是否已存在（从数据库检查）
    fund_codes = db.get_fund_codes()
    if fund_code in fund_codes:
        return error_response(ValidationError(f'基金 {fund_name} ({fund_code}) 已存在于监控列表中'))
    
    # 获取持仓信息
    log.info(f"预览基金 [{fund_code}] 持仓信息")
    holdings = fund_api.get_fund_top_holdings(fund_code, force_update=True)
    
    if not holdings:
        return error_response(NotFoundError('基金持仓', fund_code))
    
    # 计算前十大重仓股累计比例
    total_ratio = sum(h.get('持仓比例', 0) for h in holdings)
    
    response_data = {
        'fund_code': fund_code,
        'fund_name': fund_name,
        'holdings': holdings,
        'holdings_count': len(holdings),
        'total_ratio': round(total_ratio, 2)  # 前十大重仓股累计比例
    }
    
    return success_response(response_data)




@app.route('/api/fund/add', methods=['POST'])
@api_endpoint
def add_fund():
    """添加基金到监控列表（带验证和自动获取持仓）"""
    fund_code = request.json.get('fund_code', '').strip()
    
    # 规则检查 1: 基金代码必须为6位数字
    if not fund_code:
        return error_response(ValidationError('请输入基金代码'))
    
    if not fund_code.isdigit() or len(fund_code) != 6:
        return error_response(ValidationError('基金代码必须为6位数字，请检查后重试'))
    
    # 规则检查 2: 联网验证基金是否存在
    fund_info = fund_api.get_fund_basic_info(fund_code)
    if not fund_info:
        return error_response(NotFoundError('基金', fund_code))
    
    fund_name = fund_info.get('基金名称', fund_code)
    
    # 直接尝试添加到数据库（让数据库处理重复检查，避免竞态条件）
    if not db.add_fund(fund_code, fund_name, 0):
        return error_response(ValidationError(f'基金 {fund_name} ({fund_code}) 已存在于监控列表中或添加失败'))
    
    # 现在获取持仓信息
    log.info(f"开始为新添加的基金 [{fund_code}] 获取持仓信息")
    holdings = fund_api.get_fund_top_holdings(fund_code, force_update=True)
    
    if not holdings:
        log.warning(f"基金 [{fund_code}] 已添加，但获取持仓失败")
        response_data = {
            'fund_code': fund_code,
            'fund_name': fund_name,
            'holdings_count': 0
        }
        return success_response(response_data, '基金已添加，但获取持仓信息失败，请稍后手动刷新')
    
    log.info(f"基金 [{fund_code}] 添加成功，持仓信息已自动获取 ({len(holdings)} 只股票)")
    
    response_data = {
        'fund_code': fund_code,
        'fund_name': fund_name,
        'holdings_count': len(holdings)
    }
    return success_response(response_data, f'基金添加成功！已自动获取 {len(holdings)} 只重仓股票信息')


@app.route('/api/fund/remove/<fund_code>', methods=['DELETE'])
@api_endpoint
def remove_fund(fund_code):
    """从监控列表移除基金（同时删除所有相关数据）"""
    # 检查基金是否存在
    if not db.fund_exists(fund_code):
        return error_response(NotFoundError('基金', fund_code))
    
    # 从数据库删除（级联删除持仓数据）
    if db.remove_fund(fund_code):
        log.info(f"基金 [{fund_code}] 及其所有相关数据已完全移除")
        return success_response(None, '基金移除成功')
    else:
        return error_response(APIError('移除基金失败', 500, 'REMOVE_ERROR'))


@app.route('/api/fund/position/<fund_code>', methods=['PUT'])
@api_endpoint
def update_fund_position(fund_code):
    """修改用户持仓金额"""
    data = request.json
    position_amount = data.get('position_amount', 0)
    
    if not isinstance(position_amount, (int, float)) or position_amount < 0:
        return error_response(ValidationError('持仓金额必须为非负数字'))
    
    # 更新数据库
    if db.update_user_position(fund_code, position_amount):
        log.info(f"更新基金 [{fund_code}] 持仓金额: {position_amount}")
        return success_response(None, f'基金 {fund_code} 持仓金额已更新为 {position_amount} 元')
    else:
        return error_response(NotFoundError('基金', fund_code))


# 已移除旧版静态HTML查看功能，现已使用Flask动态页面替代
# 如需静态HTML功能，请参考文档中的说明


import signal

# 全局变量，用于控制服务器关闭
server_shutdown = False

@app.route('/api/exit', methods=['POST'])
@api_endpoint
def exit_server():
    """退出服务器并终止程序"""
    global server_shutdown
    log.info("收到退出请求，服务器即将关闭...")
    server_shutdown = True
    
    # 使用定时器延迟退出，确保API响应能返回给客户端
    import threading
    def delayed_exit():
        time.sleep(1)
        log.info("服务器已关闭")
        os._exit(0)
    
    threading.Thread(target=delayed_exit, daemon=True).start()
    return success_response(None, '服务器正在关闭...')


if __name__ == '__main__':
    print("="*60)
    print("基金估值与K线监控系统")
    print("="*60)
    print(f"\n访问地址: http://localhost:5000")
    print(f"数据库: {DB_FILE}")
    print(f"UI配置: {UI_CONFIG_FILE}")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n按 Ctrl+C 停止服务\n")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

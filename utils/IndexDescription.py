# -*- coding: utf-8 -*-
"""
板块指数描述获取工具
用于从网络获取各板块指数的一句话描述
"""

import requests
import json
import os
import time
from typing import Dict, Optional

# 板块描述缓存文件
DESCRIPTION_CACHE_FILE = 'data/zs_descriptions_cache.json'

# 板块描述API配置
# 使用东方财富或同花顺的公开API获取板块信息
EASTMONEY_QUOTE_API = "https://searchapi.eastmoney.com/api/suggest/get"


def get_index_description_from_eastmoney(index_code: str, index_name: str) -> Optional[str]:
    """
    从东方财富搜索API获取板块描述
    
    Args:
        index_code: 指数代码
        index_name: 指数名称
        
    Returns:
        板块描述字符串，获取失败返回None
    """
    try:
        # 构造请求参数
        params = {
            'input': index_name,
            'type': '14',  # 指数类型
            'count': '5',
            'province': '',
            'locus': '',
            'token': 'D43BF722C8E3375CA9598A5ED23B68D1'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
        
        response = requests.get(EASTMONEY_QUOTE_API, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析搜索结果
        if data and 'QuotationCodeTable' in data and 'Data' in data['QuotationCodeTable']:
            items = data['QuotationCodeTable']['Data']
            for item in items:
                # 匹配指数名称或代码
                if item.get('Name') == index_name or item.get('Code') in index_code:
                    # 构造描述信息
                    security_type = item.get('SecurityTypeName', '指数')
                    code = item.get('Code', '')
                    return f"{index_name}是{security_type}，代码{code}，反映相关板块的整体表现。"
        
        return None
    except Exception as e:
        print(f"[描述获取] 获取 {index_name}({index_code}) 描述失败: {e}")
        return None


def get_index_description_from_local(index_code: str, descriptions: Dict[str, str]) -> str:
    """
    从本地配置获取板块描述
    
    Args:
        index_code: 指数代码
        descriptions: 本地描述字典
        
    Returns:
        板块描述字符串，不存在返回空字符串
    """
    return descriptions.get(index_code, '')


def generate_default_description(index_code: str, index_name: str) -> str:
    """
    生成默认的板块描述
    
    Args:
        index_code: 指数代码
        index_name: 指数名称
        
    Returns:
        默认描述字符串
    """
    # 根据板块名称关键词生成描述
    descriptions_map = {
        '科创': '科创板相关指数，聚焦科技创新企业，具有高成长、高波动特征。',
        '创业': '创业板指数，反映创业板市场整体表现，以成长型企业为主。',
        '上证': '上海证券交易所相关指数，代表沪市整体或特定板块表现。',
        '深证': '深圳证券交易所相关指数，代表深市整体或特定板块表现。',
        '沪深': '跨沪深两市的指数，综合反映A股市场表现。',
        '中证': '中证指数公司编制，覆盖特定行业或主题板块。',
        '半导体': '聚焦半导体产业链，涵盖芯片设计、制造、封测等环节。',
        '芯片': '追踪芯片产业相关公司，反映国产替代和技术创新进程。',
        '新能源': '覆盖新能源汽车、光伏、风电等清洁能源领域。',
        '医药': '涵盖医药制造、医疗服务、创新药等细分领域。',
        '医疗': '聚焦医疗器械、医疗服务等相关产业。',
        '白酒': '以白酒行业龙头企业为代表，具有消费防御属性。',
        '消费': '涵盖食品饮料、家用电器等日常消费领域。',
        '银行': '以商业银行为主要成分股，具有高股息、低波动特征。',
        '券商': '反映证券行业整体表现，与市场成交活跃度高度相关。',
        '军工': '涵盖航空航天、船舶制造、军工电子等国防相关产业。',
        '科技': '聚焦科技创新领域，涵盖电子、计算机、通信等行业。',
        '人工智能': '追踪AI产业链相关公司，包括算法、算力、应用等环节。',
        '机器人': '涵盖工业机器人、服务机器人及核心零部件企业。',
        '黄金': '追踪黄金价格走势，具有避险和抗通胀属性。',
        '原油': '反映国际原油价格变动，与全球经济周期密切相关。',
        '纳斯达克': '美国纳斯达克市场指数，以科技股为主导。',
        '日经': '日本东京股市主要指数，反映日本经济表现。',
        '恒生': '香港恒生系列指数，覆盖港股主要行业板块。',
        '越南': '越南股市主要指数，代表新兴市场投资机会。',
        '印度': '印度股市主要指数，反映印度经济发展状况。',
        '东南亚': '东南亚地区科技相关指数，布局新兴市场。',
        '煤炭': '涵盖煤炭开采、煤化工等相关产业。',
        '电力': '覆盖发电、电网等电力产业链相关企业。',
        '稀土': '聚焦稀土开采、加工及应用领域企业。',
        '农业': '涵盖种植业、畜牧业、农产品加工等农业产业链。',
        '养殖': '聚焦畜禽养殖及相关饲料、疫苗产业链。',
        '传媒': '涵盖影视、游戏、广告、出版等文化传媒产业。',
        '金融科技': '融合金融与科技，涵盖互联网金融、区块链等领域。',
        '大数据': '聚焦大数据采集、存储、分析及应用服务企业。',
        '通信': '涵盖电信运营、通信设备、光通信等通信产业链。',
        '消费电子': '覆盖智能手机、可穿戴设备等消费电子产业链。',
        '智能汽车': '聚焦智能网联汽车及相关零部件产业。',
        '光伏': '涵盖光伏产业链上游硅料至下游电站运营全环节。',
        '电池': '覆盖动力电池、储能电池及相关材料企业。',
        '储能': '聚焦储能系统、储能电池及储能变流器等产业。',
        '创新药': '以创新药研发企业为主，具有高投入、高回报特征。',
        '中药': '涵盖中药制造、中药材种植等传统医药产业。',
        '脑机接口': '前沿科技领域，聚焦脑科学与人工智能结合应用。',
        '商业航天': '涵盖卫星制造、火箭发射等商业航天产业链。',
        'CPO': '光电共封装技术相关，是光通信领域前沿方向。',
        '固态电池': '新一代电池技术，具有高能量密度和安全性优势。',
        '小微盘': '反映小市值股票整体表现，具有高弹性特征。',
        '北证': '北京证券交易所相关指数，聚焦创新型中小企业。',
    }
    
    # 匹配关键词
    for keyword, desc in descriptions_map.items():
        if keyword in index_name:
            return f"{index_name}{desc}"
    
    # 默认描述
    return f"{index_name}是反映相关板块整体表现的重要指数。"


def fetch_all_index_descriptions(zs_all: Dict, existing_descriptions: Dict[str, str] = None) -> Dict[str, str]:
    """
    批量获取所有板块指数描述
    
    Args:
        zs_all: 板块配置字典 {code: [name, ...]}
        existing_descriptions: 已存在的描述字典
        
    Returns:
        更新后的描述字典
    """
    if existing_descriptions is None:
        existing_descriptions = {}
    
    descriptions = existing_descriptions.copy()
    
    print("[描述获取] 开始获取板块指数描述...")
    
    for index_code, info in zs_all.items():
        # 如果已存在描述，跳过
        if index_code in descriptions and descriptions[index_code]:
            print(f"[描述获取] {index_code} 已存在描述，跳过")
            continue
        
        index_name = info[0] if isinstance(info, list) else str(info)
        
        print(f"[描述获取] 正在获取 {index_name}({index_code}) 的描述...")
        
        # 尝试从网络获取
        online_desc = get_index_description_from_eastmoney(index_code, index_name)
        
        if online_desc:
            descriptions[index_code] = online_desc
        else:
            # 使用默认描述
            descriptions[index_code] = generate_default_description(index_code, index_name)
        
        # 添加延迟，避免请求过快
        time.sleep(0.5)
    
    print(f"[描述获取] 完成，共获取 {len(descriptions)} 个板块描述")
    return descriptions


def load_descriptions_from_config(config_file: str) -> Dict[str, str]:
    """
    从配置文件加载板块描述
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        描述字典
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('zs_descriptions', {})
    except Exception as e:
        print(f"[描述加载] 加载描述失败: {e}")
    
    return {}


def save_descriptions_to_config(config_file: str, descriptions: Dict[str, str]):
    """
    保存板块描述到配置文件
    
    Args:
        config_file: 配置文件路径
        descriptions: 描述字典
    """
    try:
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config['zs_descriptions'] = descriptions
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"[描述保存] 已保存 {len(descriptions)} 个板块描述到配置文件")
    except Exception as e:
        print(f"[描述保存] 保存描述失败: {e}")


# 预定义的详细描述数据（用于离线时或获取失败时使用）
PREDEFINED_DESCRIPTIONS = {
    "1.000001": "上证指数是上海证券交易所编制的综合股价指数，反映沪市整体走势，是中国A股市场最重要的基准指数之一。",
    "1.000300": "沪深300指数由沪深两市市值大、流动性好的300只股票组成，综合反映中国A股市场整体表现，是股指期货的标的指数。",
    "90.BK0701": "中证500指数由全部A股中剔除沪深300指数成分股后总市值排名靠前的500只股票组成，反映中小市值公司整体表现。",
    "0.399330": "深证100指数由深圳市场市值大、成交活跃的100只A股组成，是深圳市场的旗舰指数，代表深市核心资产。",
    "1.000016": "上证50指数由沪市规模大、流动性好的最具代表性的50只股票组成，反映上海市场大盘蓝筹股整体表现。",
    "2.932000": "小微盘指数聚焦小市值股票，具有高弹性、高波动特征，适合风险偏好较高的投资者关注。",
    "0.899050": "北证50指数是北京证券交易所首只宽基指数，由北交所市值规模大、流动性好的50只股票组成。",
    "1.000698": "科创100指数是科创板中小市值成长股的代表指数，聚焦半导体、生物医药、新能源等硬科技领域，具有高弹性、高波动特征，是布局科技创新前沿的核心宽基工具。",
    "1.000688": "科创50指数由科创板市值最大、流动性好的50只股票组成，反映最具市场代表性的一批科创板企业整体表现。",
    "0.399006": "创业板指数由创业板市场中市值大、流动性好的100只股票组成，反映创业板市场整体运行情况，以成长型企业为主。",
    "2.931643": "双创50指数从科创板和创业板中选取50只新兴产业上市公司，反映双创板块整体表现。",
    "1.000685": "科创板指数反映上海证券交易所科创板市场整体表现，聚焦硬科技领域创新企业。",
    "90.BK1059": "脑机接口板块指数涵盖脑机接口技术研发及应用相关企业，是前沿科技投资主题。",
    "90.BK0963": "商业航天板块指数覆盖卫星制造、火箭发射、地面设备等商业航天产业链企业。",
    "2.931071": "人工智能指数追踪AI产业链相关公司，涵盖算法、算力、数据、应用等全链条。",
    "2.H30590": "机器人指数涵盖工业机器人、服务机器人及核心零部件企业，反映机器人产业整体发展。",
    "90.BK1036": "半导体板块指数覆盖芯片设计、制造、封测、设备等半导体全产业链企业，是国产替代核心赛道。",
    "2.931743": "半导体材料设备指数聚焦半导体材料和设备细分领域，是半导体产业上游核心环节。",
    "2.931719": "CS电池指数覆盖动力电池、储能电池及相关材料企业，反映电池产业整体表现。",
    "2.H30007": "存储芯片指数聚焦存储芯片设计、制造及相关设备材料企业，是半导体重要细分领域。",
    "90.BK1128": "CPO概念指数涵盖光电共封装技术相关企业，是光通信领域的前沿发展方向。",
    "0.399282": "大数据50指数由大数据产业相关上市公司组成，覆盖数据采集、存储、分析、应用等环节。",
    "2.931186": "中证科技指数涵盖沪深两市科技领域龙头公司，综合反映中国科技产业整体表现。",
    "2.931380": "大科技指数覆盖电子、计算机、通信等科技行业龙头，反映科技板块整体走势。",
    "2.931140": "通信指数涵盖电信运营、通信设备、光通信等产业链，是信息基础设施的核心。",
    "2.931494": "消费电子指数覆盖智能手机、可穿戴设备、智能家居等消费电子产业链。",
    "90.BK0968": "固态电池板块指数聚焦固态电池技术研发及产业化企业，是下一代电池技术方向。",
    "90.BK0900": "新能源车板块指数覆盖新能源汽车整车及核心零部件企业，反映新能源汽车产业发展。",
    "0.399432": "智能汽车指数涵盖智能网联汽车、自动驾驶、车联网等相关企业。",
    "0.970035": "深证光伏指数覆盖光伏产业链上中下游企业，反映光伏产业发展状况。",
    "0.983160": "低碳科技指数聚焦清洁能源、节能环保、碳减排等低碳经济领域。",
    "0.489013": "稀土指数涵盖稀土开采、分离、加工及应用企业，是战略性资源板块。",
    "2.931167": "先进制造指数覆盖高端装备制造、智能制造等相关企业，反映制造业转型升级。",
    "2.930599": "中证高装指数聚焦高端装备制造领域，是制造业高端化的重要方向。",
    "2.931523": "创新药指数由创新药研发企业组成，具有高投入、高风险、高回报特征。",
    "1.000683": "科创生物指数由科创板生物医药企业组成，反映科创板生物医药产业整体表现。",
    "90.BK0727": "医疗服务板块指数涵盖医疗服务机构、CRO、医疗器械服务等细分领域。",
    "1.000933": "中证医药指数覆盖医药制造、医药商业、医疗器械等全产业链，反映医药行业整体表现。",
    "2.930641": "中证中药指数由中药制造及相关企业组成，反映中药产业发展状况。",
    "124.HSCICH": "恒生医疗保健业指数由港股医疗保健行业公司组成，覆盖医药、器械、服务等领域。",
    "90.BK0711": "券商板块指数由证券公司组成，与市场成交额和资本市场改革高度相关，具有高弹性特征。",
    "0.399699": "金融科技指数涵盖互联网金融、区块链、数字支付等金融科技领域。",
    "0.399959": "军工指数覆盖航空航天、船舶制造、军工电子等国防军工产业链。",
    "2.931009": "建筑材料指数由水泥、玻璃、管材等建材企业组成，与房地产和基建投资密切相关。",
    "2.H30199": "电力指数涵盖发电、电网等电力产业链企业，具有公用事业防御属性。",
    "1.000820": "煤炭指数覆盖煤炭开采、煤化工等企业，与能源价格和宏观经济周期相关。",
    "0.399997": "中证白酒指数由白酒行业龙头组成，具有消费防御属性和品牌护城河。",
    "90.BK0438": "食品饮料板块指数覆盖白酒、乳制品、调味品等食品饮料细分行业。",
    "1.000036": "上证消费指数由沪市主要消费行业公司组成，反映沪市消费板块表现。",
    "90.BK0450": "家用电器板块指数涵盖白电、黑电、小家电等家电产业链企业。",
    "2.H50047": "沪港深消费指数覆盖A股和港股主要消费行业公司，反映两岸三地消费板块表现。",
    "0.399971": "中证传媒指数涵盖影视、游戏、广告、出版等文化传媒产业。",
    "1.000949": "中证农业指数覆盖种植业、畜牧业、农产品加工等农业产业链。",
    "0.159865": "养殖ETF跟踪指数聚焦畜禽养殖产业链，与猪周期密切相关。",
    "100.NDX": "纳斯达克100指数由美国纳斯达克市场100只非金融类大盘股组成，以科技股为主导。",
    "100.N225": "日经225指数是日本东京股市最具代表性的股价指数，反映日本经济整体表现。",
    "124.HSTECH": "恒生科技指数由港股科技主题公司组成，涵盖互联网、金融科技、云计算等领域。",
    "1.513730": "东南亚科技指数覆盖东南亚地区科技相关企业，布局新兴市场投资机会。",
    "100.VNINDEX": "越南胡志明指数是越南股市主要基准指数，代表新兴市场投资机会。",
    "100.SENSEX": "印度孟买SENSEX指数是印度股市历史最悠久的指数，反映印度经济发展状况。",
    "90.BK0547": "黄金板块指数覆盖黄金开采、冶炼等企业，与黄金价格高度相关，具有避险属性。",
    "102.CL00Y": "NYMEX原油指数跟踪纽约商品交易所原油期货价格，与全球经济周期和地缘政治密切相关。",
    "0.399986": "中证银行指数由商业银行组成，具有高股息、低估值、稳健经营的特征。",
}


def get_predefined_description(index_code: str) -> Optional[str]:
    """
    获取预定义的板块描述
    
    Args:
        index_code: 指数代码
        
    Returns:
        预定义描述，不存在返回None
    """
    return PREDEFINED_DESCRIPTIONS.get(index_code)


def initialize_descriptions(config_file: str, zs_all: Dict) -> Dict[str, str]:
    """
    初始化板块描述，优先使用预定义数据，若不存在则生成默认描述
    
    Args:
        config_file: 配置文件路径
        zs_all: 板块配置字典
        
    Returns:
        描述字典
    """
    # 首先加载配置文件中的描述
    descriptions = load_descriptions_from_config(config_file)
    
    # 遍历所有板块，补充缺失的描述
    for index_code, info in zs_all.items():
        if index_code not in descriptions or not descriptions[index_code]:
            # 优先使用预定义描述
            predefined = get_predefined_description(index_code)
            if predefined:
                descriptions[index_code] = predefined
            else:
                # 生成默认描述
                index_name = info[0] if isinstance(info, list) else str(info)
                descriptions[index_code] = generate_default_description(index_code, index_name)
    
    # 保存到配置文件
    save_descriptions_to_config(config_file, descriptions)
    
    return descriptions


if __name__ == '__main__':
    # 测试代码
    test_zs = {
        "1.000698": ["科创100", "019861"],
        "1.000001": ["上证指数", "000001"],
        "90.BK1036": ["半导体", "020629"],
    }
    
    print("测试预定义描述获取:")
    for code in test_zs:
        desc = get_predefined_description(code)
        print(f"{code}: {desc or '无预定义描述'}")
    
    print("\n测试初始化描述:")
    descs = initialize_descriptions('data/test_zs_fund_online_ui.json', test_zs)
    for code, desc in descs.items():
        print(f"{code}: {desc[:50]}...")

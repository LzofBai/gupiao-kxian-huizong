from chardet import detect  # 分析字符集格式 pip install chardet
from json import loads as json_loads
from os.path import splitext
from sys import argv as sys_argv, _getframe, exit as sys_exit
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'log' not in globals():
    from utils.Logger import Logger  # 记录日志文档

    log = Logger(f'logs/{os.path.basename(splitext(__file__)[0])}.log', level='error').logger


def getcontext(context_file_name):
    if context_file_name[0] == '"' == context_file_name[-1]:
        context_file_name = context_file_name[1:-1]
    context = open(context_file_name, 'rb')  # 只读方式打开文本文件
    data = context.read()  # 读出全部内容
    char_code = detect(data)['encoding']  # 识别编码格式
    try:
        data = data.decode(char_code)  # 以识别的编码格式尝试转换
        log.debug(f'预估文本文件[{context_file_name}]的编码格式为[{char_code}]')
    except:
        data = data.decode('gbk', 'ignore')
        log.debug(f'将文本文件[{context_file_name}]的编码格式强制转到gbk')
    context.close()  # 关闭文本文件
    return data  # 返回文本内容


def udl2dict(udl_file=f'{splitext(__file__)[0]}.udl'):
    '''
    返回key是Provider/Password/Persist Security Info/User ID/Initial Catalog/Data Source的字典
    :return: dict
    '''
    udl = getcontext(udl_file)
    if udl:
        udl = udl.split('\n')[2]
    else:
        log.logger.error(f"连接配置信息可能不正确,请双击该文档进行配置[{udl_file}]")
        sys_exit(_getframe().f_lineno)
    lst = udl.split('\r')[0].split(';')
    dic = dict()
    for l in lst:
        s = l.split('=', 1)
        dic[s[0]] = s[1]
    return dic


def json_file2dataframe(context_file_name):
    import pandas as pd
    import json

    # 假设json_str是您的JSON字符串
    json_str = getcontext(context_file_name=context_file_name)

    # 将JSON字符串转换为Python对象
    data = json.loads(json_str)

    # 创建DataFrame
    df = pd.DataFrame(data)
    return df


def is_num(s):
    try:
        if float(s).is_integer():
            try:
                return True  # int(s)   # -1000000007
            except:
                return True  # float(s)  # -9e9
        else:
            return True  # float(s)     # -5.5e5 | nan | -inf
    except:
        return False


def try2float(s, default=None):
    if is_num(s):
        return float(s)
    return default


def try2int(s, default=None):
    if is_num(s):
        return int(s)
    return default


def file2json(filename):
    str_config = getcontext(filename)
    try:
        return json_loads(str_config)
    except Exception as e:
        log.error(f'配置文件{filename}内容或编码格式有误,请检查并重新保存后再试')
        exit(_getframe().f_lineno)


if __name__ == '__main__':
    if 'log' not in globals():
        from Logger import Logger  # 记录日志文档
        log = Logger(f'{splitext(__file__)[0]}.log', level='debug').logger
    # if len(sys_argv) == 2:
    #     filename = sys_argv[1]
    #     json_file2dataframe(filename)

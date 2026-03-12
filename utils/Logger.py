import logging
from logging.handlers import RotatingFileHandler
import os


class Logger:
    """
    自定义日志记录器类
    用于创建和配置日志记录功能
    """
    
    def __init__(self, log_file, level='info', max_bytes=10485760, backup_count=5):
        """
        初始化日志记录器
        
        :param log_file: 日志文件路径
        :param level: 日志级别 (debug, info, warning, error, critical)
        :param max_bytes: 单个日志文件最大字节数,默认10MB
        :param backup_count: 保留的备份文件数量
        """
        self.log_file = log_file
        self.level = level.upper()
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # 创建日志记录器
        self.logger = logging.getLogger(log_file)
        self.logger.setLevel(getattr(logging, self.level))
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 创建文件handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, self.level))
            
            # 创建控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.level))
            
            # 设置日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加handler到logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """记录DEBUG级别日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录INFO级别日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录WARNING级别日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录ERROR级别日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录CRITICAL级别日志"""
        self.logger.critical(message)


if __name__ == '__main__':
    # 测试示例
    log = Logger('test.log', level='debug').logger
    log.debug('这是一条调试信息')
    log.info('这是一条普通信息')
    log.warning('这是一条警告信息')
    log.error('这是一条错误信息')
    log.critical('这是一条严重错误信息')

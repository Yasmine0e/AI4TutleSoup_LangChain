"""
日志工具模块
"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

def get_logger(
    module_name: Optional[str] = "default",
    level: int = logging.INFO,
    stream = sys.stdout
) -> logging.Logger:
    """
    获取配置好的 logger 实例
    
    Args:
        module_name: 模块名，默认使用 __name__
        level: 日志等级，默认 INFO
        stream: 输出流，默认 sys.stdout
        
    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    # 使用传入的模块名
    logger = logging.getLogger(module_name)
    
    # 设置日志等级
    logger.setLevel(level)
    
    # 如果 logger 已经有 handler，直接返回
    if logger.handlers:
        return logger
        
    # 创建控制台处理器
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到 logger
    logger.addHandler(console_handler)
    
    # TODO: 文件日志处理器
    # 后续如需添加文件日志，可以在这里添加 FileHandler
    # file_handler = logging.FileHandler('app.log')
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
        
    return logger

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则只输出到控制台
        level: 日志级别
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建格式化器  
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 创建循环文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 使用示例
if __name__ == '__main__':
    # 基本使用
    logger = get_logger()
    logger.info('这是一条信息')
    logger.warning('这是一条警告')
    
    # 自定义模块名
    custom_logger = get_logger('custom_module')
    custom_logger.info('来自自定义模块的信息')
    
    # 自定义日志等级
    debug_logger = get_logger(level=logging.DEBUG)
    debug_logger.debug('这是一条调试信息')
    
    # 验证重复调用不会重复添加 handler
    same_logger = get_logger('custom_module')
    same_logger.info('这条信息只会输出一次') 
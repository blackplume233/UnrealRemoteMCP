import logging
import unreal

class UnrealLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        if record.levelno >= logging.ERROR:
            unreal.log_error(log_entry)
        elif record.levelno >= logging.WARNING:
            unreal.log_warning(log_entry)
        else:
            unreal.log(log_entry)
            
def setup_logging(name : str | None = None) -> None:
    # 获取根 Logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # 设置日志级别

    # 创建自定义的 Unreal 日志处理器
    unreal_handler = UnrealLogHandler()
    unreal_handler.setLevel(logging.INFO)  # 设置处理器的日志级别

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    unreal_handler.setFormatter(formatter)

    # 添加处理器到 Logger
    logger.addHandler(unreal_handler)
import logging

from typing import Optional
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


ue_log_capture = unreal.PythonLogCaptureContext()
capture_count = 0
class LogCaptureScope:
    def __enter__(self):
        global capture_count
        if capture_count == 0:
            ue_log_capture.clear()
            ue_log_capture.begin_capture()
        capture_count += 1
        return ue_log_capture
    def __exit__(self, exc_type: Optional[type], exc_value: Optional[BaseException], traceback: Optional[object]) -> bool:
        global capture_count
        capture_count -= 1
        if capture_count == 0:
            ue_log_capture.end()
        # Do not suppress exceptions
        return False
    

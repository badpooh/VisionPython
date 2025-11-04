from demo_test.demo_process import DemoTest
from function.func_modbus import ConnectionManager
import threading


class Canceled(RuntimeError):
    pass

class CancelToken:
    def __init__(self):
        self._evt = threading.Event()
    def cancel(self):
        self._evt.set()
    def is_canceled(self) -> bool:
        return self._evt.is_set()
    def wait(self, timeout: float) -> bool:
        # True면 취소 신호 감지
        return self._evt.wait(timeout)

class TestProcess:
    
    def __init__(self, test_mode: DemoTest, connect_manager: ConnectionManager, score_callback=None, stop_callback=None):
        self.score_callback = score_callback
        self.stop_callback = stop_callback 
        self.test_mode = test_mode
        self.connect_manager = connect_manager
    
    def test_by_name(self, test_name, base_save_path, test_mode, search_pattern):
        
        if test_mode == "Demo" or "NoLoad":
            if test_name == "tm_balance":
                self.test_mode.meter_test_mode_balance(base_save_path, search_pattern)
            else:
                print(f"Unknown test name: {test_name}")
        else:
            print("demo_test_by_name Error")
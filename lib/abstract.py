from abc import ABC, abstractmethod

class RandomProcess(ABC):
    
    @abstractmethod
    def generate_ticks(self):
        return NotImplemented
    
    @abstractmethod
    def generate_random_process(self, state, hurst):
        return NotImplemented
    
    @abstractmethod
    def make_daily(self, hours=5, mins=2):
        return NotImplemented
    
    @abstractmethod
    def calculate_K(self, K_array):
        return NotImplemented
    
    @abstractmethod
    def make_days(self, day_num):
        return NotImplemented
    
    @abstractmethod
    def map_label(self, df):
        return NotImplemented
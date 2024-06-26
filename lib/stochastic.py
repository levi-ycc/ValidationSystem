import fbm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lib.abstract import RandomProcess

class MarkovChain(object):
    
    def __call__(self, state_num=10):
        tran_prob = np.zeros([state_num, state_num])
        for m in range(state_num):
            rand_num = np.random.rand(state_num)
            total = rand_num.sum()
            tran_prob[m] = [n/total for n in rand_num]
        return tran_prob
        
class HurstExponent(object):
    
    def __call__(self, state_num=10, floor=30, ceiling=70):
        interval = list(range(floor, ceiling))
        bm_per_episode = np.random.choice(interval, state_num)
        bm_per_episode = bm_per_episode / 100
        return bm_per_episode

class ConnectedBrownianMotion(RandomProcess):
    
    def __init__(self, state_num=10, tick_length=1024):
        self.state_num = state_num
        self.tick_length = tick_length
        self.transprob_array = MarkovChain.__call__(self.state_num)
        self.last_val = 0
        
    def generate_ticks(self):
        self.hurst_array = HurstExponent.__call__(self.state_num)
        self.fbm_array = np.array([])
        rand_num = np.random.rand(self.state_num)
        state_switch = np.random.choice(list(range(10)), 10)
        
        total = rand_num.sum()
        self.each_len = [int(n/total * self.tick_length) for n in rand_num]
        
        self.hurst_list = []
        for state in range(self.state_num):
            hurst = self.hurst_array[state_switch[state]]
            tseries = self.generate_random_process(state, hurst)
#             tseries = fbm.FBM(n=each_len[state], hurst=hurst, 
#                                    length=1, method='daviesharte').fbm()
            tseries = tseries + self.last_val
            self.fbm_array = np.append(self.fbm_array, tseries[1:])
            self.hurst_list = self.hurst_list + [hurst]*self.each_len[state]
            self.last_val = self.fbm_array[-1]
        return self.fbm_array
    
    def generate_random_process(self, state, hurst):
        return fbm.FBM(n=self.each_len[state], hurst=hurst, 
                                   length=1, method='daviesharte').fbm()
    
    def make_daily(self, hours=5, mins=2):
        groups = hours * (60 / mins)
        K_array = np.asarray(np.array_split(self.fbm_array, groups))
        self.hurst_array = np.asarray(np.array_split(self.hurst_list, groups))
        out_list = self.calculate_K(K_array)
        df = pd.DataFrame(out_list)
        df['Date'] = range(df.shape[0])
        labels = self.map_label(df)
        df['label'] = labels
        return df.copy()
        
    def calculate_K(self, K_array):
        out_list = []
        for k in range(K_array.shape[0]):
            H = K_array[k].max()
            L = K_array[k].min()
            O = K_array[k][0]
            C = K_array[k][-1]
            hurst = self.hurst_array[k][0]
            out_list.append({'O':O, 'H':H, 'L':L, 'C':C, 'Hurst': hurst})
        return out_list
    
    def make_days(self, day_num):
        for d in range(day_num):
            self.generate_ticks()
            tmp_df = self.make_daily()
            yield tmp_df
    
    def map_label(self, df):
        map_array = []
        for i in df['Hurst']:
            if i < 0.5:
                map_array.append('neg_cor')
            elif i > 0.5:
                map_array.append('pos_cor')
            else:
                map_array.append('bm')
        return map_array
            
        
class LocalVolModel(ConnectedBrownianMotion):
    def __init__(self, state_num=10, tick_length=1024):
        super().__init__(state_num, tick_length)
        
    def set_values(self, S0, r, q, sigma):     
        self.periods = self.tick_length
        self.S0 = S0
        self.r = r
        self.q = q
        self.sigma = sigma
        
    def generate_random_process(self, state, hurst):
        return self.generate_lvm()
    
    def generate_lvm(self):
        w = [np.random.normal(0, 1/self.periods) for a in range(self.periods)]
        t=1/self.periods
        randw = [(self.r-self.q) * t + self.sigma*w[i] for i in range(len(w))]
        ds = self.S0*randw
        df = pd.DataFrame(ds, columns=['price'])
        df = pd.concat([pd.DataFrame([self.S0], columns=['price']), df], ignore_index=True)
        df['price'].cumsum().values
        return df['price'].cumsum().values
    
    def generate_ticks(self):        
        tseries = self.generate_random_process(None, None)
        self.fbm_array = tseries
        return self.fbm_array
    
    def make_daily(self, hours=5, mins=2):
        groups = hours * (60 / mins)
        K_array = np.asarray(np.array_split(self.fbm_array, groups))
        out_list = self.calculate_K(K_array)
        df = pd.DataFrame(out_list)
        df['Date'] = range(df.shape[0])
        return df.copy()
    
    def calculate_K(self, K_array):
        out_list = []
        for k in range(K_array.shape[0]):
            H = K_array[k].max()
            L = K_array[k].min()
            O = K_array[k][0]
            C = K_array[k][-1]
            out_list.append({'O':O, 'H':H, 'L':L, 'C':C})
        return out_list

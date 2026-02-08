"""
ETH多时间框架实时监控交易系统 v5.1 安卓版
适用于安卓手机的Kivy版本
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.stacklayout import StackLayout
from kivy.metrics import dp

import requests
import threading
import time
from datetime import datetime
import random
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

# 设置窗口大小适合手机
Window.size = (360, 640)

class ETHTraderApp(App):
    def build(self):
        self.title = "ETH交易助手 v5.1"
        self.root_layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))
        
        # 设置背景颜色
        with self.root_layout.canvas.before:
            Color(0.1, 0.1, 0.2, 1)  # 深蓝色背景
            self.rect = Rectangle(size=Window.size, pos=self.root_layout.pos)
        
        # 创建顶部标题栏
        header = BoxLayout(size_hint=(1, 0.1), orientation='horizontal')
        header.add_widget(Label(text='📊 ETH智能交易', font_size='20sp', bold=True, color=(1, 1, 1, 1)))
        header.add_widget(Label(text='v5.1 安卓版', font_size='12sp', color=(0.7, 0.7, 1, 1)))
        self.root_layout.add_widget(header)
        
        # 创建标签页
        self.tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 0.9))
        
        # 标签1: 实时监控
        tab1 = TabbedPanelItem(text='📈 实时监控')
        self.setup_monitoring_tab(tab1)
        self.tabs.add_widget(tab1)
        
        # 标签2: 交易参数
        tab2 = TabbedPanelItem(text='⚙️ 交易设置')
        self.setup_settings_tab(tab2)
        self.tabs.add_widget(tab2)
        
        # 标签3: 交易计划
        tab3 = TabbedPanelItem(text='📋 交易计划')
        self.setup_plan_tab(tab3)
        self.tabs.add_widget(tab3)
        
        # 标签4: 日志
        tab4 = TabbedPanelItem(text='📝 日志')
        self.setup_log_tab(tab4)
        self.tabs.add_widget(tab4)
        
        self.root_layout.add_widget(self.tabs)
        
        # 初始化变量
        self.current_price = 0
        self.price_change = 0
        self.monitoring = False
        self.api_working = False
        self.base_url = "https://api.gateio.ws/api/v4"
        
        # 交易参数默认值
        self.trade_params = {
            'capital': '5000',
            'leverage': '10',
            'risk_percent': '1',
            'stop_distance': '2.0',
            'risk_reward': '1.5',
            'auto_plan_threshold': '85'
        }
        
        # 数据存储
        self.price_histories = {
            "1m": [], "5m": [], "15m": [], "1h": [], "4h": []
        }
        
        # 启动初始化
        Clock.schedule_once(self.initialize_app, 1)
        
        return self.root_layout
    
    def setup_monitoring_tab(self, tab):
        """设置监控标签页"""
        layout = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # 价格显示区域
        price_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(100))
        price_box.add_widget(Label(text='ETH当前价格', font_size='16sp', color=(1, 1, 1, 1)))
        
        self.price_label = Label(text='$0.00', font_size='28sp', bold=True, color=(0, 1, 1, 1))
        price_box.add_widget(self.price_label)
        
        self.change_label = Label(text='0.00%', font_size='16sp', color=(0.5, 1, 0.5, 1))
        price_box.add_widget(self.change_label)
        
        content.add_widget(price_box)
        
        # 控制按钮
        btn_box = BoxLayout(size_hint=(1, None), height=dp(40))
        self.start_btn = Button(text='▶️ 开始监控', on_press=self.start_monitoring)
        self.stop_btn = Button(text='⏸️ 暂停', on_press=self.stop_monitoring)
        self.refresh_btn = Button(text='🔄 刷新', on_press=self.manual_refresh)
        
        btn_box.add_widget(self.start_btn)
        btn_box.add_widget(self.stop_btn)
        btn_box.add_widget(self.refresh_btn)
        content.add_widget(btn_box)
        
        # 时间框架指标
        content.add_widget(Label(text='📊 多时间框架信号', font_size='16sp', color=(1, 1, 1, 1)))
        
        self.timeframe_layout = GridLayout(cols=3, spacing=dp(5), size_hint_y=None)
        self.timeframe_layout.bind(minimum_height=self.timeframe_layout.setter('height'))
        
        timeframes = ["1分钟", "5分钟", "15分钟", "1小时", "4小时"]
        self.signal_labels = {}
        
        for tf in timeframes:
            self.timeframe_layout.add_widget(Label(text=tf, font_size='12sp', color=(1, 1, 1, 1)))
            self.signal_labels[f"{tf}_price"] = Label(text='--', font_size='12sp', color=(1, 1, 1, 1))
            self.timeframe_layout.add_widget(self.signal_labels[f"{tf}_price"])
            
            self.signal_labels[f"{tf}_signal"] = Label(text='等待', font_size='12sp', color=(0.8, 0.8, 0.8, 1))
            self.timeframe_layout.add_widget(self.signal_labels[f"{tf}_signal"])
        
        content.add_widget(self.timeframe_layout)
        
        # 总体信号
        content.add_widget(Label(text='🤖 系统建议', font_size='16sp', color=(1, 1, 1, 1)))
        
        self.direction_label = Label(text='等待分析...', font_size='18sp', bold=True, color=(1, 1, 0, 1))
        content.add_widget(self.direction_label)
        
        self.confidence_label = Label(text='置信度: 0%', font_size='14sp', color=(1, 1, 1, 1))
        content.add_widget(self.confidence_label)
        
        self.reason_label = Label(text='正在获取数据...', font_size='12sp', color=(0.8, 0.8, 0.8, 1))
        content.add_widget(self.reason_label)
        
        layout.add_widget(content)
        tab.add_widget(layout)
    
    def setup_settings_tab(self, tab):
        """设置交易参数标签页"""
        layout = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        content.add_widget(Label(text='⚙️ 交易参数设置', font_size='18sp', color=(1, 1, 1, 1)))
        
        # 参数输入框
        params = [
            ("💰 本金 (USDT):", "capital", "5000"),
            ("⚡ 杠杆倍数:", "leverage", "10"),
            ("🛡️ 单笔风险 (%):", "risk_percent", "1"),
            ("📉 止损距离 (%):", "stop_distance", "2.0"),
            ("📈 盈亏比:", "risk_reward", "1.5"),
            ("🔔 自动计划阈值 (%):", "auto_plan_threshold", "85"),
        ]
        
        self.param_inputs = {}
        
        for label_text, key, default in params:
            param_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50))
            param_box.add_widget(Label(text=label_text, font_size='14sp', color=(1, 1, 1, 1), size_hint_x=0.6))
            
            input_field = TextInput(text=default, multiline=False, font_size='14sp', 
                                   size_hint_x=0.4, background_color=(0.2, 0.2, 0.3, 1),
                                   foreground_color=(1, 1, 1, 1))
            input_field.bind(text=self.on_param_change)
            param_box.add_widget(input_field)
            self.param_inputs[key] = input_field
            
            content.add_widget(param_box)
        
        # 自动刷新开关
        auto_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50))
        auto_box.add_widget(Label(text='🔄 自动刷新:', font_size='14sp', color=(1, 1, 1, 1)))
        
        self.auto_switch = Switch(active=False)
        self.auto_switch.bind(active=self.toggle_auto_refresh)
        auto_box.add_widget(self.auto_switch)
        
        content.add_widget(auto_box)
        
        # 刷新频率选择
        freq_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50))
        freq_box.add_widget(Label(text='刷新频率:', font_size='14sp', color=(1, 1, 1, 1)))
        
        self.freq_spinner = Spinner(
            text='60秒',
            values=('30秒', '60秒', '2分钟', '5分钟'),
            size_hint=(None, None),
            size=(dp(100), dp(44))
        )
        freq_box.add_widget(self.freq_spinner)
        content.add_widget(freq_box)
        
        # 测试按钮
        test_btn = Button(text='🔊 测试警报', on_press=self.test_alarm, 
                         size_hint=(1, None), height=dp(50))
        content.add_widget(test_btn)
        
        # 状态显示
        self.status_label = Label(text='🔄 正在初始化...', font_size='12sp', color=(1, 1, 0, 1))
        content.add_widget(self.status_label)
        
        layout.add_widget(content)
        tab.add_widget(layout)
    
    def setup_plan_tab(self, tab):
        """设置交易计划标签页"""
        layout = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # 生成计划按钮
        plan_btn = Button(text='📋 生成交易计划', on_press=self.generate_plan,
                         size_hint=(1, 0.1))
        layout.add_widget(plan_btn)
        
        copy_btn = Button(text='📋 复制计划', on_press=self.copy_plan,
                         size_hint=(1, 0.1))
        layout.add_widget(copy_btn)
        
        # 计划显示区域
        self.plan_text = TextInput(text='请先生成交易计划...', readonly=True,
                                  font_size='12sp', background_color=(0.1, 0.1, 0.15, 1),
                                  foreground_color=(1, 1, 1, 1))
        layout.add_widget(self.plan_text)
        
        tab.add_widget(layout)
    
    def setup_log_tab(self, tab):
        """设置日志标签页"""
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # 控制按钮
        log_btn_box = BoxLayout(size_hint=(1, 0.1))
        clear_btn = Button(text='🗑️ 清空日志', on_press=self.clear_log)
        export_btn = Button(text='📤 导出日志', on_press=self.export_log)
        
        log_btn_box.add_widget(clear_btn)
        log_btn_box.add_widget(export_btn)
        layout.add_widget(log_btn_box)
        
        # 日志显示区域
        self.log_text = TextInput(text='ETH交易助手 v5.1 安卓版 启动\n', readonly=True,
                                 font_size='12sp', background_color=(0.1, 0.1, 0.15, 1),
                                 foreground_color=(0.9, 0.9, 0.9, 1))
        layout.add_widget(self.log_text)
        
        tab.add_widget(layout)
    
    def on_param_change(self, instance, value):
        """参数改变时的处理"""
        param_name = None
        for key, widget in self.param_inputs.items():
            if widget == instance:
                param_name = key
                break
        
        if param_name and value:
            self.trade_params[param_name] = value
            self.log_message(f"参数更新: {param_name} = {value}")
    
    def initialize_app(self, dt):
        """初始化应用程序"""
        self.log_message("🎮 ETH交易助手 v5.1 安卓版启动")
        self.log_message("=" * 40)
        
        # 测试API连接
        threading.Thread(target=self.test_api).start()
        
        # 获取初始数据
        threading.Thread(target=self.initial_data_fetch).start()
    
    def test_api(self):
        """测试API连接"""
        try:
            url = f"{self.base_url}/spot/tickers"
            params = {"currency_pair": "ETH_USDT"}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                self.api_working = True
                self.log_message("✅ API连接成功")
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '✅ API连接成功'), 0)
            else:
                self.api_working = False
                self.log_message("❌ API连接失败")
        except Exception as e:
            self.log_message(f"❌ API测试错误: {str(e)}")
            self.api_working = False
    
    def initial_data_fetch(self):
        """获取初始数据"""
        # 获取实时价格
        price_data = self.get_real_time_price()
        if price_data:
            Clock.schedule_once(lambda dt: self.update_price_display(price_data['price'], price_data['change']), 0)
            self.log_message(f"✅ 价格获取: ${price_data['price']:.2f}")
        
        # 获取历史数据
        self.fetch_history_data()
    
    def get_real_time_price(self):
        """获取实时价格"""
        try:
            url = f"{self.base_url}/spot/tickers"
            params = {"currency_pair": "ETH_USDT"}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                tickers = response.json()
                if tickers and len(tickers) > 0:
                    ticker = tickers[0]
                    
                    price = float(ticker["last"])
                    change_percent = float(ticker["change_percentage"])
                    
                    return {"price": price, "change": change_percent}
            
            return None
            
        except Exception as e:
            self.log_message(f"价格获取错误: {str(e)}")
            return None
    
    def fetch_history_data(self):
        """获取历史数据"""
        timeframes = {
            "1m": {"interval": "1m", "limit": 100},
            "5m": {"interval": "5m", "limit": 100},
            "15m": {"interval": "15m", "limit": 100},
            "1h": {"interval": "1h", "limit": 100},
            "4h": {"interval": "4h", "limit": 100}
        }
        
        for tf_key, params in timeframes.items():
            try:
                url = f"{self.base_url}/spot/candlesticks"
                
                params_dict = {
                    "currency_pair": "ETH_USDT",
                    "interval": params["interval"],
                    "limit": params["limit"]
                }
                
                response = requests.get(url, params=params_dict, timeout=10)
                
                if response.status_code == 200:
                    candles = response.json()
                    
                    if candles and len(candles) > 0:
                        candles.sort(key=lambda x: float(x[0]))
                        prices = [float(candle[2]) for candle in candles]
                        
                        if prices:
                            self.price_histories[tf_key] = prices
                            
                            tf_name = {"1m": "1分钟", "5m": "5分钟", "15m": "15分钟",
                                      "1h": "1小时", "4h": "4小时"}[tf_key]
                            self.log_message(f"✅ {tf_name}数据: {len(prices)}条")
            except Exception as e:
                self.log_message(f"❌ {tf_key}数据错误: {str(e)}")
    
    def calculate_ema(self, prices, period):
        """计算指数移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        prices_array = np.array(prices[-period*3:])
        multiplier = 2 / (period + 1)
        
        sma = np.mean(prices_array[:period])
        ema = sma
        
        for price in prices_array[period:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)
    
    def calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        seed = deltas[:period]
        
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100
        
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def analyze_timeframe(self, tf_key, tf_name):
        """分析单个时间框架"""
        prices = self.price_histories[tf_key]
        
        if len(prices) < 25:
            return {
                "price": prices[-1] if prices else 0,
                "signal": "等待",
                "color": (0.8, 0.8, 0.8, 1),
                "score": 0
            }
        
        current_price = prices[-1]
        
        # 计算EMA
        ema7 = self.calculate_ema(prices, 7)
        ema25 = self.calculate_ema(prices, 25)
        
        # 计算RSI
        rsi = self.calculate_rsi(prices, 14)
        
        # 计算信号分数
        score = 0
        
        # EMA排列
        if current_price > ema7 > ema25:
            score += 2
        elif current_price < ema7 < ema25:
            score -= 2
        
        # RSI信号
        if rsi > 70:
            score -= 1.5
        elif rsi < 30:
            score += 1.5
        
        # 判断信号
        if score >= 1.5:
            signal = "强烈看多"
            color = (0, 1, 0, 1)  # 绿色
        elif score >= 0.5:
            signal = "看多"
            color = (0.5, 1, 0.5, 1)  # 浅绿色
        elif score <= -1.5:
            signal = "强烈看空"
            color = (1, 0, 0, 1)  # 红色
        elif score <= -0.5:
            signal = "看空"
            color = (1, 0.5, 0.5, 1)  # 浅红色
        else:
            signal = "中性"
            color = (0.8, 0.8, 0.8, 1)  # 灰色
        
        return {
            "price": current_price,
            "signal": signal,
            "color": color,
            "score": score,
            "rsi": rsi
        }
    
    def perform_analysis(self):
        """执行分析"""
        try:
            # 更新价格
            price_data = self.get_real_time_price()
            if price_data:
                Clock.schedule_once(lambda dt: self.update_price_display(
                    price_data['price'], price_data['change']), 0)
            
            # 分析每个时间框架
            timeframe_map = {
                "1m": "1分钟",
                "5m": "5分钟", 
                "15m": "15分钟",
                "1h": "1小时",
                "4h": "4小时"
            }
            
            total_score = 0
            timeframe_count = 0
            signals_summary = {"看多": 0, "看空": 0, "中性": 0}
            
            for tf_key, tf_name in timeframe_map.items():
                if len(self.price_histories[tf_key]) >= 25:
                    result = self.analyze_timeframe(tf_key, tf_name)
                    
                    # 更新显示
                    Clock.schedule_once(lambda dt, r=result, tn=tf_name: 
                                       self.update_timeframe_display(tn, r), 0)
                    
                    signal_type = result["signal"]
                    if "看多" in signal_type:
                        signals_summary["看多"] += 1
                    elif "看空" in signal_type:
                        signals_summary["看空"] += 1
                    else:
                        signals_summary["中性"] += 1
                    
                    total_score += result["score"]
                    timeframe_count += 1
            
            # 计算总体建议
            if timeframe_count > 0:
                avg_score = total_score / timeframe_count
                
                if avg_score > 1.5:
                    direction = "强烈建议做多"
                    strength = "强"
                    direction_color = (0, 1, 0, 1)
                    confidence = min(95, 75 + avg_score * 10)
                elif avg_score > 0.8:
                    direction = "建议做多"
                    strength = "中"
                    direction_color = (0.5, 1, 0.5, 1)
                    confidence = min(85, 65 + avg_score * 10)
                elif avg_score < -1.5:
                    direction = "强烈建议做空"
                    strength = "强"
                    direction_color = (1, 0, 0, 1)
                    confidence = min(95, 75 + abs(avg_score) * 10)
                elif avg_score < -0.8:
                    direction = "建议做空"
                    strength = "中"
                    direction_color = (1, 0.5, 0.5, 1)
                    confidence = min(85, 65 + abs(avg_score) * 10)
                else:
                    direction = "建议观望"
                    strength = "弱"
                    direction_color = (0.8, 0.8, 0.8, 1)
                    confidence = 40
                
                # 更新显示
                Clock.schedule_once(lambda dt: setattr(self.direction_label, 'text', direction), 0)
                Clock.schedule_once(lambda dt: setattr(self.direction_label, 'color', direction_color), 0)
                Clock.schedule_once(lambda dt: setattr(self.confidence_label, 'text', f'置信度: {confidence:.0f}%'), 0)
                
                reason_text = f"看多:{signals_summary['看多']} 看空:{signals_summary['看空']} 中性:{signals_summary['中性']}"
                Clock.schedule_once(lambda dt: setattr(self.reason_label, 'text', reason_text), 0)
                
                # 记录日志
                log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] {direction} | 置信度: {confidence:.0f}%"
                self.log_message(log_msg)
                
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'✅ 分析完成 - {direction.split("建议")[-1]}'), 0)
            
        except Exception as e:
            self.log_message(f"分析错误: {str(e)}")
    
    def update_price_display(self, price, change):
        """更新价格显示"""
        self.current_price = price
        self.price_change = change
        
        self.price_label.text = f"${price:.2f}"
        
        change_text = f"{change:+.2f}%"
        self.change_label.text = change_text
        
        if change > 0:
            self.change_label.color = (0, 1, 0, 1)
        elif change < 0:
            self.change_label.color = (1, 0, 0, 1)
        else:
            self.change_label.color = (0.8, 0.8, 0.8, 1)
    
    def update_timeframe_display(self, tf_name, result):
        """更新时间框架显示"""
        self.signal_labels[f"{tf_name}_price"].text = f"${result['price']:.2f}"
        self.signal_labels[f"{tf_name}_signal"].text = result['signal']
        self.signal_labels[f"{tf_name}_signal"].color = result['color']
    
    def start_monitoring(self, instance):
        """开始监控"""
        if not self.monitoring:
            self.monitoring = True
            self.start_btn.disabled = True
            self.stop_btn.disabled = False
            
            self.log_message("✅ 监控已启动")
            
            # 启动监控循环
            threading.Thread(target=self.monitor_loop).start()
    
    def stop_monitoring(self, instance):
        """停止监控"""
        self.monitoring = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.log_message("⏸️ 监控已暂停")
    
    def monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            self.perform_analysis()
            
            # 获取频率设置
            freq_text = self.freq_spinner.text
            if freq_text == '30秒':
                sleep_time = 30
            elif freq_text == '60秒':
                sleep_time = 60
            elif freq_text == '2分钟':
                sleep_time = 120
            elif freq_text == '5分钟':
                sleep_time = 300
            else:
                sleep_time = 60
            
            time.sleep(sleep_time)
    
    def manual_refresh(self, instance):
        """手动刷新"""
        self.log_message("🔄 手动刷新数据...")
        threading.Thread(target=self.perform_analysis).start()
    
    def toggle_auto_refresh(self, instance, value):
        """切换自动刷新"""
        if value:
            self.log_message("✅ 自动刷新已启用")
        else:
            self.log_message("⏸️ 自动刷新已停止")
    
    def generate_plan(self, instance):
        """生成交易计划"""
        try:
            if self.current_price <= 0:
                self.show_popup("提示", "请先获取价格数据")
                return
            
            direction = self.direction_label.text
            confidence_text = self.confidence_label.text.replace('置信度: ', '').replace('%', '')
            confidence = float(confidence_text) if confidence_text.replace('.', '').isdigit() else 0
            
            if "观望" in direction or confidence < 50:
                self.plan_text.text = "【⚠️ 交易建议】\n当前信号不明确，不建议交易。\n建议等待更强信号出现。"
                return
            
            # 生成交易计划
            plan = self.create_trade_plan(direction, confidence, self.current_price)
            self.plan_text.text = plan
            self.log_message("📋 交易计划已生成")
            
        except Exception as e:
            self.show_popup("错误", f"生成计划错误: {str(e)}")
    
    def create_trade_plan(self, direction, confidence, price):
        """创建交易计划"""
        try:
            # 获取参数
            stop_distance = float(self.trade_params.get('stop_distance', 2.0))
            risk_reward = float(self.trade_params.get('risk_reward', 1.5))
            capital = float(self.trade_params.get('capital', 5000))
            risk_percent = float(self.trade_params.get('risk_percent', 1))
            
            if "做多" in direction:
                action = "买入做多"
                stop_loss = price * (1 - stop_distance/100)
                take_profit = price * (1 + stop_distance/100 * risk_reward)
            else:
                action = "卖出做空"
                stop_loss = price * (1 + stop_distance/100)
                take_profit = price * (1 - stop_distance/100 * risk_reward)
            
            # 计算仓位
            risk_amount = capital * (risk_percent / 100)
            price_risk = abs(price - stop_loss)
            contract_amount = risk_amount / price_risk if price_risk > 0 else 0
            
            plan = f"""【📋 交易计划】
ETH价格: ${price:.2f}
信号: {direction}
置信度: {confidence:.0f}%

🎯 交易方向: {action}
入场价: ${price:.2f}
止损: ${stop_loss:.2f}
止盈: ${take_profit:.2f}

💰 资金管理
本金: ${capital:.2f}
单笔风险: ${risk_amount:.2f} ({risk_percent}%)
合约数: {contract_amount:.4f} ETH

⏰ 建议持仓: 2-4小时
⚠️ 风险提示: 市场有风险"""
            
            return plan
            
        except Exception as e:
            return f"生成计划错误: {str(e)}"
    
    def copy_plan(self, instance):
        """复制计划"""
        if self.plan_text.text:
            # 在安卓上，我们需要使用剪贴板
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(self.plan_text.text)
                self.show_popup("成功", "交易计划已复制到剪贴板")
                self.log_message("📋 计划已复制")
            except:
                self.show_popup("提示", "复制功能在当前设备上可能不可用")
    
    def clear_log(self, instance):
        """清空日志"""
        self.log_text.text = "日志已清空\n"
        self.log_message("✅ 日志已清空")
    
    def export_log(self, instance):
        """导出日志"""
        self.show_popup("提示", "在安卓设备上，请使用分享功能导出日志")
    
    def test_alarm(self, instance):
        """测试警报"""
        self.log_message("🔊 测试警报（请在安卓设置中允许通知权限）")
        self.show_popup("测试", "警报测试！请检查通知权限")
    
    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        Clock.schedule_once(lambda dt: setattr(self.log_text, 'text', self.log_text.text + log_entry), 0)
    
    def show_popup(self, title, message):
        """显示弹出窗口"""
        content = BoxLayout(orientation='vertical', padding=dp(10))
        content.add_widget(Label(text=message))
        
        btn = Button(text='确定', size_hint=(1, 0.3))
        
        popup = Popup(title=title, content=content,
                     size_hint=(0.8, 0.4))
        
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()

if __name__ == '__main__':
    # Trigger build at: 2026-02-08 17:33

    ETHTraderApp().run()

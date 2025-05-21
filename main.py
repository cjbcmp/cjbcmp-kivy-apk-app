from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
import requests
from datetime import datetime


def safe_float(s):
    try:
        return float(s)
    except:
        return None

def get_stock_data(stock_code):
    url = f"https://qt.gtimg.cn/q={stock_code}"
    try:
        res = requests.get(url, timeout=5)
        raw = res.text
        if "~" not in raw:
            return None
        data = raw.split('~')
        stock_name = data[1]
        yesterday_close = safe_float(data[3])
        current_price = safe_float(data[4])
        buy_prices = data[9], data[11], data[13], data[15], data[17]
        buy_volumes = data[10], data[12], data[14], data[16], data[18]
        sell_prices = data[19], data[21], data[23], data[25], data[27]
        sell_volumes = data[20], data[22], data[24], data[26], data[28]
        return {
            "name": stock_name,
            "yesterday_close": yesterday_close,
            "current_price": current_price,
            "buy": list(zip(buy_prices, buy_volumes)),
            "sell": list(zip(sell_prices, sell_volumes)),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception:
        return None

def get_industry_info(stock_code):
    if stock_code.startswith("sh"):
        secid = f"0.{stock_code[2:]}"
    elif stock_code.startswith("sz"):
        secid = f"1.{stock_code[2:]}"
    else:
        return "未知", None

    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        js = res.json()
        f10 = js.get("data", {}).get("f10", {})
        industry_name = f10.get("HYBK", "未知")
        industry_index = f10.get("HYBKZDF", None)
        if industry_index is not None:
            industry_index = float(industry_index)
        return industry_name, industry_index
    except Exception:
        return "未知", None

def get_index_data():
    codes = {'沪': 'sh000001', '深': 'sz399001', '创': 'sz399006'}
    result = {}
    try:
        res = requests.get(f"https://qt.gtimg.cn/q={','.join(codes.values())}")
        text = res.text.split(';')
        for line in text:
            if '~' in line:
                parts = line.split('~')
                name = parts[1]
                yclose = safe_float(parts[3])
                now = safe_float(parts[4])
                if yclose and now:
                    pct = (now - yclose) / yclose * 100
                    for k, v in codes.items():
                        if v in line:
                            result[k] = pct
        return result
    except:
        return {}

def format_pct(pct):
    if pct is None:
        return "---", "gray"
    pct_str = f"{pct:+.2f}%"
    color = "red" if pct > 0 else ("green" if pct < 0 else "black")
    return pct_str, color


class StockApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        self.code_input = TextInput(text='sz002130', multiline=False, font_size=20, size_hint=(0.4, 1))
        search_btn = Button(text='查询', font_size=20, size_hint=(0.2, 1))
        search_btn.bind(on_press=self.update_data)
        self.pct_label = Label(text='---', font_size=20, size_hint=(0.4, 1), color=(0,0,0,1))

        top_bar.add_widget(self.code_input)
        top_bar.add_widget(search_btn)
        top_bar.add_widget(self.pct_label)

        self.root.add_widget(top_bar)

        self.name_label = Label(text='股票名称', font_size=24)
        self.root.add_widget(self.name_label)

        self.sell_grid = GridLayout(cols=2, spacing=5, size_hint=(1, 0.3))
        self.sell_labels = []
        for _ in range(5):
            left = Label(text='卖x ---', font_size=18)
            right = Label(text='---', font_size=18)
            self.sell_labels.append((left, right))
            self.sell_grid.add_widget(left)
            self.sell_grid.add_widget(right)
        self.root.add_widget(self.sell_grid)

        self.root.add_widget(Label(text="----------", font_size=18, color=(.6,.6,.6,1), size_hint=(1, 0.05)))

        self.buy_grid = GridLayout(cols=2, spacing=5, size_hint=(1, 0.3))
        self.buy_labels = []
        for _ in range(5):
            left = Label(text='买x ---', font_size=18)
            right = Label(text='---', font_size=18)
            self.buy_labels.append((left, right))
            self.buy_grid.add_widget(left)
            self.buy_grid.add_widget(right)
        self.root.add_widget(self.buy_grid)

        self.industry_label = Label(text='行业：---', font_size=18, color=(0.3, 0.3, 1, 1))
        self.time_label = Label(text='更新时间：---', font_size=16)

        self.index_label = Label(text='沪：---  深：---  创：---', font_size=16, color=(0.2, 0.2, 0.2, 1))
        self.root.add_widget(self.index_label)

        self.root.add_widget(self.industry_label)
        self.root.add_widget(self.time_label)

        Clock.schedule_interval(self.update_data, 2)
        return self.root

    def update_data(self, *args):
        code = self.code_input.text.strip()
        data = get_stock_data(code)
        if not data:
            self.name_label.text = "获取失败"
            return

        self.name_label.text = f"{data['name']}（{code}）"
        yclose = data['yesterday_close']
        now = data['current_price']
        if yclose and now:
            pct = (now - yclose) / yclose * 100
            pct_str, pct_color = format_pct(pct)
        else:
            pct_str, pct_color = "---", "gray"
        self.pct_label.text = pct_str
        self.pct_label.color = self.color_map(pct_color)

        for i in range(5):
            idx = 4 - i
            sell_price = safe_float(data['sell'][idx][0])
            sell_vol = data['sell'][idx][1]
            color = self.price_color(sell_price, yclose)
            self.sell_labels[i][0].text = f"卖{idx + 1} {sell_price:.2f}" if sell_price else "卖x ---"
            self.sell_labels[i][0].color = color
            self.sell_labels[i][1].text = f"{sell_vol}" if sell_vol else "---"
            self.sell_labels[i][1].color = color

            buy_price = safe_float(data['buy'][i][0])
            buy_vol = data['buy'][i][1]
            color = self.price_color(buy_price, yclose)
            self.buy_labels[i][0].text = f"买{i + 1} {buy_price:.2f}" if buy_price else "买x ---"
            self.buy_labels[i][0].color = color
            self.buy_labels[i][1].text = f"{buy_vol}" if buy_vol else "---"
            self.buy_labels[i][1].color = color

        self.time_label.text = f"更新时间：{data['time']}"

        # 行业信息
        industry_name, industry_index = get_industry_info(code)
        pct_str, color_str = format_pct(industry_index)
        self.industry_label.text = f"行业：{industry_name}   涨跌幅：{pct_str}"
        self.industry_label.color = self.color_map(color_str)

        # 指数信息
        index_data = get_index_data()
        text_parts = []
        for k in ['沪', '深', '创']:
            pct = index_data.get(k)
            pct_str, _ = format_pct(pct)
            text_parts.append(f"{k}：{pct_str}")
        self.index_label.text = "  ".join(text_parts)

    def price_color(self, price, yesterday):
        if price is None or yesterday is None:
            return (0, 0, 0, 1)
        if price > yesterday:
            return (1, 0, 0, 1)
        elif price < yesterday:
            return (0, 0.6, 0, 1)
        else:
            return (0, 0, 0, 1)

    def color_map(self, name):
        return {
            "red": (1, 0, 0, 1),
            "green": (0, 0.6, 0, 1),
            "gray": (0.5, 0.5, 0.5, 1),
            "black": (0, 0, 0, 1)
        }.get(name, (0, 0, 0, 1))


if __name__ == '__main__':
    StockApp().run()

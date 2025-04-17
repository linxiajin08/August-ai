import tkinter as tk
from tkinter import messagebox
import speech_recognition as sr
import requests
import pyttsx3
import json
import os
import threading

# 初始化语音引擎
engine = pyttsx3.init()

# 初始化语音识别器
r = sr.Recognizer()

# 对话历史记录
conversation_history = []

# 关键词
WAKE_WORD = '特定关键词'

# API 地址
API_URL = 'your_api_url'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('语音助手配置')
        self.geometry('500x600')

        # 网格布局配置
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        
        # 模型 URL 输入框
        self.url_label = tk.Label(self, text='模型 URL:')
        self.url_label.grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.url_entry = tk.Entry(self)
        self.url_entry.insert(0, 'https://api.siliconflow.cn/v1')
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        # API 模型名称输入框
        self.model_label = tk.Label(self, text='API 模型名称:')
        self.model_label.grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.model_entry = tk.Entry(self)
        self.model_entry.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

        # 唤醒词输入框
        self.wake_label = tk.Label(self, text='唤醒词:')
        self.wake_label.grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.wake_entry = tk.Entry(self)
        self.wake_entry.grid(row=2, column=1, padx=10, pady=5, sticky='ew')

        # API密钥输入框
        self.key_label = tk.Label(self, text='API密钥:')
        self.key_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.key_entry = tk.Entry(self, show='*')
        self.key_entry.grid(row=3, column=1, padx=10, pady=5, sticky='ew')

        # 功能按钮区域
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=4, column=0, columnspan=2, pady=15, sticky='ew')
        
        # 蓝牙状态按钮
        self.bluetooth_button = tk.Button(self.button_frame, text='蓝牙状态', command=self.toggle_bluetooth)
        self.bluetooth_button.pack(side='left', padx=5)

        # 保存配置按钮
        self.save_button = tk.Button(self.button_frame, text='保存配置', command=self.save_config)        self.save_button.pack(side='left', padx=5)
        
        # 获取API按钮
        self.get_api_button = tk.Button(self.button_frame, text='获取API', command=self.open_api_url)
        self.get_api_button.pack(side='left', padx=5)



        # 启动按钮
        self.start_button = tk.Button(self, text='启动', command=self.start_assistant, bg='#4CAF50', fg='white')
        self.start_button.grid(row=5, column=0, columnspan=2, padx=20, pady=20, sticky='nsew')

        # 加载已有配置
        self.load_config()

    def start_assistant(self):
        global API_URL
        API_URL = self.url_entry.get().rstrip('V1')
        if not hasattr(self, 'running') or not self.running:
            self.running = True
            self.assistant_thread = threading.Thread(target=self.run_assistant, daemon=True)
            self.assistant_thread.start()
            self.start_button.config(text='停止', bg='red')
        else:
            self.running = False
            self.start_button.config(text='启动', bg='#4CAF50')

    def run_assistant(self):
        while self.running:
            try:
                if self.listen_for_wake_word():
                    command = self.listen_for_command()
                    if command:
                        response = self.call_api(command, self.model_entry.get())
                        if response:
                            print(f'AI 回复: {response}')
                            self.after(0, self.speak_response, response)
            except Exception as e:
                self.after(0, self.log_message, f"运行错误: {str(e)}")

    def speak_response(self, response):
        engine.say(response)
        engine.runAndWait()

    def listen_for_wake_word(self):
        try:
            if not hasattr(self, 'wake_word_logged') or not self.wake_word_logged:
                self.after(0, self.log_message, "监听唤醒词...")
                self.wake_word_logged = True
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=3, phrase_time_limit=5)
            try:
                text = r.recognize_google(audio, language='zh-CN')
                if self.wake_entry.get().strip() in text:
                    self.wake_word_logged = False
                    return True
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                self.after(0, messagebox.showerror, '连接错误', f'无法连接语音识别服务: {e}')
        except Exception as e:
            self.after(0, self.log_message, f"唤醒词监听错误: {str(e)}")
        return False

    def listen_for_command(self):
        with sr.Microphone() as source:
            print('请说出您的命令...')
            audio = r.listen(source)
        try:
            command = r.recognize_google(audio, language='zh-CN')
            print(f'命令: {command}')
            return command
        except sr.UnknownValueError:
            print('无法识别语音')
        except sr.RequestError as e:
            print(f'语音识别服务连接失败: {e}')
            messagebox.showerror('连接错误', '无法连接语音识别服务，请检查网络连接')
        return None

    def log_message(self, message):
        self.log_text.insert(tk.END, f"[LOG] {message}\n")
        self.log_text.see(tk.END)

    def listen_for_wake_word(self):
        self.log_message("监听唤醒词...")

    def call_api(self, command, model_name):
        self.log_message(f"收到命令: {command}")
        response = self._call_model_api(command, model_name)
        if response:
            self.log_message("模型响应处理完成")
            return self._call_voice_api(response)
        return None

    def _call_voice_api(self, text):
        try:
            voice_uilapi = self.voice_uilapi_entry.get()
            voice_model_name = self.voice_model_entry.get()
            self.log_message("正在调用语音服务API...")
            headers = {'Authorization': f'Bearer {self.key_entry.get()}'}
            data = {
                'text': text,
                'model': voice_model_name
            }
            response = requests.post(voice_uilapi, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', text)
            else:
                print(f'语音服务 API 请求失败，状态码: {response.status_code}')
        except Exception as e:
            self.log_message(f"语音服务错误: {str(e)}")
        return text

    def _call_model_api(self, command, model_name):
        headers = {'Authorization': f'Bearer {self.key_entry.get()}'}
        data = {
            'command': command,
            'model': model_name,
            'history': conversation_history
        }
        try:
            response = requests.post(API_URL, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                conversation_history.append(result['response'])
                return result['response']
            else:
                print(f'API 请求失败，状态码: {response.status_code}')
        except requests.RequestException as e:
            print(f'API 请求错误: {e}')
        return None


    def toggle_bluetooth(self):
        current_device = getattr(self, 'bluetooth_device', '扬声器')
        new_device = '蓝牙耳机' if current_device == '扬声器' else '扬声器'
        self.bluetooth_device = new_device
        engine.setProperty('output_device', new_device)
        messagebox.showinfo('蓝牙状态', f'已切换到 {new_device}')

    def open_api_url(self):
        import webbrowser
        webbrowser.open('https://cloud.siliconflow.cn/i/QOxdzxkd')
        
    def save_config(self):
        config = {
            'api_url': self.url_entry.get(),
            'model_name': self.model_entry.get(),
            'wake_word': self.wake_entry.get(),
            'api_key': self.key_entry.get(),
            'bluetooth_device': getattr(self, 'bluetooth_device', '扬声器'),
            'voice_uilapi': self.voice_uilapi_entry.get(),
            'voice_model_name': self.voice_model_entry.get(),
            'voice_url': self.voice_entry.get()
        }
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f)
            messagebox.showinfo('成功', '配置保存成功')
        except Exception as e:
            messagebox.showerror('错误', f'配置保存失败: {e}')



    def load_config(self):
        try:
            # 确保输入框在加载配置前已创建
            self.create_input_fields()
            if os.path.exists('config.json'):
                with open('config.json') as f:
                    config = json.load(f)
                self.url_entry.delete(0, tk.END)
                api_url = config.get('api_url', '')
                if api_url:
                    self.url_entry.insert(0, api_url)
                else:
                    self.url_entry.insert(0, 'https://api.ciallo.ac.cn/v1')
                self.model_entry.delete(0, tk.END)
                model_name = config.get('model_name', '')
                if model_name:
                    self.model_entry.insert(0, model_name)
                self.wake_entry.delete(0, tk.END)
                wake_word = config.get('wake_word', '')
                if wake_word:
                    self.wake_entry.insert(0, wake_word)
                self.key_entry.delete(0, tk.END)
                api_key = config.get('api_key', '')
                if api_key:
                    self.key_entry.insert(0, api_key)
                self.voice_uilapi_entry.delete(0, tk.END)
                voice_uilapi = config.get('voice_uilapi', '')
                if voice_uilapi:
                    self.voice_uilapi_entry.insert(0, voice_uilapi)
                self.voice_model_entry.delete(0, tk.END)
                voice_model_name = config.get('voice_model_name', '')
                if voice_model_name:
                    self.voice_model_entry.insert(0, voice_model_name)
                
                self.voice_entry.delete(0, tk.END)
                voice_url = config.get('voice_url', '')
                if voice_url:
                    self.voice_entry.insert(0, voice_url)
        except Exception as e:
            print(f'加载配置失败: {e}')
            messagebox.showerror('错误', f'加载配置失败: {e}')
    def create_input_fields(self):
        # 语音服务 URL 输入框
        self.voice_label = tk.Label(self, text='语音服务 URL:')
        self.voice_label.grid(row=4, column=0, padx=10, pady=5, sticky='e')
        self.voice_entry = tk.Entry(self)
        self.voice_entry.grid(row=4, column=1, padx=10, pady=5, sticky='ew')
        # 语音服务 Uilapi 输入框
        self.voice_uilapi_label = tk.Label(self, text='语音服务 Uilapi:')
        self.voice_uilapi_label.grid(row=5, column=0, padx=10, pady=5, sticky='e')
        self.voice_uilapi_entry = tk.Entry(self)
        self.voice_uilapi_entry.grid(row=5, column=1, padx=10, pady=5, sticky='ew')
        # 语音服务模型名称输入框
        self.voice_model_label = tk.Label(self, text='语音服务模型名称:')
        self.voice_model_label.grid(row=6, column=0, padx=10, pady=5, sticky='e')
        self.voice_model_entry = tk.Entry(self)
        self.voice_model_entry.grid(row=6, column=1, padx=10, pady=5, sticky='ew')

        # 调整按钮区域位置
        self.button_frame.grid(row=7, column=0, columnspan=2, pady=15, sticky='ew')

        # 启动按钮下移
        self.start_button.grid(row=8, column=0, columnspan=2, padx=20, pady=20, sticky='nsew')

        # 日志区域
        self.log_label = tk.Label(self, text='运行日志:')
        self.log_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5, sticky='w')

        self.log_text = tk.Text(self, height=8)
        self.log_scroll = tk.Scrollbar(self, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        self.log_text.grid(row=10, column=0, columnspan=2, padx=10, pady=5, sticky='nsew')
        self.log_scroll.grid(row=10, column=2, sticky='ns')

        # 配置布局权重
        self.grid_rowconfigure(10, weight=1)

if __name__ == '__main__':
    app = App()
    app.mainloop()

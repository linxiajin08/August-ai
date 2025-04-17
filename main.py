import speech_recognition as sr
import requests

# 初始化语音识别器
r = sr.Recognizer()

# 对话历史记录
conversation_history = []

# 关键词
WAKE_WORD = '特定关键词'

# API 地址
API_URL = 'your_api_url'


def listen_for_wake_word():
    with sr.Microphone() as source:
        print('等待唤醒词...')
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language='zh-CN')
        print(f'识别结果: {text}')
        if WAKE_WORD in text:
            return True
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f'请求错误; {e}')
    return False


def listen_for_command():
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
        print(f'请求错误; {e}')
    return None


def call_api(command):
    global conversation_history
    conversation_history.append(command)
    data = {
        'command': command,
        'history': conversation_history
    }
    try:
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            result = response.json()
            conversation_history.append(result['response'])
            return result['response']
        else:
            print(f'API 请求失败，状态码: {response.status_code}')
    except requests.RequestException as e:
        print(f'API 请求错误: {e}')
    return None


if __name__ == '__main__':
    while True:
        if listen_for_wake_word():
            command = listen_for_command()
            if command:
                response = call_api(command)
                if response:
                    print(f'AI 回复: {response}')
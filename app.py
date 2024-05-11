import time
import os
import datetime
import webbrowser
import glob
import json
from flask import render_template, Flask, jsonify, request
from flask_socketio import SocketIO
from threading import Thread
import requests


class WebUI:
    def __init__(self):
        # WebUI
        self.webapp = Flask(__name__)
        # self.socketio = SocketIO(self.webapp)
        self.messages = ["hello, this is a test string", "another line"]  # a list to cache recorded sentence
        
        # 创建相应的文件夹
        self.recorder_path = '/home/seeed/aa/raw_meeting_transcript'
        self.summary_path = '/home/seeed/aa/meeting_summary'
        if not os.path.exists(self.recorder_path):
            os.makedirs(self.recorder_path)
            print(f"Folder '{self.recorder_path}' was created.")
        else:
            print(f"Folder '{self.recorder_path}' already exists.")
        if not os.path.exists(self.summary_path):
            os.makedirs(self.summary_path)
            print(f"Folder '{self.summary_path}' was created.")
        else:
            print(f"Folder '{self.summary_path}' already exists.")

        # ASR
        self.asr_server_url = 'http://127.0.0.1:7771'
        self.asr_flag = 0

        # LLM
        self.llm_url = 'http://localhost:11434/api/generate'

        self.save_record_name = None
        self.webapp_thread = None
        self.setup_routes()

    def setup_routes(self):
        @self.webapp.route('/')
        def index():
            return render_template('index.html')
        
        @self.webapp.route('/chat-rag', methods=['POST'])
        def chat_rag():
            data = request.get_json()

            url = 'http://127.0.0.1:7774/api/rag-query'
            params = {'prompt': data['text']}

            response = requests.get(url, params=params)

            if response.status_code == 200:
                rst = response.json()
                print(rst)
            else:
                print('Failed to retrieve data:', response.status_code)

            return jsonify(response=rst['message'])
        
        @self.webapp.route('/get_recorder_messages', methods=['GET'])
        def get_messages():
            response = requests.get('http://127.0.0.1:7771/api/get-text')
            if response.status_code == 200:
                data = response.json()
                if self.asr_flag == 1:
                    if data['content'] != self.messages[-1] and data['content'] not in self.messages:
                        self.messages[-1] = data['content']

                    if data['final'] is True and self.messages[-1] != ' ':
                        self.messages.append(' ')
            else:
                print('Failed to retrieve data:', response.status_code)
            return jsonify(self.messages)

        @self.webapp.route('/btn-start-record', methods=['POST'])
        def btn_start_record():
            self.messages.clear()
            self.messages.append('')
            self.asr_flag = 1
            return '', 200

        @self.webapp.route('/btn-stop-record', methods=['POST'])
        def btn_stop_record():
            self.asr_flag = 0
            return '', 200
        
        @self.webapp.route('/save-record', methods=['POST'])
        def save_record():
            now = datetime.datetime.now()
            formatted_time = now.strftime('%Y-%m-%d_%H-%M-%S')
            self.save_record_name = f'record_{formatted_time}.txt'
            print(f'{self.recorder_path}/{self.save_record_name}')
            with open(f'{self.recorder_path}/{self.save_record_name}', 'w') as file:
                for item in self.messages:
                    file.write(item + '\n')
            return '', 200
        
        @self.webapp.route('/gen-summary', methods=['POST'])
        def gen_summary():
            self.asr_flag = 0

            file_path = self.get_latest_txt_file(self.recorder_path)
            print(file_path)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read() 
            
            data = {
                "model": "llama3",
                "prompt": f"Please summarise this meeting transcript:{content}"
            }
            response = requests.post(self.llm_url, json=data, stream=True)
            if response.status_code == 200:
                self.messages.clear()
                self.messages.append('')
                for line in response.iter_lines():
                    if line: 
                        json_data = json.loads(line.decode('utf-8'))
                        self.messages[-1] += json_data['response']
                        print(json_data)
            else:
                print("Failed to get valid response, status code:", response.status_code)
            return '', 200

        @self.webapp.route('/save-summary', methods=['POST'])
        def save_summary():
            self.asr_flag = 0
            record_file_path = self.get_latest_txt_file(self.recorder_path)
            filename = os.path.basename(record_file_path)
            filename = 'summary_' + filename
            save_path = os.path.join(self.summary_path, filename)
            print(save_path)

            with open(save_path, 'w') as file:
                for item in self.messages:
                    file.write(item + '\n')

            return '', 200
        
        @self.webapp.route('/get_messages', methods=['GET'])
        def get_messages1():
            return jsonify(self.messages)
        
    def run(self):
        self.webapp.run()

    def get_asr_message(self):
        url = self.asr_server_url + '/api/get-text'
        while True:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if self.asr_flag == 1:
                    if data['content'] != self.messages[-1] and data['content'] not in self.messages:
                        self.messages[-1] = data['content']
                    if data['final'] is True and self.messages[-1] != '':
                        self.messages.append('')
                    # print(self.messages[-1])
            else:
                print('Failed to retrieve data:', response.status_code)
            time.sleep(1)

    @staticmethod
    def get_latest_txt_file(directory):
        txt_files = {}

        for filename in os.listdir(directory):
            if filename.endswith('.txt'): 
                full_path = os.path.join(directory, filename)
                mod_time = os.path.getmtime(full_path)
                txt_files[full_path] = mod_time

        if txt_files:
            latest_file = max(txt_files, key=txt_files.get)
            return latest_file
        else:
            return None

if __name__ == '__main__':
    re = WebUI()
    re.run()

#!/usr/bin/env python3
import sys
import time
import threading
import pyaudio
from flask import Flask, jsonify, request, Response, stream_with_context
import riva.client
import riva.client.audio_io


class RivaBase(threading.Thread):

    def __init__(self, auth=None, input_device=None, sample_rate_hz=16000, audio_chunk=1600, audio_channels=1,
                 automatic_punctuation=True, verbatim_transcripts=True, profanity_filter=False,
                 language_code='en-US', boosted_lm_words=None, boosted_lm_score=4.0, callback=None):
        super(RivaBase, self).__init__()

        assert auth is not None, f"Invalid parameter： {auth}"
        self.asr_service = riva.client.ASRService(auth)

        self.input_device = input_device
        self.sample_rate_hz = sample_rate_hz
        self.audio_chunk = audio_chunk
        self.callback = callback
        if self.callback is None:
            self.callback = self.callback_example

        self.asr_config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                language_code=language_code,
                max_alternatives=1,
                profanity_filter=profanity_filter,
                enable_automatic_punctuation=automatic_punctuation,
                verbatim_transcripts=verbatim_transcripts,
                sample_rate_hertz=sample_rate_hz,
                audio_channel_count=audio_channels,
            ),
            interim_results=True,
        )

        riva.client.add_word_boosting_to_config(self.asr_config, boosted_lm_words, boosted_lm_score)
        self.mute_flag = False
        self.stop_flag = False

    def run(self):
        try:
            with riva.client.audio_io.MicrophoneStream(
                    self.sample_rate_hz,
                    self.audio_chunk,
                    device=self.input_device,
            ) as audio_chunk_iterator:
                responses = self.asr_service.streaming_response_generator(
                    audio_chunks=audio_chunk_iterator, streaming_config=self.asr_config
                )
                for response in responses:
                    if self.stop_flag:
                        audio_chunk_iterator.close()
                    if self.get_mute_state():
                        continue
                    else:
                        if not response.results:
                            continue
                        self.callback(response)
            print('ASR Server Stop!')
        except:
            sys.exit(0)

    @staticmethod
    def callback_example(response):
        try:
            for result in response.results:
                if not result.alternatives:
                    continue
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    print("## " + transcript)
                    print(f"Confidence:{result.alternatives[0].confidence:9.4f}" + "\n")
                    return True
                else:
                    print(">> " + transcript)
                    print(f"Stability：{result.stability:9.4f}" + "\n")
        finally:
            pass

    def get_mute_state(self):
        return self.mute_flag

    @staticmethod
    def list_devices():
        riva.client.audio_io.list_input_devices()


class ASR_Riva:
    def __init__(self, input_device=None, sample_rate_hz=None):
        self.asrapp = Flask(__name__)
        self.port=7771
        self.setup_routes()

        self.riva_server = "127.0.0.1:50051"

        if input_device is None:
            target_device = self.get_asr_devices_list()
            input_device = target_device['index']
            sample_rate_hz = int(target_device['defaultSampleRate'])
            print(f"Microphone parameters : {input_device}, {sample_rate_hz}")

        auth = riva.client.Auth(uri=self.riva_server)
        self.asr = RivaBase(auth, input_device, sample_rate_hz, callback=self.asr_callback)
        self.asr.start()

        self.text_cache = []
        self.text_stream = {'content':'', 'final': True, 'push': True, 'asr_state': self.asr.stop_flag}

    def asr_callback(self, response):
        try:
            
            for result in response.results:
                if not result.alternatives:
                    continue
                transcript = result.alternatives[0].transcript

                if result.is_final:
                    print("## " + transcript)
                    print(f"Confidence:{result.alternatives[0].confidence:9.4f}" + "\n")
                    self.text_stream['content'] = transcript
                    self.text_stream['final'] = True
                    self.text_stream['push'] = False
                    self.text_cache.append(self.text_stream)
                    if len(self.text_cache) > 100:
                        del self.text_cache[:50]
                else:
                    if result.stability > 0.8:
                        print(">> " + transcript)
                        print(f"Stability：{result.stability:9.4f}" + "\n")
                        self.text_stream['content'] = transcript
                        self.text_stream['final'] = False
                        self.text_stream['push'] = False
        finally:
            pass

    def setup_routes(self):

        @self.asrapp.route('/api/get-text')
        def get_text():
            self.text_stream['push'] = True
            return jsonify(self.text_stream)

        @self.asrapp.route('/api/get-cache')
        def get_cache():
            return jsonify(self.text_cache[-1])

        @self.asrapp.route('/api/asr-stop')
        def asr_stop():
            self.asr.stop_flag=True
            print('Stop!')
            return jsonify({"response": 'stop'})
        
        @self.asrapp.route('/api/asr-start')
        def update_doc():
            if self.asr.stop_flag == True:
                self.asr.stop_flag=False
                self.asr.start()
                print('Start!')
                return jsonify({"response": 'start'})
            else:
                return jsonify({"response": 'running'})
        
        @self.asrapp.route('/stream')
        def stream():
            def generate():
                while True:
                    if self.text_stream['push'] is False:
                        yield self.text_stream['content'] + '\n'
                    time.sleep(1)
            return Response(stream_with_context(generate()), mimetype='text/plain')


    def run(self):
        self.asrapp.run(port=self.port)

    @staticmethod
    def get_asr_devices_list():
        target_device = None
        p = pyaudio.PyAudio()
        print("Input audio devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] < 1:
                continue
            if 'USB' in info["name"]:
                target_device = info
            print(f"{info['index']}: {info['name']}")
        p.terminate()
        if target_device is None:
            print('No available input device found, please manually config an device.')
            sys.exit(0)
        else:
            return target_device

if __name__ == '__main__':
    re = ASR_Riva()
    re.run()

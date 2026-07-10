# backend/video_engine.py
import os
import requests
import time
import base64

class VideoGenerator:
    def __init__(self):
        self.api_key = os.getenv('HUGGINGFACE_TOKEN')
        self.endpoint = "https://api-inference.huggingface.co/models/nvidia/Cosmos3-Nano"

    def generate_scene(self, prompt: str, duration: int = 5) -> dict:
        if not self.api_key:
            return self._mock_generate(prompt, duration)

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'inputs': prompt,
            'parameters': {
                'duration': duration,
                'fps': 24,
                'height': 704,
                'width': 1280
            }
        }
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=180)
            if response.status_code == 200:
                data = response.json()
                # If the response contains a base64 video, handle it
                if 'video' in data:
                    video_data = data['video']
                    return {
                        'success': True,
                        'video_base64': video_data,
                        'prompt': prompt,
                        'duration': duration
                    }
                return {
                    'success': True,
                    'video_url': data.get('video_url'),
                    'prompt': prompt,
                    'duration': duration
                }
            else:
                return self._mock_generate(prompt, duration)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mock': True,
                'video_url': f'https://example.com/mock_{int(time.time())}.mp4'
            }

    def _mock_generate(self, prompt: str, duration: int) -> dict:
        return {
            'success': True,
            'video_url': f'https://example.com/mock_{int(time.time())}.mp4',
            'prompt': prompt,
            'duration': duration,
            'mock': True
        }

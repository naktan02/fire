import threading
import logging
from flask import Flask, jsonify
from flask_cors import CORS

class EvacuationServer:
    def __init__(self, port=5000):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 로그 레벨 조정
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # 공유 데이터 저장소
        self.status_data = {
            "fire_detected": False,
            "directions": {}
        }
        
        # 라우트 설정
        self._setup_routes()
        
        # 스레드 제어
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True

    def _setup_routes(self):
        @self.app.route('/status')
        def get_status():
            return jsonify(self.status_data)

        @self.app.route('/direction/<int:dot_id>')
        def get_direction(dot_id):
            direction = self.status_data["directions"].get(dot_id, "STOP")
            return jsonify({"id": dot_id, "direction": direction})

    def _run_server(self):
        print(f">>> Web Server started on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

    def start(self):
        self.thread.start()

    def update_data(self, fire_detected, directions):
        """메인 스레드에서 최신 정보를 이 함수로 밀어넣습니다."""
        self.status_data["fire_detected"] = fire_detected
        self.status_data["directions"] = directions
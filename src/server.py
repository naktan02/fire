import threading
import logging
from flask import Flask, jsonify, request  # request 추가됨
from flask_cors import CORS

class EvacuationServer:
    def __init__(self, port=5000):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # 데이터 저장소
        self.status_data = {
            "fire_detected": False,
            "directions": {},
            "people_count": 0  # [추가] 현재 인원수
        }
        
        self._setup_routes()
        
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True

    def _setup_routes(self):
        # 1. 상태 조회 (현황판/아두이노용)
        @self.app.route('/status')
        def get_status():
            return jsonify(self.status_data)

        # 2. 특정 도트 방향 조회 (스마트 비상구용)
        @self.app.route('/direction/<int:dot_id>')
        def get_direction(dot_id):
            direction = self.status_data["directions"].get(dot_id, "STOP")
            return jsonify({
                "id": dot_id, 
                "direction": direction,
                "fire": self.status_data["fire_detected"]
            })

        # 3. [추가] 인원수 업데이트 (아두이노가 보낸 데이터 받기)
        @self.app.route('/api/people_count', methods=['POST'])
        def update_people():
            data = request.get_json()
            if not data:
                return "No Data", 400
            
            msg_type = data.get("type")
            if msg_type == "IN":
                self.status_data["people_count"] += 1
                print(f"[People] Someone entered! Total: {self.status_data['people_count']}")
            elif msg_type == "OUT":
                if self.status_data["people_count"] > 0:
                    self.status_data["people_count"] -= 1
                print(f"[People] Someone left! Total: {self.status_data['people_count']}")
                
            return jsonify({"current_count": self.status_data["people_count"]})

    def _run_server(self):
        print(f">>> Web Server started on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

    def start(self):
        self.thread.start()

    def update_data(self, fire_detected, directions):
        self.status_data["fire_detected"] = fire_detected
        self.status_data["directions"] = directions
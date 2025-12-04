import cv2
import numpy as np

class Detector:
    def __init__(self):
        # 유지보수를 위한 임계값 설정
        self.WALL_THRESH = 200       # 흰색 벽으로 인식할 밝기 기준 (0~255)
        self.CANDLE_THRESH = 240     # 양초 불빛으로 인식할 밝기 기준 (매우 밝음)
        self.MIN_WALL_AREA = 500     # 잡음 제거를 위한 최소 벽 면적
        self.MIN_FIRE_AREA = 10      # 최소 불 영역 크기

    def detect_corners(self, frame):
        """
        검은 배경에서 가장 큰 흰색/밝은 영역(전체 맵 테두리)을 찾거나,
        또는 검은 바닥과 대비되는 사각형 영역을 찾습니다.
        (기존 코드 유지 및 보완)
        """
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)
        edges = cv2.Canny(img_blur, 50, 150) # Canny 임계값 조정

        # 팽창 연산으로 끊어진 선 연결
        kernel = np.ones((5, 5), np.uint8)
        img_dilate = cv2.dilate(edges, kernel, iterations=2)
        img_thresh = cv2.erode(img_dilate, kernel, iterations=1)

        contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, img_thresh

        biggest = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 5000: continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4 and area > max_area:
                biggest = approx
                max_area = area

        if biggest is None:
            return None, img_thresh

        # 좌표 정렬 (TL, TR, BR, BL)
        pts = biggest.reshape(4, 2).astype(np.float32)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1).reshape(-1)

        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]
        tr = pts[np.argmin(diff)]
        bl = pts[np.argmax(diff)]

        corners = np.array([tl, tr, br, bl], dtype=np.float32).reshape(-1, 1, 2)
        return corners, img_thresh

    def warp_perspective(self, frame, corners, width, height):
        if corners is None: return None
        
        dst = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]], dtype=np.float32)
        src = corners.reshape(4, 2).astype(np.float32)
        M = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(frame, M, (width, height))

    def detect_walls_in_map(self, warped_frame):
        """
        [새 기능] 맵 내부의 흰색 벽을 감지합니다.
        검은색 바닥(어두움) vs 흰색 벽(밝음)
        """
        gray = cv2.cvtColor(warped_frame, cv2.COLOR_BGR2GRAY)
        
        # 밝은 부분(흰색 벽)만 추출
        _, mask = cv2.threshold(gray, self.WALL_THRESH, 255, cv2.THRESH_BINARY)
        
        # 노이즈 제거
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask # GridMap에서 이 마스크를 사용해 장애물 등록

    def detect_fire(self, frame):
        """
        [개선됨] 양초는 '매우 밝은 점'으로 인식합니다.
        색상보다는 밝기(Value)나 Grayscale Intensity가 효과적입니다.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 매우 밝은 영역(양초 심지 불빛) 찾기
        _, mask = cv2.threshold(gray, self.CANDLE_THRESH, 255, cv2.THRESH_BINARY)
        
        # 영역 확장 (불의 위험 반경)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fire_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.MIN_FIRE_AREA: continue
            
            x, y, w, h = cv2.boundingRect(c)
            fire_boxes.append((x, y, w, h))

        return fire_boxes, mask

    def detect_exit(self, frame):
        """
        탈출구 인식. 바닥이 검은색이므로 탈출구는 '녹색'이나 다른 색이어야 인식 가능합니다.
        (기존의 녹색 종이 기준으로 작성)
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 녹색 범위 (환경에 따라 튜닝 필요)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        exit_boxes = []
        for c in contours:
            if cv2.contourArea(c) < 200: continue
            x, y, w, h = cv2.boundingRect(c)
            exit_boxes.append((x, y, w, h))
            
        return exit_boxes, mask
# detector.py
import cv2
import numpy as np

class Detector:
    def __init__(self):
        pass

    # -------------------------
    # 1) 맵 코너(종이 모서리) 검출
    # -------------------------
    def detect_corners(self, frame):
        """
        화면 속 '종이'의 4개 모서리를 감지합니다.
        (문서 스캐너처럼 가장 큰 사각형 컨투어를 찾는 방식)

        :param frame: 입력 이미지 프레임 (BGR)
        :return: (corners, mask)
                 corners: 4x1x2 float32 (TL, TR, BR, BL) 또는 None
                 mask: 엣지/컨투어 마스크 (디버깅용)
        """
        # 1. 그레이 + 블러
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)

        # 2. Canny 엣지
        edges = cv2.Canny(img_blur, 80, 200)

        # 3. 팽창/침식으로 엣지 두껍게
        kernel = np.ones((5, 5), np.uint8)
        img_dilate = cv2.dilate(edges, kernel, iterations=2)
        img_thresh = cv2.erode(img_dilate, kernel, iterations=1)

        # 4. 외곽선 찾기
        contours, _ = cv2.findContours(
            img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None, img_thresh

        # 5. 가장 큰 사각형 컨투어 하나 선택
        biggest = None
        max_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # 너무 작은 잡음은 제외 (영상 크기에 따라 조절)
            if area < 5000:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            # 꼭짓점이 4개인 큰 컨투어만 후보
            if len(approx) == 4 and area > max_area:
                biggest = approx
                max_area = area

        if biggest is None:
            return None, img_thresh

        # 6. 점 순서 정렬 (TL, TR, BR, BL)
        pts = biggest.reshape(4, 2).astype(np.float32)

        # (x + y)가 가장 작은 -> TL
        # (x - y)가 가장 작은 -> TR? (블로그 코드랑 맞추기 위해 아래 방식 사용)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1).reshape(-1)

        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]
        tr = pts[np.argmin(diff)]
        bl = pts[np.argmax(diff)]

        corners = np.array([tl, tr, br, bl], dtype=np.float32).reshape(-1, 1, 2)

        # 디버깅용 mask는 엣지/threshold 결과를 그대로 사용
        return corners, img_thresh

    # -------------------------
    # 2) 투시 변환
    # -------------------------
    def warp_perspective(self, frame, corners, width, height):
        """
        감지된 코너를 이용해 프레임을 투시 변환합니다.
        :param frame: 원본 프레임.
        :param corners: 4x1x2 float32 (TL, TR, BR, BL).
        :param width: 결과 맵 너비.
        :param height: 결과 맵 높이.
        :return: warped 이미지 또는 None
        """
        if corners is None or len(corners) != 4:
            return None

        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)

        src = corners.reshape(4, 2).astype(np.float32)
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(frame, M, (width, height))

        return warped

    # -------------------------
    # 3) 불(빨간색) 감지 
    # -------------------------
    def detect_fire(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([179, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fire_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 200:
                continue
            x, y, w, h = cv2.boundingRect(c)
            fire_boxes.append((x, y, w, h))

        return fire_boxes, mask

    # -------------------------
    # 4) 탈출구(검은색) 감지
    # -------------------------
    def detect_exit(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 60])
        mask = cv2.inRange(hsv, lower_black, upper_black)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        exit_boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 200:
                continue
            x, y, w, h = cv2.boundingRect(c)
            exit_boxes.append((x, y, w, h))

        return exit_boxes, mask

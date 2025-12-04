from get_coords import main as coord_mode
from main import main as evac_mode

if __name__ == "__main__":
    print("=== 모드 선택 ===")
    print("1. 카메라에서 맵 warp + 좌표 찍기 (DOT / EXIT)")
    print("2. 도트별 최단 경로 시뮬레이션 (메인 알고리즘)")

    mode = input("모드를 선택하세요 (1/2): ").strip()

    if mode == "1":
        coord_mode()
    elif mode == "2":
        evac_mode()
    else:
        print("잘못된 입력입니다.")

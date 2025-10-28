#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proto3.py — Pi + Coral EdgeTPU + CatCIN API
(v3: YUYV 640x480, 쿨다운 제거, 1-shot, 서보 +23도 누적 이동)
Flow:
  1. Detect 'cat'
  2. Capture 1 frame → POST /catcin/recognize-and-get-dues
  3. If is_due=True → Servo slow-move (+23도 누적) + POST /catcin/medi-logs
"""

import os, time, argparse, requests, uuid
from datetime import datetime, timedelta
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from adafruit_servokit import ServoKit

from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter, run_inference

import RPi.GPIO as GPIO

# 맨 위 import들 아래에 추가
from threading import Thread, Lock

SERVO_LOCK = Lock()  # 서보/기록 동시 접근 방지

# ---------------- Config ----------------
CAT_CLASS_ID = 17
SCORE_TH = 0.5
CAP_DIR = Path("/home/pi/cat_caps"); CAP_DIR.mkdir(parents=True, exist_ok=True)
KEEP_CAPS = 60

# --- [★v4 수정★] Servo Config (개별 누적 이동 로직) ---
SERVO_CHANNELS = [8, 9, 10, 11] # (프로젝트의 채널)
STEP_DELAY = 0.02           # 1도당 이동 딜레이 (속도)
DISPENSE_MOVE_ANGLE = 23    # 1회 배출 시 이동 각도
# g_current_angle = 0       # (v3 전역 변수, v4에서 사용 안 함)
g_current_angles = {ch: 0 for ch in SERVO_CHANNELS} # ★ v4: 채널별 개별 각도
# --- [★v4 완료★] ---

# --- [★v4 추가★] 약-서보 매핑 ---
MEDICINE_TO_SERVO_MAP = {
    "고양이 Impact": 8,
    "고양이 combo": 9,
    "캣츠힐 초록": 10,
    # "다른 약 이름": 11 # 채널 11이 필요하면 여기에 추가
}
# --- [★v4 추가 완료★] ---

# ---------------- Drawing ----------------
def draw_dets(img_bgr, inference_size, objs, labels):
    h, w, _ = img_bgr.shape
    sx, sy = w / inference_size[0], h / inference_size[1]
    for o in objs:
        bb = o.bbox.scale(sx, sy)
        x0, y0, x1, y1 = int(bb.xmin), int(bb.ymin), int(bb.xmax), int(bb.ymax)
        label = f"{int(o.score*100)}% {labels.get(o.id, o.id)}"
        cv2.rectangle(img_bgr, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2.putText(img_bgr, label, (x0, max(0, y0-8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    return img_bgr

# --- PCA9685 setup ---
_pca_kit = None

# --- [★v4 수정★] 개별 서보 이동 헬퍼 함수 ---
def _servo_slow_move(kit, channel_target_map):
    """
    (v4 수정)
    지정된 채널들을 {채널: 목표각도} 맵에 따라 1도씩 천천히 이동시킵니다.
    g_current_angles 상태를 업데이트합니다.
    """
    global g_current_angles

    # 1. 이동 계획 생성
    moves = []
    max_steps = 0
    for ch, target_angle in channel_target_map.items():
        if ch not in g_current_angles:
            print(f"[servo_slow] 경고: {ch}는 관리대상이 아닙니다. 건너뜁니다.")
            continue
            
        target_angle = int(max(0, min(180, target_angle))) # 0-180도
        current = g_current_angles[ch] # ★ v4: 채널의 현재 각도

        if target_angle == current:
            print(f"[servo_slow] ch {ch}: 이미 {target_angle}°입니다. (이동 불필요)")
            continue

        print(f"[servo_slow] 계획 ch {ch}: {current}° -> {target_angle}°")
        step = 1 if target_angle > current else -1
        # range(start, end, step)
        angle_steps = list(range(current + step, target_angle + step, step))
        moves.append({'ch': ch, 'steps': angle_steps, 'target': target_angle})
        max_steps = max(max_steps, len(angle_steps))
    
    if not moves:
        print(f"[servo_slow] 이동할 채널이 없습니다.")
        return

    print(f"[servo_slow] 1도씩 동시 이동 시작 (최대 {max_steps} 스텝, delay={STEP_DELAY}s)...")

    # 2. 1스텝(1도)씩 쪼개서 *동시* 이동
    for i in range(max_steps):
        for move in moves:
            ch = move['ch']
            if i < len(move['steps']): # 아직 이 서보가 이동할 스텝이 남았는지
                angle = move['steps'][i]
                try:
                    kit.servo[ch].angle = angle
                except Exception as e:
                    pass # 개별 서보 에러 무시
        
        time.sleep(STEP_DELAY)

    # 3. ★★★ 현재 각도 상태 업데이트
    for move in moves:
        g_current_angles[move['ch']] = move['target']
    
    print(f"✅ [servo_slow] 이동 완료. 현재 각도: {g_current_angles}")

    # 4. 대기 모드 (전력 해제)
    print("...서보 해제 (duty_cycle = 0)...")
    for ch in channel_target_map.keys(): # 이동에 관여한 채널만 해제
        try:
            kit._pca.channels[ch].duty_cycle = 0
        except:
            pass


# --- [★v4 수정★] 서보 배출 로직 (개별 +23도 누적 이동) ---
def _servo_dispense(channels_to_move: list):
    """
    (새 로직 v4)
    신호를 받을 때마다 'channels_to_move' 리스트의 채널들만
    현재 각도에서 +23도씩 천천히 이동합니다.
    """
    global g_current_angles # ★ v4: 개별 각도
    global DISPENSE_MOVE_ANGLE
    
    if not channels_to_move:
        print("⚠️ [servo_dispense] 이동할 채널이 없습니다. (channels_to_move is empty)")
        return

    # 중복 제거
    unique_channels = sorted(list(set(channels_to_move)))
    print(f"🔧 [servo_dispense] {unique_channels} 채널 +{DISPENSE_MOVE_ANGLE}도 이동...")
    kit = _pca_get() # 초기화 보장

    # --- 1. 목표 각도 맵 계산 ---
    target_map = {}
    for ch in unique_channels:
        if ch not in g_current_angles:
            print(f"⚠️ [servo_dispense] 경고: {ch}는 관리 대상 채널이 아닙니다. 건너뜁니다.")
            continue
        
        current = g_current_angles[ch] # ★ v4: 개별 현재 각도
        target = min(current + DISPENSE_MOVE_ANGLE, 180) # 180도 넘지 않도록
        
        if target == current:
            print(f"⚠️ [servo_dispense] ch {ch}: 이미 최대 각도({current}°)입니다. 이동하지 않습니다.")
            continue
        
        target_map[ch] = target # (예: {8: 23, 9: 46})

    if not target_map:
        print("⚠️ [servo_dispense] 모든 대상 채널이 이미 최대 각도이거나 대상이 없습니다.")
        return

    print(f"...이동 계획(Map): {target_map}")
    _servo_slow_move(kit, target_map) # ★ v4: 새 헬퍼 함수 호출
    # (g_current_angles은 _servo_slow_move 내부에서 갱신됨)

    print(f"✅ [servo_dispense] 이동 완료. 새 각도: {g_current_angles}")

# --- [★추가★] 엔터 키 입력을 위한 스레드 핸들러 ---
def process_event_async(args, event_id, shots):
    """
    백그라운드 작업 (서보 로직 v4 적용됨)
    """
    try:
        resp = recognize(args.recognize_url, args.device_id, event_id, shots, args.api_key)
        print("[client] server resp:", resp, flush=True)

        recog = (resp.get("recognition") or {})
        med   = (resp.get("medication")  or {})
        cat_id = extract_cat_id(recog)
        due_list = med.get("due_medicines") or []
        due_now = [m for m in due_list if isinstance(m, dict) and m.get("is_due") is True]
        print(f"[debug] (async) due_now_count={len(due_now)}, cat_id={cat_id}", flush=True)

        # --- [★v4 수정★] 투약할 약 이름 기반으로 채널 매핑 ---
        channels_to_trigger = []
        if due_now and cat_id:
            for item in due_now:
                med_name = item.get("medicine_name")
                if not med_name:
                    continue
                
                # 맵(MEDICINE_TO_SERVO_MAP)에서 채널 찾기
                ch = MEDICINE_TO_SERVO_MAP.get(med_name)
                if ch is not None:
                    if ch not in channels_to_trigger:
                        channels_to_trigger.append(ch)
                else:
                    print(f"[client] (async) 경고: '{med_name}'에 매핑된 서보가 없습니다.")
            
            print(f"[client] (async) 투약 대상 약품 발견. 서보 채널: {channels_to_trigger}")
        # --- [★v4 수정 완료★] ---
        
        # --- [★v4.1 추가★] 약(8,9,10)이 하나라도 작동하면, 사료(11)도 같이 작동 ---
        # 1. 11번 채널이 관리 대상인지 확인 (SERVO_CHANNELS에 11이 있어야 함)
        if 11 in SERVO_CHANNELS:
            
            # 2. 8, 9, 10번 채널 중 하나라도 channels_to_trigger 리스트에 있는지 확인
            med_channels_triggered = any(ch in channels_to_trigger for ch in [8, 9, 10])
            
            # 3. 약 채널이 작동했고, 11번이 아직 리스트에 없다면
            if med_channels_triggered and (11 not in channels_to_trigger):
                print("[client] (async) 약품(8,9,10)이 배출되므로, 사료(11)도 함께 추가합니다.")
                channels_to_trigger.append(11)
        # --- [★v4.1 추가 완료★] ---

        if not channels_to_trigger: # (수정) due_now -> channels_to_trigger
            print("[client] (async) no due medicine (or no mapped servo) -> NOOP", flush=True)
            return

        # 서보 & 로그는 동시 접근 막기 위해 락
        with SERVO_LOCK:
            if args.dry_run:
                print(f"[client] (async) DRY-RUN: would DISPENSE (channels: {channels_to_trigger}) now.", flush=True)
            else:
                print(f"[client] (async) DISPENSE -> servo (channels: {channels_to_trigger})", flush=True)
                # --- [★v4 수정★] 채널 리스트를 인자로 전달 ---
                _servo_dispense(channels_to_trigger)
                # --- [★v4 수정 완료★] ---

            # 투약 기록 생성 (이 로직은 변경 없음)
            for item in due_now:
                mid = item.get("medicine_id")
                if not mid: continue
                try:
                    res = create_medi_log(args.base_url, cat_id, mid, args.api_key)
                    print(f"[client] (async) medi-log created for med={mid}: {res}", flush=True)
                except Exception as e:
                    print("[client] (async) warn: medi-log failed:", e, flush=True)

    except Exception as e:
        print("[client] (async) error:", e, flush=True)


# --- [★v4 수정★] 엔터 키 입력을 위한 스레드 핸들러 ---
def manual_servo_trigger():
    """
    키 입력(메인 스레드)을 받아 서보를 안전하게(락) 작동시키는
    백그라운드 스레드용 함수. (v4 수정)
    """
    # API 콜백과 동일한 락을 사용해 동시 접근 방지
    print("\n[manual_trigger] 엔터 키 입력 감지. 서보 락 획득 시도...", flush=True)
    with SERVO_LOCK:
        print("[manual_trigger] 락 획득. 수동 배출(+23도)을 호출합니다.", flush=True)
        
        # --- [★v4 수정★]
        # 엔터키는 '모든' 관리 대상 채널을 이동시킵니다 (기존 v3 동작과 유사)
        _servo_dispense(SERVO_CHANNELS)
        # --- [★v4 수정 완료★] ---

    print("[manual_trigger] 작업 완료. 락 해제.", flush=True)
# --- [★v4 수정★] 서보 초기화 로직 (개별 각도 적용) ---
def _pca_get():
    """
    ServoKit 객체를 가져오거나, 없으면 새로 초기화합니다.
    (수정) g_current_angles를 사용해 0도로 리셋합니다.
    """
    global _pca_kit
    global g_current_angles # ★ v4: 개별 각도
    if _pca_kit is None:
        print("🔧 ServoKit 초기화 중 (v4 슬로우 무브 로직 적용)...")
        _pca_kit = ServoKit(channels=16, frequency=50)

        print(f"...채널 {SERVO_CHANNELS} 펄스 폭 설정 (500-2500)...")
        for ch in SERVO_CHANNELS:
            _pca_kit.servo[ch].set_pulse_width_range(500, 2500)

        # (수정) '열림' 각도(23도)에서 0도로 천천히 이동
        print("...초기화: 0도로 천천히 이동합니다 (안전 리셋)...")
        
        # ★ v4: 모든 채널을 23도로 가정하고 시작
        for ch in SERVO_CHANNELS:
            g_current_angles[ch] = DISPENSE_MOVE_ANGLE
        
        # ★ v4: 모든 채널을 0도로 이동 (새 헬퍼 함수 사용)
        target_map = {ch: 0 for ch in SERVO_CHANNELS}
        _servo_slow_move(_pca_kit, target_map)
        # (이제 g_current_angles는 모두 0이 됨)

        print(f"✅ 서보 초기화 완료. 현재 각도: {g_current_angles}")

    return _pca_kit

# ---------------- Camera ----------------
def open_camera_yuyv_only(idx, w, h, fps):
    """
    이 하드웨어(YUYV @ 640x480)에 최적화된 카메라 열기 함수
    """
    print(f"Opening YUYV-only camera: /dev/video{idx} ({w}x{h} @ {fps}fps)")
    cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open /dev/video{idx}")

    # 1. YUYV 포맷 설정
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))

    # 2. 해상도 및 FPS 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)
    time.sleep(0.5) # 설정 적용 대기

    # 3. 설정 확인
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        raise RuntimeError(f"Failed to set YUYV mode or read frame.")

    # 4. YUYV는 cvtColor가 필요하므로 'YUYV_RAW' 모드 반환
    mode = "YUYV_RAW" if (frame.ndim == 2 or (frame.ndim == 3 and frame.shape[2] == 2)) else "BGR"

    print(f"Camera opened successfully (detected mode={mode})")
    return cap, mode


def get_bgr_frame(cap, mode):
    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError("Failed to read frame")
    if mode == "YUYV_RAW" and (frame.ndim == 2 or (frame.ndim == 3 and frame.shape[2] == 2)):
        return cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
    return frame

def get_cat_bbox_px(objs, infer_size, frame_shape, labels, score_th=0.5, cat_id=17, margin=0.10):
    H, W, _ = frame_shape
    sx, sy = W / infer_size[0], H / infer_size[1]
    cats = [o for o in objs if (o.id == cat_id or labels.get(o.id, '').lower() == 'cat') and o.score >= score_th]
    if not cats:
        return None
    best = max(cats, key=lambda o: o.score)
    bb = best.bbox.scale(sx, sy)
    x0, y0, x1, y1 = float(bb.xmin), float(bb.ymin), float(bb.xmax), float(bb.ymax)
    w = x1 - x0; h = y1 - y0
    dx = w * margin; dy = h * margin
    x0 -= dx; y0 -= dy; x1 += dx; y1 += dy
    x0 = max(0, int(x0)); y0 = max(0, int(y0))
    x1 = min(W, int(x1)); y1 = min(H, int(y1))
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1, y1)

# ---------------- HTTP ----------------
def recognize(url, device_id, event_id, image_paths, api_key=""):
    headers = {} if not api_key else {"Authorization": f"Bearer {api_key}"}
    data = {"device_id": device_id, "event_id": event_id}
    files = [("files", (Path(p).name, open(p, "rb"), "image/jpeg")) for p in image_paths]
    try:
        r = requests.post(url, headers=headers, data=data, files=files, timeout=30)
    finally:
        for _, f, *_ in files:
            try: f.close()
            except: pass
    r.raise_for_status()
    return r.json()

def create_medi_log(base_url, cat_id, medicine_id, api_key=""):
    url = f"{base_url}/catcin/medi-logs"
    headers = {} if not api_key else {"Authorization": f"Bearer {api_key}"}
    form = {"cat_id": cat_id, "medicine_id": medicine_id}
    r = requests.post(url, headers=headers, data=form, timeout=20)
    r.raise_for_status()
    if "application/json" in (r.headers.get("content-type", "")):
        return r.json()
    return r.text

# ---------------- Utils ----------------
def _get_fresh_frame(cap, mode, fps):
    flush_n = max(2, int(fps // 5))
    for _ in range(flush_n):
        cap.grab()
    ok, frame = cap.retrieve()
    if not ok or frame is None:
        ok2, frame2 = cap.read()
        if not ok2 or frame2 is None:
            raise RuntimeError("capture failed")
        frame = frame2
    if mode == "YUYV_RAW" and (frame.ndim == 2 or (frame.ndim == 3 and frame.shape[2] == 2)):
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
    else:
        frame_bgr = frame
    return frame_bgr

def capture_one_crop(frame_to_crop, bbox_px, out_dir: Path):
    """
    (수정) 새 프레임을 받지 않고, 좌표 계산에 사용된 프레임을 바로 잘라 저장합니다.
    frame_to_crop: (e.g., 640x480) BGR frame used for detection.
    bbox_px: (x0,y0,x1,y1) crop coordinates.
    """
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    # frame_bgr = _get_fresh_frame(cap, mode, fps) # <-- 삭제

    x0, y0, x1, y1 = bbox_px
    crop = frame_to_crop[y0:y1, x0:x1].copy() # <-- 전달받은 frame_to_crop 사용

    fp = out_dir / f"cap_crop_{ts}_0.jpg"
    Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).save(fp, quality=92)
    return [str(fp)]

def capture_one_full(frame_to_save, out_dir: Path):
    """
    (수정) Fallback용. Bbox를 못찾은 BGR 프레임 1장을 저장합니다.
    """
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    # frame_bgr = _get_fresh_frame(cap, mode, fps) # <-- 삭제

    fp = out_dir / f"cap_full_{ts}_0.jpg"
    # 전달받은 frame_to_save 사용
    Image.fromarray(cv2.cvtColor(frame_to_save, cv2.COLOR_BGR2RGB)).save(fp, quality=92)
    return [str(fp)]

def trim_caps(keep=KEEP_CAPS):
    for old in sorted(CAP_DIR.glob("cap_*.jpg"), reverse=True)[keep:]:
        try: old.unlink()
        except: pass

def extract_cat_id(recog: dict):
    return recog.get("cat_id") or recog.get("new_cat_id") or recog.get("most_similar_to")

# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser()
    default_model_dir = '/home/pi/Projects/coral/pycoral/test_data'
    ap.add_argument('--model',  default=os.path.join(default_model_dir, 'ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite'))
    ap.add_argument('--labels', default=os.path.join(default_model_dir, 'coco_labels.txt'))
    ap.add_argument('--threshold', type=float, default=SCORE_TH)
    ap.add_argument('--top_k', type=int, default=3)
    ap.add_argument('--camera', type=int, default=0)

    # (수정) 카메라 하드웨어에 맞게 640x480으로 변경
    ap.add_argument('--width', type=int, default=640)
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--fps', type=int, default=30)

    ap.add_argument('--recognize_url', required=True)
    ap.add_argument('--base_url', required=True)
    ap.add_argument('--api_key', default="")
    ap.add_argument('--device_id', default='pi-01')
    ap.add_argument('--dry_run', action='store_true')
    ap.add_argument('--no_display', action='store_true')
    args = ap.parse_args()

    # Load EdgeTPU model
    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    labels = read_label_file(args.labels)
    infer_w, infer_h = input_size(interpreter)

    # (수정) YUYV 전용 카메라 열기 함수 호출
    cap, mode = open_camera_yuyv_only(args.camera, args.width, args.height, args.fps)

    if cap is None:
        raise RuntimeError(f"Cannot open /dev/video{args.camera}")
    print(f"🎥 USB camera opened ({mode}). Press 'q' to quit.")

    print("[main] 서보 초기화를 위해 _pca_get()을 미리 호출합니다...")
    _pca_get()
    print("[main] 서보 초기화 완료 (0도 이동), 메인 루프 시작.")

    last_trigger = 0.0
    COOLDOWN_CAPTURE_SEC = 8.0 # (이 쿨다운은 캡처/전송 쿨다운으로, 서보와 무관)

    while True:
        try:
            frame_bgr = get_bgr_frame(cap, mode)
        except Exception as e:
            print("⚠️", e)
            time.sleep(0.03)
            continue

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (infer_w, infer_h), interpolation=cv2.INTER_LINEAR)
        run_inference(interpreter, resized.tobytes())
        objs = get_objects(interpreter, args.threshold)[:args.top_k]

        if not args.no_display:
            view = draw_dets(frame_bgr.copy(), (infer_w, infer_h), objs, labels)
            cv2.imshow('CatCIN (EdgeTPU client)', view)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == 13: # 13 = Enter (Return) 키
                print("[main] Enter 키 감지됨! 수동 서보 트리거 스레드 시작...", flush=True)
                # 메인 루프(영상)가 멈추지 않도록 스레드로 분리
                Thread(target=manual_servo_trigger, daemon=True).start()
               

        print("[debug] objs:", [(labels.get(o.id, o.id), o.id, round(o.score, 3)) for o in objs], flush=True)

        cat_hit = any(
            (labels.get(o.id, '').strip().lower() == 'cat' or o.id == CAT_CLASS_ID)
            and (o.score >= args.threshold)
            for o in objs
        )
        print("[debug] cat_hit =", cat_hit, flush=True)

        if not cat_hit:
            continue

        if time.time() - last_trigger < COOLDOWN_CAPTURE_SEC:
            print(f"[debug] cooldown: {time.time() - last_trigger:.2f}s elapsed (< {COOLDOWN_CAPTURE_SEC}s)")
            continue
        last_trigger = time.time()

        event_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
        print(f"[client] CAT detected -> capture & upload (event_id={event_id})", flush=True)

        try:
            bbox_px = get_cat_bbox_px(objs, (infer_w, infer_h), frame_bgr.shape, labels,
                                      score_th=args.threshold, cat_id=CAT_CLASS_ID, margin=0.12)

            # === [수정된 부분] ===
            if bbox_px is None:
                print("[client] cat bbox not found; fallback full-frame capture")
                # (수정) cap, mode, fps 대신 frame_bgr을 전달
                shots = capture_one_full(frame_bgr, CAP_DIR)
            else:
                print(f"[client] cat bbox:", bbox_px)
                # (수정) cap, mode, fps 대신 frame_bgr을 전달
                shots = capture_one_crop(frame_bgr, bbox_px, CAP_DIR)
            # === [수정 완료] ===

            print("[debug] saved:", shots, flush=True)
            Thread(target=process_event_async, args=(args, event_id, shots), daemon=True).start()
            trim_caps(KEEP_CAPS)

        except Exception as e:
            print("[client] error:", e, flush=True)

    cap.release()
    if not args.no_display:
        cv2.destroyAllWindows()

    # --- 프로그램 종료 시 서보 정리 (finally와 유사) ---
    print("\n\n--- 프로그램을 종료합니다. ---")
    global _pca_kit
    if _pca_kit is not None:
        print("🧹 모든 서보를 안전하게 해제합니다...")
        for ch in SERVO_CHANNELS:
            try:
                _pca_kit._pca.channels[ch].duty_cycle = 0
            except:
                pass
        print("✅ 모든 서보 안전하게 해제 완료.")


if __name__ == "__main__":
    main()

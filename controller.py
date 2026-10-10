import cv2
import mediapipe as mp
import pyautogui
import screen_brightness_control as sbc
import math
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam.")
    exit()

# Screen settings
screen_width, screen_height = pyautogui.size()

previous_action = 0
last_action_time = 0

zoom_level = 100
volume_level = 50
brightness_level = 50

# Get initial brightness if supported
try:
    brightness_level = sbc.get_brightness(display=0)[0]
except Exception:
    pass


def distance(p1, p2, width, height):
    x1, y1 = int(p1.x * width), int(p1.y * height)
    x2, y2 = int(p2.x * width), int(p2.y * height)

    return math.hypot(x2 - x1, y2 - y1)


def count_fingers(hand):
    landmarks = hand.landmark
    count = 0

    # Check four fingers
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    for tip, pip in zip(tips, pips):
        if landmarks[tip].y < landmarks[pip].y:
            count += 1

    return count


while True:
    success, frame = cap.read()

    if not success:
        print("Cannot read webcam.")
        break

    # Mirror camera
    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    message = "Show your hand"

    if results.multi_hand_landmarks:

        hand = results.multi_hand_landmarks[0]
        lm = hand.landmark

        mp_draw.draw_landmarks(
            frame,
            hand,
            mp_hands.HAND_CONNECTIONS
        )

        fingers = count_fingers(hand)

        # Thumb and index finger distance
        pinch_distance = distance(lm[4], lm[8], width, height)

        # Hand's vertical position
        hand_y = int(lm[9].y * height)

        # MODE 1: ZOOM
        # Raise index and middle fingers
        if fingers == 2:

            message = "ZOOM MODE"

            # Increase or decrease zoom using pinch distance
            if pinch_distance > 100 and time.time() - last_action_time > 0.5:
                pyautogui.hotkey('ctrl', '+')
                last_action_time = time.time()

            elif pinch_distance < 40 and time.time() - last_action_time > 0.5:
                pyautogui.hotkey('ctrl', '-')
                last_action_time = time.time()

        # MODE 2: BRIGHTNESS
        # Show all four fingers and thumb
        elif fingers == 4:

            message = "BRIGHTNESS MODE"

            if hand_y < height // 3:
                brightness_level = min(100, brightness_level + 5)

            elif hand_y > 2 * height // 3:
                brightness_level = max(0, brightness_level - 5)

            if time.time() - last_action_time > 0.4:
                try:
                    sbc.set_brightness(brightness_level, display=0)
                    last_action_time = time.time()
                except Exception:
                    pass

        # MODE 3: VOLUME
        # Make a fist
        elif fingers == 0:

            message = "VOLUME MODE"

            if hand_y < height // 3:
                pyautogui.press('volumeup')
                last_action_time = time.time()

            elif hand_y > 2 * height // 3:
                pyautogui.press('volumedown')
                last_action_time = time.time()

        else:
            message = "Change your gesture"

    # Display information
    cv2.putText(
        frame,
        message,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Press Q to exit",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow("Hand Gesture Controller", frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
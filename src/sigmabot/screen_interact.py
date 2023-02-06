import time

import cv2
import numpy as np
import pyautogui
from board_recognizer import recognize

# Define the screen size
screen_width, screen_height = pyautogui.size()

# Define the scale factor for reducing the resolution
scale_factor = 0.5

# Define the chessboard pattern size
pattern_size = (7, 7)

square_size = 76  # chess.com @ 110%

while True:
    # Capture the screen
    screen = pyautogui.screenshot()
    frame = np.array(screen)

    # Reduce the resolution of the frame
    frame = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)

    print(recognize.predict_chessboard(frame))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(corners)
        break

cv2.destroyAllWindows()

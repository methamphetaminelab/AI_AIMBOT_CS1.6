import torch
import numpy as np
import cv2
import pygetwindow as gw
import mss
import time
import keyboard
import pyautogui
import win32api
import win32con

class ObjectDetection:
    def __init__(self, model_path):
        self.model = self.load_model(model_path)
        self.classes = self.model.names
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print('\n\nDevice Used:', self.device)

    def load_model(self, model_path):
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        return model

    def score_frame(self, frame):
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        labels, cord = results.xyxy[0][:, -1], results.xyxyn[0][:, :-1]
        return labels, cord

    def class_to_label(self, x):
        return self.classes[int(x)]

    def plot_boxes(self, results, frame):
        labels, cord = results
        n = len(labels)
        center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2

        closest_distance = float('inf')
        closest_object_coords = None

        for i in range(n):
            row = cord[i]
            if row[4] >= 0.2 and self.class_to_label(labels[i]) == "enemy":
                x1, y1, x2, y2 = int(row[0] * frame.shape[1]), int(row[1] * frame.shape[0]), int(row[2] * frame.shape[1]), int(row[3] * frame.shape[0])
                object_center_x, object_center_y = (x1 + (x2 - x1) // 2, y2 + (y1 - y2) // 2)
                distance = np.sqrt((object_center_x - center_x)**2 + (object_center_y - center_y)**2)

                if distance < closest_distance:
                    closest_distance = distance
                    closest_object_coords = (object_center_x, object_center_y)

                bgr = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                cv2.putText(frame, self.class_to_label(labels[i]), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 2)
                print(f'Detected: [{x1} {y1} | {x2} {y2}]')

        if closest_object_coords:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(speed_factor * (closest_object_coords[0] - center_x)), int(speed_factor * (closest_object_coords[1] - center_y-offset)), 0, 0)
            print(f'Moved to the center of the closest object: {closest_object_coords}')

        return frame

    def get_cs_window_rect(self):
        cs_window = gw.getWindowsWithTitle("Counter-Strike")
        if cs_window:
            cs_window = cs_window[0]
            return cs_window.left, cs_window.top, cs_window.width, cs_window.height
        else:
            raise Exception("No Counter-Strike window")

    def __call__(self):
        with mss.mss() as sct:
            while True:
                cs_rect = self.get_cs_window_rect()
                screen_rect = (cs_rect[0], cs_rect[1], cs_rect[0] + cs_rect[2], cs_rect[1] + cs_rect[3])

                start_time = time.perf_counter()
                frame = np.array(sct.grab(screen_rect))
                results = self.score_frame(frame)
                frame = self.plot_boxes(results, frame)
                end_time = time.perf_counter()

                fps = 1 / np.round(end_time - start_time, 3)
                bgr = (0, 255, 0)
                cv2.putText(frame, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 2)
                cv2.imshow('img', frame)
                print(f'FPS: [ {int(fps)} ]')
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

#---settings---
speed_factor = 5
offest = 15
model_path = 'best.pt'
#---settings---

detection = ObjectDetection(model_path)
detection()

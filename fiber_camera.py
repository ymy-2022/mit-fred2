import time
import sys
import cv2
import numpy as np
from typing import Tuple
from PyQt5.QtWidgets import QWidget, QLabel, QDoubleSpinBox, QInputDialog, QMessageBox
from PyQt5.QtGui import QImage, QPixmap

from database import Database
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from user_interface import UserInterface

class FiberCamera(QWidget):
    use_binary_for_edges = True
    use_erode = True
    use_dilate = True
    use_gaussian = True
    use_binary = True

    def __init__(self, target_diameter, gui: 'UserInterface') -> None:
        super().__init__()
        self.raw_image = QLabel()
        self.canny_image = QLabel()
        self.processed_image = QLabel()
        self.target_diameter = target_diameter  # 现在为 None
        self.capture = cv2.VideoCapture(0)
        self.gui = gui
        self.diameter_coefficient = Database.get_calibration_data("diameter_coefficient")
        self.previous_time = 0.0

    def camera_loop(self) -> None:
        current_time = time.time()
        success, frame = self.capture.read()
        if not success:
            print("Failed to capture frame")
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, _, _ = frame.shape
        frame = frame[height//4:3*height//4, :]
        edges, binary_frame = self.get_edges(frame)
        detected_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, minLineLength=30, maxLineGap=100)
        fiber_diameter = self.get_fiber_diameter(detected_lines)
        frame = self.plot_lines(frame, detected_lines)

        Database.camera_timestamps.append(current_time)
        Database.diameter_readings.append(fiber_diameter)
        Database.diameter_setpoint.append(0)  # 直接写0
        Database.diameter_delta_time.append(current_time - self.previous_time)
        self.previous_time = current_time

        image_for_gui = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        self.raw_image.setPixmap(QPixmap(image_for_gui))

        image_for_gui = QImage(edges, edges.shape[1], edges.shape[0], QImage.Format_Grayscale8)
        self.canny_image.setPixmap(QPixmap(image_for_gui))

        image_for_gui = QImage(binary_frame, binary_frame.shape[1], binary_frame.shape[0], QImage.Format_Grayscale8)
        self.processed_image.setPixmap(QPixmap(image_for_gui))

    def get_edges(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        kernel = np.ones((5,5), np.uint8)

        if FiberCamera.use_erode:
            frame = cv2.erode(frame, kernel, iterations=2)
        if FiberCamera.use_dilate:
            frame = cv2.dilate(frame, kernel, iterations=2)
        if FiberCamera.use_gaussian:
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
        if FiberCamera.use_binary:
            _, binary_frame = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY)
        else:
            binary_frame = frame.copy()

        if FiberCamera.use_binary_for_edges is False:
            edges = cv2.Canny(frame, 100, 250, apertureSize=3)
        else:
            edges = cv2.Canny(binary_frame, 100, 250, apertureSize=3)
        return edges, binary_frame

    def get_fiber_diameter(self, lines):
        leftmost_min = sys.maxsize
        leftmost_max = 0
        rightmost_min = sys.maxsize
        rightmost_max = 0
        if lines is None or len(lines) <= 1:
            return 0
        for line in lines:
            x0, _, x1, _ = line[0]
            leftmost_min = min(leftmost_min, x0, x1)
            leftmost_max = max(leftmost_max, min(x0, x1))
            rightmost_min = min(rightmost_min, max(x0, x1))
            rightmost_max = max(rightmost_max, x0, x1)
        return (((leftmost_max - leftmost_min) + (rightmost_max - rightmost_min)) / 2 * self.diameter_coefficient)

    def get_fiber_diameter_noC(self, lines):
        leftmost_min = sys.maxsize
        leftmost_max = 0
        rightmost_min = sys.maxsize
        rightmost_max = 0
        if lines is None or len(lines) <= 1:
            return 0
        for line in lines:
            x0, _, x1, _ = line[0]
            leftmost_min = min(leftmost_min, x0, x1)
            leftmost_max = max(leftmost_max, min(x0, x1))
            rightmost_min = min(rightmost_min, max(x0, x1))
            rightmost_max = max(rightmost_max, x0, x1)
        return (((leftmost_max - leftmost_min) + (rightmost_max - rightmost_min)) / 2)

    def plot_lines(self, frame, lines):
        if lines is not None:
            for line in lines:
                x0, y0, x1, y1 = line[0]
                cv2.line(frame, (x0, y0), (x1, y1), (255, 0, 0), 2)
        return frame

    def calibrate(self):
        num_samples = 50
        accumulated_diameter = 0
        valid_samples = 0
        diameter_mm, ok = QInputDialog.getDouble(
            self.gui.window,
            "Calibrate Camera",
            "Enter wire actual diameter (mm) for calibration",
            decimals=4,
            min=0.01,
            max=100.0
        )
        if not ok:
            return
        for _ in range(num_samples):
            success, frame = self.capture.read()
            if not success:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            edges, _ = self.get_edges(frame)
            detected_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, minLineLength=30, maxLineGap=100)
            fiber_diameter = self.get_fiber_diameter_noC(detected_lines)
            if fiber_diameter > 0:
                accumulated_diameter += fiber_diameter
                valid_samples += 1
        if valid_samples > 0:
            average_diameter_px = accumulated_diameter / valid_samples
        else:
            average_diameter_px = 1
        self.diameter_coefficient = diameter_mm / average_diameter_px
        Database.update_calibration_data("diameter_coefficient", str(self.diameter_coefficient))
        QMessageBox.information(self.gui.window, "Calibration", "Diameter calibration done.")

    def camera_feedback(self, current_time: float) -> None:
        try:
            success, frame = self.capture.read()
            if not success:
                return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, _, _ = frame.shape
            frame = frame[height//4:3*height//4, :]
            edges, binary_frame = self.get_edges(frame)
            detected_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, minLineLength=30, maxLineGap=100)
            current_diameter = self.get_fiber_diameter(detected_lines)
            if self.gui.diameter_plot:
                self.gui.diameter_plot.update_plot(current_time, current_diameter, 0)
            Database.camera_timestamps.append(current_time)
            Database.diameter_readings.append(current_diameter)
            Database.diameter_setpoint.append(0)
            Database.diameter_delta_time.append(current_time - self.previous_time)
            self.previous_time = current_time
        except Exception as e:
            print(f"Error in camera feedback: {e}")

    def closeEvent(self, event):
        self.capture.release()
        event.accept()

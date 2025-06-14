from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QPushButton, QMessageBox, QLineEdit
)
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database import Database
from fiber_camera import FiberCamera

class UserInterface:
    def __init__(self) -> None:
        self.app = QApplication.instance() or QApplication([])
        self.window = QWidget()
        self.layout = QGridLayout()

        self.device_started = False
        self.start_motor_calibration = False
        self.camera_feedback_enabled = False
        self.dc_motor_close_loop_enabled = False

        # motor_setpoint 直接写死（比如30.0）
        self.motor_setpoint = 30.0

        self.diameter_plot = self.add_plots()
        self.target_diameter = self.add_diameter_controls()

        self.csv_filename = QLineEdit("Enter a file name")
        self.layout.addWidget(self.csv_filename, 24, 8)

        self.fiber_camera = FiberCamera(self.target_diameter, self)
        if self.fiber_camera.diameter_coefficient == -1:
            self.show_message("Camera calibration data not found", "Please calibrate the camera.")
            self.fiber_camera.diameter_coefficient = 0.00782324

        self.layout.addWidget(self.fiber_camera.raw_image, 2, 8, 6, 1)
        self.layout.addWidget(self.fiber_camera.processed_image, 9, 8, 6, 1)

        self.add_buttons()

        self.window.setLayout(self.layout)
        self.window.setWindowTitle("MIT FrED")
        self.window.setGeometry(100, 100, 1600, 1000)
        self.window.setFixedSize(1600, 1000)
        self.window.setAutoFillBackground(True)

    def add_plots(self):
        diameter_plot = self.Plot("Diameter", "Diameter (mm)")
        self.layout.addWidget(diameter_plot, 2, 0, 8, 4)
        return diameter_plot

    def add_diameter_controls(self):
        label = QLabel("Target Diameter (mm)")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        # 这里保留直径设定控件，如果不需要可以注释掉
        # spin = QDoubleSpinBox()
        # spin.setRange(0.3, 0.6)
        # spin.setValue(0.35)
        # spin.setSingleStep(0.01)
        # spin.setDecimals(2)
        # self.layout.addWidget(label, 16, 9)
        # self.layout.addWidget(spin, 17, 9)
        # return spin
        self.layout.addWidget(label, 16, 9)
        return None

    def add_buttons(self):
        self.create_button("Start Motor (Default 30RPM)", self.set_motor_close_loop, 1, 6, "motor_button")
        self.create_button("Start Ploting", self.set_camera_feedback, 1, 9)
        self.create_button("Start Heater (Default 95C)", self.set_start_device, 2, 6)
        self.create_button("Calibrate motor", self.set_calibrate_motor, 1, 1)
        self.create_button("Calibrate camera", self.set_calibrate_camera, 1, 2)
        self.create_button("Download CSV File", self.set_download_csv, 24, 6)
        self.create_button("Exit", self.exit_program, 24, 9)

    def create_button(self, text, handler, row, col, obj_attr_name=None):
        btn = QPushButton(text)
        btn.setStyleSheet("background-color: green; font-size: 14px; font-weight: bold;")
        btn.clicked.connect(handler)
        self.layout.addWidget(btn, row, col)
        if obj_attr_name:
            setattr(self, obj_attr_name, btn)

    def start_gui(self) -> None:
        timer = QTimer()
        timer.timeout.connect(self.fiber_camera.camera_loop)
        timer.start(200)
        self.window.show()
        self.app.exec_()

    def set_motor_close_loop(self) -> None:
        self.dc_motor_close_loop_enabled = not self.dc_motor_close_loop_enabled
        if self.dc_motor_close_loop_enabled:
            self.motor_button.setText("Stop Motor")
            # motor_setpoint 直接用默认值，无需再取控件值
            QMessageBox.information(self.window, "Motor Control", f"Motor closed loop started (setpoint={self.motor_setpoint}, Kp=0.4, Ki=0.2, Kd=0.05)")
        else:
            self.motor_button.setText("Start Motor (Default 30RPM)")
            QMessageBox.information(self.window, "Motor Control", "Motor closed loop stopped.")

    def set_camera_feedback(self) -> None:
        self.camera_feedback_enabled = not self.camera_feedback_enabled
        msg = "started" if self.camera_feedback_enabled else "stopped"
        QMessageBox.information(self.window, "Camera Feedback", f"Camera feedback {msg}.")

    def set_start_device(self) -> None:
        self.device_started = True
        QMessageBox.information(self.window, "Device Start", "Temperature closed loop started (setpoint=95, Kp=1.4, Ki=0.2, Kd=0.8, Fan=30%)")

    def set_calibrate_motor(self) -> None:
        self.start_motor_calibration = True
        QMessageBox.information(self.window, "Motor Calibration", "Motor is calibrating.")

    def set_calibrate_camera(self) -> None:
        QMessageBox.information(self.window, "Camera Calibration", "Camera is calibrating.")
        self.fiber_camera.calibrate()
        QMessageBox.information(self.window, "Calibration", "Camera calibration completed. Please restart the program.")

    def set_download_csv(self) -> None:
        QMessageBox.information(self.window, "Download CSV", "Downloading CSV file.")
        Database.generate_csv(self.csv_filename.text())

    def exit_program(self) -> None:
        self.window.close()
        self.app.quit()

    def show_message(self, title: str, message: str) -> None:
        QMessageBox.information(self.window, title, message)

    class Plot(FigureCanvas):
        def __init__(self, title: str, y_label: str) -> None:
            self.figure = Figure()
            self.axes = self.figure.add_subplot(111)
            super().__init__(self.figure)
            self.axes.set_title(title)
            self.axes.set_xlabel("Time (s)")
            self.axes.set_ylabel(y_label)
            self.progress_line, = self.axes.plot([], [], lw=2, label=title)
            self.setpoint_line, = self.axes.plot([], [], lw=2, color='r', label=f'Target {title}')
            self.axes.legend()
            self.x_data = []
            self.y_data = []
            self.setpoint_data = []

        def update_plot(self, x: float, y: float, setpoint: float) -> None:
            max_points = 100
            self.x_data.append(x)
            self.y_data.append(y)
            self.setpoint_data.append(setpoint)
            self.x_data = self.x_data[-max_points:]
            self.y_data = self.y_data[-max_points:]
            self.setpoint_data = self.setpoint_data[-max_points:]
            self.progress_line.set_data(self.x_data, self.y_data)
            self.setpoint_line.set_data(self.x_data, self.setpoint_data)
            self.axes.relim()
            self.axes.autoscale_view()
            self.draw()

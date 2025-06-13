"""File to setup the layout of the User Interface"""

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSlider, QPushButton, QMessageBox, QLineEdit, QCheckBox
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database import Database
from fiber_camera import FiberCamera

class UserInterface():
    """Graphical User Interface Class"""

    def __init__(self) -> None:
        self.app = QApplication([])
        self.window = QWidget()
        self.layout = QGridLayout()

        self.diameter_plot = self.add_plots()
        self.target_diameter = self.add_diameter_controls()
        self.extrusion_motor_speed = self.add_motor_controls()
        self.target_temperature_label, self.target_temperature = self.add_temperature_controls()
        self.fan_duty_cycle_label, self.fan_duty_cycle = self.add_fan_controls()

        # Hide temperature setpoint and fan duty cycle controls
        self.target_temperature_label.hide()
        self.target_temperature.hide()
        self.fan_duty_cycle_label.hide()
        self.fan_duty_cycle.hide()

        # Editable text box for the CSV file name
        self.csv_filename = QLineEdit()
        self.csv_filename.setText("Enter a file name")
        self.layout.addWidget(self.csv_filename, 24, 8)

        self.device_started = False
        self.start_motor_calibration = False
        self.camera_feedback_enabled = False
        self.dc_motor_close_loop_enabled = False

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
        """Add only the diameter plot to the layout"""
        font_style = "font-size: 16px; font-weight: bold;"
        binary_checkbox = QCheckBox("Binary")
        binary_checkbox.setStyleSheet(font_style)
        diameter_plot = self.Plot("Diameter", "Diameter (mm)")
        self.layout.addWidget(binary_checkbox, 10, 1)
        self.layout.addWidget(diameter_plot, 2, 0, 8, 4)
        return diameter_plot

    def add_diameter_controls(self):
        font_style = "font-size: %ipx; font-weight: bold;"
        target_diameter_label = QLabel("Target Diameter (mm)")
        target_diameter_label.setStyleSheet(font_style % 16)
        target_diameter = QDoubleSpinBox()
        target_diameter.setMinimum(0.3)
        target_diameter.setMaximum(0.6)
        target_diameter.setValue(0.35)
        target_diameter.setSingleStep(0.01)
        target_diameter.setDecimals(2)
        self.layout.addWidget(target_diameter_label, 16, 9)
        self.layout.addWidget(target_diameter, 17, 9)
        return target_diameter

    def add_motor_controls(self):
        font_style = "font-size: %ipx; font-weight: bold;"
        extrusion_motor_speed_label = QLabel("Extrusion Motor Speed (RPM)")
        extrusion_motor_speed_label.setStyleSheet(font_style % 16)
        extrusion_motor_speed = QDoubleSpinBox()
        extrusion_motor_speed.setMinimum(0.0)
        extrusion_motor_speed.setMaximum(20.0)
        extrusion_motor_speed.setValue(0.0)
        extrusion_motor_speed.setSingleStep(0.1)
        extrusion_motor_speed.setDecimals(2)
        self.layout.addWidget(extrusion_motor_speed_label, 11, 6)
        self.layout.addWidget(extrusion_motor_speed, 12, 6)
        return extrusion_motor_speed

    def add_temperature_controls(self):
        """Add UI controls for the temperature (no PID controls)"""
        font_style = "font-size: %ipx; font-weight: bold;"
        target_temperature_label = QLabel("Temperature Setpoint(C)")
        target_temperature_label.setStyleSheet(font_style % 16)
        target_temperature = QSlider(Qt.Horizontal)
        target_temperature.setMinimum(65)
        target_temperature.setMaximum(105)
        target_temperature.setValue(95)  # Default 95C
        target_temperature.valueChanged.connect(self.update_temperature_slider_label)
        self.layout.addWidget(target_temperature_label, 14, 6)
        self.layout.addWidget(target_temperature, 15, 6)
        return target_temperature_label, target_temperature

    def add_fan_controls(self):
        font_style = "font-size: %ipx; font-weight: bold;"
        fan_duty_cycle_label = QLabel("Fan Duty Cycle (%)")
        fan_duty_cycle_label.setStyleSheet(font_style % 14)
        fan_duty_cycle = QSlider(Qt.Horizontal)
        fan_duty_cycle.setMinimum(0)
        fan_duty_cycle.setMaximum(100)
        fan_duty_cycle.setValue(30)
        fan_duty_cycle.valueChanged.connect(self.update_fan_slider_label)
        self.layout.addWidget(fan_duty_cycle_label, 22, 6)
        self.layout.addWidget(fan_duty_cycle, 23, 6)
        return fan_duty_cycle_label, fan_duty_cycle

    def add_buttons(self):
        font_style = "background-color: green; font-size: 14px; font-weight: bold;"

        motor_close_loop = QPushButton("Start Motor (Default 30RPM)")
        motor_close_loop.setStyleSheet(font_style)
        motor_close_loop.clicked.connect(self.set_motor_close_loop)

        start_device = QPushButton("Start Heater (Default 95C)")
        start_device.setStyleSheet(font_style)
        start_device.clicked.connect(self.set_start_device)

        calibrate_motor = QPushButton("Calibrate motor")
        calibrate_motor.setStyleSheet(font_style)
        calibrate_motor.clicked.connect(self.set_calibrate_motor)

        calibrate_camera = QPushButton("Calibrate camera")
        calibrate_camera.setStyleSheet(font_style)
        calibrate_camera.clicked.connect(self.set_calibrate_camera)

        download_csv = QPushButton("Download CSV File")
        download_csv.setStyleSheet(font_style)
        download_csv.clicked.connect(self.set_download_csv)

        camera_feedback = QPushButton("Start Ploting")
        camera_feedback.setStyleSheet(font_style)
        camera_feedback.clicked.connect(self.set_camera_feedback)

        self.layout.addWidget(camera_feedback, 1, 9)
        self.layout.addWidget(motor_close_loop, 1, 6)
        self.layout.addWidget(start_device, 2, 6)
        self.layout.addWidget(calibrate_motor, 1, 1)
        self.layout.addWidget(calibrate_camera, 1, 2)
        self.layout.addWidget(download_csv, 24, 6)

    def start_gui(self) -> None:
        timer = QTimer()
        timer.timeout.connect(self.fiber_camera.camera_loop)
        timer.start(200)
        self.window.show()
        self.app.exec_()

    def set_motor_close_loop(self) -> None:
        self.dc_motor_close_loop_enabled = not self.dc_motor_close_loop_enabled
        if self.dc_motor_close_loop_enabled:
            # Default motor PID and setpoint
            setpoint = 30
            kp = 0.4
            ki = 0.2
            kd = 0.05
            # Use these in your control logic as needed
            QMessageBox.information(self.app.activeWindow(),
                                    "Motor Control",
                                    f"Motor close loop started (setpoint={setpoint}, Kp={kp}, Ki={ki}, Kd={kd})")
        else:
            QMessageBox.information(self.app.activeWindow(),
                                    "Motor Control",
                                    "Motor close loop control stopped.")

    def update_temperature_slider_label(self, value) -> None:
        self.target_temperature_label.setText(f"Temperature: {value} C")

    def update_fan_slider_label(self, value) -> None:
        self.fan_duty_cycle_label.setText(f"Fan Duty Cycle: {value} %")

    def set_camera_feedback(self) -> None:
        self.camera_feedback_enabled = not self.camera_feedback_enabled
        if self.camera_feedback_enabled:
            QMessageBox.information(self.app.activeWindow(),
                                    "Camera Feedback", "Camera feedback started.")
        else:
            QMessageBox.information(self.app.activeWindow(),
                                    "Camera Feedback", "Camera feedback stopped.")

    def set_start_device(self) -> None:
        # Default temperature PID and setpoint and fan duty cycle
        setpoint = 95
        kp = 1.4
        ki = 0.2
        kd = 0.8
        fan_duty_cycle = 30
        # Use these in your control logic as needed
        QMessageBox.information(self.app.activeWindow(), "Device Start",
                                f"Temperature close loop started (setpoint={setpoint}, Kp={kp}, Ki={ki}, Kd={kd}, Fan={fan_duty_cycle}%)")
        self.device_started = True

    def set_calibrate_motor(self) -> None:
        QMessageBox.information(self.app.activeWindow(), "Motor Calibration",
                                "Motor is calibrating.")
        self.start_motor_calibration = True

    def set_calibrate_camera(self) -> None:
        QMessageBox.information(self.app.activeWindow(), "Camera Calibration",
                                "Camera is calibrating.")
        self.fiber_camera.calibrate()
        QMessageBox.information(self.app.activeWindow(),
                                "Calibration", "Camera calibration completed. "
                                "Please restart the program.")

    def set_download_csv(self) -> None:
        QMessageBox.information(self.app.activeWindow(), "Download CSV",
                                "Downloading CSV file.")
        Database.generate_csv(self.csv_filename.text())

    def show_message(self, title: str, message: str) -> None:
        QMessageBox.information(self.app.activeWindow(), title, message)

    class Plot(FigureCanvas):
        def __init__(self, title: str, y_label: str) -> None:
            self.figure = Figure()
            self.axes = self.figure.add_subplot(111)
            super(UserInterface.Plot, self).__init__(self.figure)
            self.axes.set_title(title)
            self.axes.set_xlabel("Time (s)")
            self.axes.set_ylabel(y_label)
            self.progress_line, = self.axes.plot([], [], lw=2, label=title)
            self.setpoint_line, = self.axes.plot([], [], lw=2, color='r',
                                                 label=f'Target {title}')
            self.axes.legend()
            self.x_data = []
            self.y_data = []
            self.setpoint_data = []

        def update_plot(self, x: float, y: float, setpoint: float) -> None:
            self.x_data.append(x)
            self.y_data.append(y)
            self.setpoint_data.append(setpoint)
            self.progress_line.set_label(f"{self.axes.get_title()}: {y:.2f}")
            self.axes.legend()
            self.progress_line.set_data(self.x_data, self.y_data)
            self.setpoint_line.set_data(self.x_data, self.setpoint_data)
            self.axes.relim()
            self.axes.autoscale_view()
            self.draw()

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
        self.heater_open_loop_pwm_label, self.heater_open_loop_pwm = self.add_heater_open_loop_pwm_control()
        self.dc_motor_pwm_label, self.dc_motor_pwm = self.add_dc_motor_controls()

        # Editable text box for the CSV file name
        self.csv_filename = QLineEdit()
        self.csv_filename.setText("Enter a file name")
        self.layout.addWidget(self.csv_filename, 24, 8)

        self.device_started = False
        self.start_motor_calibration = False
        self.heater_open_loop_enabled = False
        self.dc_motor_open_loop_enabled = False
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

    def add_heater_open_loop_pwm_control(self):
        font_style = "font-size: %ipx; font-weight: bold;"
        heater_open_loop_pwm_label = QLabel("Heater Open Loop PWM (%)")
        heater_open_loop_pwm_label.setStyleSheet(font_style % 14)
        heater_open_loop_pwm = QDoubleSpinBox()
        heater_open_loop_pwm.setMinimum(0)
        heater_open_loop_pwm.setMaximum(100)
        heater_open_loop_pwm.setValue(0)
        heater_open_loop_pwm.setSingleStep(1)
        heater_open_loop_pwm.setDecimals(0)
        self.layout.addWidget(heater_open_loop_pwm_label, 3, 9)
        self.layout.addWidget(heater_open_loop_pwm, 4, 9)
        return heater_open_loop_pwm_label, heater_open_loop_pwm

    def add_dc_motor_controls(self):
        font_style = "font-size: %ipx; font-weight: bold;"
        dc_motor_pwm_label = QLabel("DC Motor PWM (%)")
        dc_motor_pwm_label.setStyleSheet(font_style % 14)
        dc_motor_pwm = QDoubleSpinBox()
        dc_motor_pwm.setMinimum(0)
        dc_motor_pwm.setMaximum(100)
        dc_motor_pwm.setValue(0)
        dc_motor_pwm.setSingleStep(1)
        dc_motor_pwm.setDecimals(0)
        self.layout.addWidget(dc_motor_pwm_label, 7, 9)
        self.layout.addWidget(dc_motor_pwm, 8, 9)
        return dc_motor_pwm_label, dc_motor_pwm

    def add_buttons(self):
        font_style = "background-color: green; font-size: 14px; font-weight: bold;"

        motor_close_loop = QPushButton("Start Motor Close Loop")
        motor_close_loop.setStyleSheet(font_style)
        motor_close_loop.clicked.connect(self.set_motor_close_loop)

        start_device = QPushButton("Start Temperature Close Loop")
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

        heater_open_loop = QPushButton("Start Heater Open Loop")
        heater_open_loop.setStyleSheet(font_style)
        heater_open_loop.clicked.connect(self.set_heater_open_loop)

        dc_motor_open_loop = QPushButton("Start DC Motor Open Loop")
        dc_motor_open_loop.setStyleSheet(font_style)
        dc_motor_open_loop.clicked.connect(self.set_dc_motor_open_loop)

        camera_feedback = QPushButton("Start camera feedback")
        camera_feedback.setStyleSheet(font_style)
        camera_feedback.clicked.connect(self.set_camera_feedback)

        self.layout.addWidget(camera_feedback, 9, 9)
        self.layout.addWidget(motor_close_loop, 2, 6)
        self.layout.addWidget(start_device, 13, 6)
        self.layout.addWidget(calibrate_motor, 1, 1)
        self.layout.addWidget(calibrate_camera, 1, 2)
        self.layout.addWidget(download_csv, 24, 6)
        self.layout.addWidget(heater_open_loop, 2, 9)
        self.layout.addWidget(dc_motor_open_loop, 6, 9)

    def start_gui(self) -> None:
        timer = QTimer()
        timer.timeout.connect(self.fiber_camera.camera_loop)
        timer.start(200)
        self.window.show()
        self.app.exec_()

    def set_heater_open_loop(self) -> None:
        if self.device_started:
            QMessageBox.warning(self.app.activeWindow(), "Control Error",
                                "Cannot start open loop control while close loop is running.\n"
                                "Please restart the program.")
            return
        self.heater_open_loop_enabled = not self.heater_open_loop_enabled
        if self.heater_open_loop_enabled:
            QMessageBox.information(self.app.activeWindow(),
                                    "Heater Control", "Heater open loop control started.")
        else:
            QMessageBox.information(self.app.activeWindow(),
                                    "Heater Control", "Heater open loop control stopped.")

    def set_dc_motor_open_loop(self) -> None:
        if self.dc_motor_close_loop_enabled:
            QMessageBox.warning(self.app.activeWindow(),
                                "Control Error",
                                "Cannot enable open loop control while close loop is active.\n"
                                "Please restart the program.")
            return
        self.dc_motor_open_loop_enabled = not self.dc_motor_open_loop_enabled
        if self.dc_motor_open_loop_enabled:
            QMessageBox.information(self.app.activeWindow(),
                                    "DC Motor Control",
                                    "DC Motor open loop control started.")
        else:
            QMessageBox.information(self.app.activeWindow(),
                                    "DC Motor Control",
                                    "DC Motor open loop control stopped.")

    def set_motor_close_loop(self) -> None:
        if self.dc_motor_open_loop_enabled:
            QMessageBox.warning(self.app.activeWindow(),
                                "Control Error",
                                "Cannot start Close Loop while Open Loop is running.\n"
                                "Please stop Open Loop control first.")
            return
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
        if self.heater_open_loop_enabled:
            QMessageBox.warning(self.app.activeWindow(),
                                "Control Error",
                                "Cannot start Close Loop while open loop control is running.\n"
                                "Please restart the program.")
            return
        # Default temperature PID and setpoint
        setpoint = 95
        kp = 1.4
        ki = 0.2
        kd = 0.8
        # Use these in your control logic as needed
        QMessageBox.information(self.app.activeWindow(), "Device Start",
                                f"Temperature close loop started (setpoint={setpoint}, Kp={kp}, Ki={ki}, Kd={kd})")
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

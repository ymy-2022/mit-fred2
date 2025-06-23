from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QPushButton,
    QMessageBox, QLineEdit, QCheckBox, QSlider
)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from database import Database
from fiber_camera import FiberCamera

class UserInterface:
    """
    Main user interface for the extrusion system.
    Provides controls for device operation, visualization, and camera.
    """
    def __init__(self) -> None:
        self.app = QApplication.instance() or QApplication([])
        self.window = QWidget()
        self.layout = QGridLayout()

        # Device control flag: True if device (heater+motor) is running
        self.device_started = False

        # Add plots and controls
        self.diameter_plot = self.add_plots()
        self.target_diameter = self.add_diameter_controls()

        # Target temperature display (not editable, for reference)
        self.target_temperature_label = QLabel("Target Temperature (°C)")
        self.target_temperature_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.target_temperature = QDoubleSpinBox()
        self.target_temperature.setRange(20.0, 300.0)
        self.target_temperature.setValue(95.0)
        self.target_temperature.setSingleStep(0.1)
        self.target_temperature.setDecimals(1)
        self.target_temperature.setReadOnly(True)
        self.layout.addWidget(self.target_temperature_label, 1, 7)
        self.layout.addWidget(self.target_temperature, 1, 8)

        # CSV filename input
        self.csv_filename = QLineEdit("Enter a file name")
        self.layout.addWidget(self.csv_filename, 22, 5, 1, 2)

        # Fiber camera setup
        self.fiber_camera = FiberCamera(self.target_diameter, self)
        if self.fiber_camera.diameter_coefficient == -1:
            self.show_message("Camera calibration data not found", "Please calibrate the camera.")
            self.fiber_camera.diameter_coefficient = 0.00782324

        # Raw and processed image labels and widgets
        raw_image_label = QLabel("Raw Image:")
        raw_image_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(raw_image_label, 10, 0, 1, 4)
        self.layout.addWidget(self.fiber_camera.raw_image, 11, 0, 6, 4)
        processed_image_label = QLabel("Processed Image:")
        processed_image_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(processed_image_label, 17, 0, 1, 4)
        self.layout.addWidget(self.fiber_camera.processed_image, 18, 0, 7, 4)

        # Add only one button to start/stop both heater and motor
        self.add_device_button(0, 5)

        # (Optional) Add other buttons as needed for calibration, plotting, CSV, etc.
        self.create_button("Calibrate camera", self.set_calibrate_camera, 0, 4)
        self.create_button("Start Plotting", self.set_camera_feedback, 0, 9)
        self.create_button("Download CSV File", self.set_download_csv, 22, 7)
        self.create_button("Exit", self.exit_program, 22, 9)

        # (Optional) Add camera/image processing controls here...

        # Set layout stretch for better appearance
        for col in range(10):
            self.layout.setColumnStretch(col, 1)
        for row in range(24):
            self.layout.setRowStretch(row, 1)

        self.window.setLayout(self.layout)
        self.window.setWindowTitle("MIT FrED")
        self.window.setGeometry(100, 100, 1600, 1000)
        self.window.setFixedSize(1600, 1000)
        self.window.setAutoFillBackground(True)

    def add_device_button(self, row, col):
        """
        Add a single button to start/stop the device (heater + motor).
        """
        self.device_button = QPushButton("Start Device")
        self.device_button.setStyleSheet("background-color: green; font-size: 14px; font-weight: bold;")
        self.device_button.setCheckable(True)
        self.device_button.clicked.connect(self.toggle_device)
        self.layout.addWidget(self.device_button, row, col)

    def toggle_device(self):
        """
        Toggle device operation. When started, both heater and motor run.
        """
        self.device_started = not self.device_started
        if self.device_started:
            self.device_button.setText("Stop Device")
            self.device_button.setStyleSheet("background-color: red; font-size: 14px; font-weight: bold;")
            QMessageBox.information(self.window, "Device Started", "Heater and motor started.")
        else:
            self.device_button.setText("Start Device")
            self.device_button.setStyleSheet("background-color: green; font-size: 14px; font-weight: bold;")
            QMessageBox.information(self.window, "Device Stopped", "Heater and motor stopped.")

    def create_button(self, text, handler, row, col, obj_attr_name=None):
        """
        Utility to add a generic button to the UI.
        """
        btn = QPushButton(text)
        btn.setStyleSheet("background-color: green; font-size: 14px; font-weight: bold;")
        btn.clicked.connect(handler)
        self.layout.addWidget(btn, row, col)
        if obj_attr_name:
            setattr(self, obj_attr_name, btn)

    def add_plots(self):
        """
        Add the diameter plot to the UI.
        """
        diameter_plot = self.Plot("Diameter", "Diameter (mm)")
        self.layout.addWidget(diameter_plot, 0, 0, 10, 4)
        return diameter_plot

    def add_diameter_controls(self):
        """
        Add target diameter controls (for camera feedback, not for extrusion control).
        """
        label = QLabel("Target Diameter (mm)")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        spin = QDoubleSpinBox()
        spin.setRange(0.3, 0.6)
        spin.setValue(0.35)
        spin.setSingleStep(0.01)
        spin.setDecimals(2)
        self.layout.addWidget(label, 0, 7)
        self.layout.addWidget(spin, 0, 8)
        return spin

    def start_gui(self) -> None:
        """
        Start the GUI event loop and camera feedback timer.
        """
        timer = QTimer()
        timer.timeout.connect(self.fiber_camera.camera_loop)
        timer.start(200)
        self.window.show()
        self.app.exec_()

    def set_camera_feedback(self) -> None:
        """
        Toggle camera feedback plotting.
        """
        self.camera_feedback_enabled = not getattr(self, "camera_feedback_enabled", False)
        msg = "started" if self.camera_feedback_enabled else "stopped"
        QMessageBox.information(self.window, "Camera Feedback", f"Camera feedback {msg}.")

    def set_calibrate_camera(self) -> None:
        """
        Calibrate the fiber camera.
        """
        QMessageBox.information(self.window, "Camera Calibration", "Camera is calibrating.")
        self.fiber_camera.calibrate()
        QMessageBox.information(self.window, "Calibration", "Camera calibration completed.")

    def set_download_csv(self) -> None:
        """
        Download CSV file with logged data.
        """
        QMessageBox.information(self.window, "Download CSV", "Downloading CSV file.")
        Database.generate_csv(self.csv_filename.text())

    def exit_program(self) -> None:
        """
        Exit the application.
        """
        self.window.close()
        self.app.quit()

    def show_message(self, title: str, message: str) -> None:
        """
        Utility to display a message box.
        """
        QMessageBox.information(self.window, title, message)

    class Plot(FigureCanvas):
        """
        Plot widget for displaying real-time data.
        """
        def __init__(self, title: str, y_label: str) -> None:
            self.figure = Figure()
            self.axes = self.figure.add_subplot(111)
            super().__init__(self.figure)
            self.figure.subplots_adjust(top=0.92)
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
            """
            Update the plot with new data points.
            """
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

# Import necessary widgets from PyQt5 for building the GUI[1].
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QPushButton,
    QMessageBox, QLineEdit, QCheckBox, QSlider
)
# Import QTimer for periodic actions and Qt for core constants[1].
from PyQt5.QtCore import QTimer, Qt
# Import FigureCanvas for embedding matplotlib plots in PyQt5[1].
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# Import Figure to create plots[1].
from matplotlib.figure import Figure

# Import custom Database module for saving/loading data[1].
from database import Database  # Custom module for saving/loading data
# Import custom FiberCamera class for camera processing[1].
from fiber_camera import FiberCamera  # Custom camera processing class

# Define the main user interface class[1].
class UserInterface:
    # Constructor for initializing the UI[1].
    def __init__(self) -> None:
        # Create the main application object, or get the existing one if already created[1].
        self.app = QApplication.instance() or QApplication([])

        # Create the main window widget[1].
        self.window = QWidget()
        # Set up a grid layout for organizing widgets[1].
        self.layout = QGridLayout()

        # State flag: True after device start button is pressed[1].
        self.device_started = False
        # State flag: Used for motor calibration (not shown in this code)[1].
        self.start_motor_calibration = False
        # State flag: True if camera feedback is running[1].
        self.camera_feedback_enabled = False
        # State flag: True if motor closed-loop control is on[1].
        self.dc_motor_close_loop_enabled = False

        # Default RPM for the motor (30.0 means 30 revolutions per minute)[1].
        self.motor_setpoint = 30.0

        # Add the live plot for diameter and store the plot object[1].
        self.diameter_plot = self.add_plots()

        # Add the spin box for setting the target diameter[1].
        self.target_diameter = self.add_diameter_controls()

        # Text box for user to enter a CSV file name for downloads[1].
        self.csv_filename = QLineEdit("Enter a file name")
        # Add the text box to the layout at row 22, column 5, spanning 1 row and 2 columns[1].
        self.layout.addWidget(self.csv_filename, 22, 5, 1, 2)

        # Set up the camera object, passing the spin box and this UI instance[1].
        self.fiber_camera = FiberCamera(self.target_diameter, self)

        # If camera calibration data is not found, show a message and set a default value[1].
        if self.fiber_camera.diameter_coefficient == -1:
            self.show_message("Camera calibration data not found", "Please calibrate the camera.")
            # Default calibration coefficient for diameter measurement[1].
            self.fiber_camera.diameter_coefficient = 0.00782324

        # Add label for raw image display[1].
        raw_image_label = QLabel("Raw Image:")
        # Set label style to bold and larger font[1].
        raw_image_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        # Add the label to the layout at row 10, column 0, spanning 1 row and 4 columns[1].
        self.layout.addWidget(raw_image_label, 10, 0, 1, 4)
        # Add the raw image widget to the layout at row 11, column 0, spanning 6 rows and 4 columns[1].
        self.layout.addWidget(self.fiber_camera.raw_image, 11, 0, 6, 4)

        # Add label for processed image display[1].
        processed_image_label = QLabel("Processed Image:")
        # Set label style to bold and larger font[1].
        processed_image_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        # Add the label to the layout at row 17, column 0, spanning 1 row and 4 columns[1].
        self.layout.addWidget(processed_image_label, 17, 0, 1, 4)
        # Add the processed image widget to the layout at row 18, column 0, spanning 7 rows and 4 columns[1].
        self.layout.addWidget(self.fiber_camera.processed_image, 18, 0, 7, 4)

        # Add all main control buttons to the layout[1].
        self.add_buttons()

        # Add checkboxes to enable/disable image processing filters[1].
        self.erode_checkbox = QCheckBox("Enable Erode Filter")
        # Default: erode filter enabled[1].
        self.erode_checkbox.setChecked(True)
        # Connect checkbox state change to handler function[1].
        self.erode_checkbox.stateChanged.connect(self.toggle_erode_filter)
        # Add checkbox to layout at row 12, column 6, spanning 1 row and 2 columns[1].
        self.layout.addWidget(self.erode_checkbox, 12, 6, 1, 2)

        self.dilate_checkbox = QCheckBox("Enable Dilate Filter")
        self.dilate_checkbox.setChecked(True)
        self.dilate_checkbox.stateChanged.connect(self.toggle_dilate_filter)
        self.layout.addWidget(self.dilate_checkbox, 13, 6, 1, 2)

        self.gaussian_checkbox = QCheckBox("Enable Gaussian Blur")
        self.gaussian_checkbox.setChecked(True)
        self.gaussian_checkbox.stateChanged.connect(self.toggle_gaussian_filter)
        self.layout.addWidget(self.gaussian_checkbox, 14, 6, 1, 2)

        self.binary_checkbox = QCheckBox("Enable Binary Threshold")
        self.binary_checkbox.setChecked(True)
        self.binary_checkbox.stateChanged.connect(self.toggle_binary_filter)
        self.layout.addWidget(self.binary_checkbox, 15, 6, 1, 2)

        # Add sliders for Canny edge detection thresholds and Hough line threshold[1].
        # Canny Lower Threshold slider: detects faint edges; range 0-150, default 100[1].
        self.canny_lower_slider = QSlider(Qt.Horizontal)
        self.canny_lower_slider.setRange(0, 150)  # Minimum 0, maximum 150
        self.canny_lower_slider.setSingleStep(5)  # Step size is 5
        self.canny_lower_slider.setTickInterval(5)  # Tick marks every 5 units
        self.canny_lower_slider.setValue(100)  # Default value is 100
        self.canny_lower_slider.valueChanged.connect(self.update_canny_lower)
        self.canny_lower_value_label = QLabel(str(self.canny_lower_slider.value()))
        self.layout.addWidget(QLabel("Canny Lower"), 16, 5, 1, 1)
        self.layout.addWidget(self.canny_lower_slider, 16, 6, 1, 2)
        self.layout.addWidget(self.canny_lower_value_label, 16, 8)

        # Canny Upper Threshold slider: detects strong edges; range 150-300, default 250[1].
        self.canny_upper_slider = QSlider(Qt.Horizontal)
        self.canny_upper_slider.setRange(150, 300)  # Minimum 150, maximum 300
        self.canny_upper_slider.setSingleStep(5)  # Step size is 5
        self.canny_upper_slider.setTickInterval(5)  # Tick marks every 5 units
        self.canny_upper_slider.setValue(250)  # Default value is 250
        self.canny_upper_slider.valueChanged.connect(self.update_canny_upper)
        self.canny_upper_value_label = QLabel(str(self.canny_upper_slider.value()))
        self.layout.addWidget(QLabel("Canny Upper"), 17, 5, 1, 1)
        self.layout.addWidget(self.canny_upper_slider, 17, 6, 1, 2)
        self.layout.addWidget(self.canny_upper_value_label, 17, 8)

        # Hough Threshold slider: minimum points to detect a line; range 10-100, default 30[1].
        self.hough_threshold_slider = QSlider(Qt.Horizontal)
        self.hough_threshold_slider.setRange(10, 100)  # Minimum 10, maximum 100
        self.hough_threshold_slider.setSingleStep(5)  # Step size is 5
        self.hough_threshold_slider.setTickInterval(5)  # Tick marks every 5 units
        self.hough_threshold_slider.setValue(30)  # Default value is 30
        self.hough_threshold_slider.valueChanged.connect(self.update_hough_threshold)
        self.hough_threshold_value_label = QLabel(str(self.hough_threshold_slider.value()))
        self.layout.addWidget(QLabel("Hough Threshold"), 18, 5, 1, 1)
        self.layout.addWidget(self.hough_threshold_slider, 18, 6, 1, 2)
        self.layout.addWidget(self.hough_threshold_value_label, 18, 8)

        # Stretch columns and rows for responsive layout[1].
        for col in range(10):  # 10 columns
            self.layout.setColumnStretch(col, 1)
        for row in range(24):  # 24 rows
            self.layout.setRowStretch(row, 1)

        # Final window settings[1].
        self.window.setLayout(self.layout)
        self.window.setWindowTitle("MIT FrED")  # Set window title
        self.window.setGeometry(100, 100, 1600, 1000)  # Position (100,100), size 1600x1000
        self.window.setFixedSize(1600, 1000)  # Prevent resizing
        self.window.setAutoFillBackground(True)  # Ensures background is painted

    # Functions to update parameters in FiberCamera when sliders move[1].
    def update_canny_lower(self, value):
        self.fiber_camera.canny_lower = value  # Update Canny lower threshold
        self.canny_lower_value_label.setText(str(value))  # Update label

    def update_canny_upper(self, value):
        self.fiber_camera.canny_upper = value  # Update Canny upper threshold
        self.canny_upper_value_label.setText(str(value))  # Update label

    def update_hough_threshold(self, value):
        self.fiber_camera.hough_threshold = value  # Update Hough threshold
        self.hough_threshold_value_label.setText(str(value))  # Update label

    # Functions to enable/disable image processing filters[1].
    def toggle_erode_filter(self, state):
        FiberCamera.use_erode = (state == 2)  # 2 means checked

    def toggle_dilate_filter(self, state):
        FiberCamera.use_dilate = (state == 2)

    def toggle_gaussian_filter(self, state):
        FiberCamera.use_gaussian = (state == 2)

    def toggle_binary_filter(self, state):
        FiberCamera.use_binary = (state == 2)

    # Add the diameter plot to the layout[1].
    def add_plots(self):
        diameter_plot = self.Plot("Diameter", "Diameter (mm)")
        # Add plot to layout at row 0, column 0, spanning 10 rows and 4 columns[1].
        self.layout.addWidget(diameter_plot, 0, 0, 10, 4)
        return diameter_plot

    # Add the spin box for setting target diameter[1].
    def add_diameter_controls(self):
        label = QLabel("Target Diameter (mm)")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        spin = QDoubleSpinBox()
        spin.setRange(0.3, 0.6)  # Only allow values between 0.3 and 0.6 mm (typical fiber range)
        spin.setValue(0.35)  # Default value is 0.35 mm
        spin.setSingleStep(0.01)  # Step size is 0.01 mm
        spin.setDecimals(2)  # Show 2 decimal places
        self.layout.addWidget(label, 0, 7)
        self.layout.addWidget(spin, 0, 8)
        return spin

    # Add all the main buttons to the layout[1].
    def add_buttons(self):
        self.create_button("Calibrate camera", self.set_calibrate_camera, 0, 4)
        self.create_button("Start Motor (Default 30RPM)", self.set_motor_close_loop, 0, 5, "motor_button")
        self.create_button("Start Heater (Default 95C)", self.set_start_device, 0, 6)
        self.create_button("Start Ploting", self.set_camera_feedback, 0, 9)
        self.create_button("Download CSV File", self.set_download_csv, 22, 7)
        self.create_button("Exit", self.exit_program, 22, 9)

    # Helper to create a button and add it to the layout[1].
    def create_button(self, text, handler, row, col, obj_attr_name=None):
        btn = QPushButton(text)
        btn.setStyleSheet("background-color: green; font-size: 14px; font-weight: bold;")
        btn.clicked.connect(handler)
        self.layout.addWidget(btn, row, col)
        if obj_attr_name:  # Save a reference if needed
            setattr(self, obj_attr_name, btn)

    # Start the GUI event loop and camera update timer[1].
    def start_gui(self) -> None:
        timer = QTimer()
        timer.timeout.connect(self.fiber_camera.camera_loop)
        timer.start(200)  # Update every 200 ms (5 FPS, smooth and not too CPU-heavy)
        self.window.show()
        self.app.exec_()

    # Button callback: start/stop motor closed-loop control[1].
    def set_motor_close_loop(self) -> None:
        self.dc_motor_close_loop_enabled = not self.dc_motor_close_loop_enabled
        if self.dc_motor_close_loop_enabled:
            self.motor_button.setText("Stop Motor")
            # Show message: setpoint=30, Kp=0.4, Ki=0.2, Kd=0.05 are PID controller parameters[1].
            QMessageBox.information(self.window, "Motor Control", f"Motor closed loop started (setpoint={self.motor_setpoint}, Kp=0.4, Ki=0.2, Kd=0.05)")
        else:
            self.motor_button.setText("Start Motor (Default 30RPM)")
            QMessageBox.information(self.window, "Motor Control", "Motor closed loop stopped.")

    # Button callback: start/stop camera feedback[1].
    def set_camera_feedback(self) -> None:
        self.camera_feedback_enabled = not self.camera_feedback_enabled
        msg = "started" if self.camera_feedback_enabled else "stopped"
        QMessageBox.information(self.window, "Camera Feedback", f"Camera feedback {msg}.")

    # Button callback: start the device (heater)[1].
    def set_start_device(self) -> None:
        self.device_started = True
        # Show message: setpoint=95, Kp=1.4, Ki=0.2, Kd=0.8, Fan=30% are PID and fan parameters[1].
        QMessageBox.information(self.window, "Device Start", "Temperature closed loop started (setpoint=95, Kp=1.4, Ki=0.2, Kd=0.8, Fan=30%)")

    # Button callback: calibrate the camera[1].
    def set_calibrate_camera(self) -> None:
        QMessageBox.information(self.window, "Camera Calibration", "Camera is calibrating.")
        self.fiber_camera.calibrate()
        QMessageBox.information(self.window, "Calibration", "Camera calibration completed.")

    # Button callback: download data as CSV[1].
    def set_download_csv(self) -> None:
        QMessageBox.information(self.window, "Download CSV", "Downloading CSV file.")
        Database.generate_csv(self.csv_filename.text())

    # Button callback: exit the program[1].
    def exit_program(self) -> None:
        self.window.close()
        self.app.quit()

    # Show a popup message[1].
    def show_message(self, title: str, message: str) -> None:
        QMessageBox.information(self.window, title, message)

    # Inner class for plotting diameter data[1].
    class Plot(FigureCanvas):
        def __init__(self, title: str, y_label: str) -> None:
            self.figure = Figure()
            self.axes = self.figure.add_subplot(111)
            super().__init__(self.figure)
            self.figure.subplots_adjust(top=0.92)  # Leave space for title
            self.axes.set_title(title)
            self.axes.set_xlabel("Time (s)")
            self.axes.set_ylabel(y_label)
            # Line for actual diameter data[1].
            self.progress_line, = self.axes.plot([], [], lw=2, label=title)
            # Line for target diameter (setpoint)[1].
            self.setpoint_line, = self.axes.plot([], [], lw=2, color='r', label=f'Target {title}')
            self.axes.legend()
            self.x_data = []
            self.y_data = []
            self.setpoint_data = []

        # Update the plot with new data[1].
        def update_plot(self, x: float, y: float, setpoint: float) -> None:
            max_points = 100  # Only show the last 100 points for clarity
            self.x_data.append(x)
            self.y_data.append(y)
            self.setpoint_data.append(setpoint)
            self.x_data = self.x_data[-max_points:]
            self.y_data = self.y_data[-max_points:]
            self.setpoint_data = self.setpoint_data[-max_points:]
            self.progress_line.set_data(self.x_data, self.y_data)
            self.setpoint_line.set_data(self.x_data, self.setpoint_data)
            self.axes.relim()  # Recalculate limits
            self.axes.autoscale_view()  # Autoscale axes
            self.draw()  # Redraw the plot

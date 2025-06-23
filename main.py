"""Main file to run the FrED device"""
import threading
import time
import RPi.GPIO as GPIO
from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from database import Database
from user_interface import UserInterface
from fan import Fan
from spooler import Spooler
from extruder import Extruder

class GuiErrorSignaller(QObject):
    # Signal for thread-safe error reporting
    error_signal = pyqtSignal(str, str)

def hardware_control(gui: UserInterface, error_signaller: GuiErrorSignaller) -> None:
    """Thread to handle hardware control"""
    time.sleep(1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    try:
        fan = Fan(gui)
        spooler = Spooler(gui)
        extruder = Extruder(gui)
        fan.start(1000, 45)
        spooler.start(1000, 0)
    except Exception as e:
        print(f"Error in hardware control: {e}")
        error_signaller.error_signal.emit("Error while starting the device", "Please restart the program.")
        return

    init_time = time.time()
    while True:
        try:
            current_time = time.time() - init_time
            Database.time_readings.append(current_time)
            if gui.start_motor_calibration:
                spooler.calibrate()
                gui.start_motor_calibration = False

            if gui.dc_motor_close_loop_enabled:
                spooler.dc_motor_close_loop_control(current_time)

            if gui.device_started:
                extruder.temperature_control_loop(current_time)
                extruder.stepper_control_loop()

            if gui.camera_feedback_enabled:
                gui.fiber_camera.camera_feedback(current_time)

            fan.control_loop()
            time.sleep(0.05)
        except Exception as e:
            print(f"Error in hardware control loop: {e}")
            error_signaller.error_signal.emit("Error in hardware control loop", "Please restart the program.")
            try:
                fan.stop()
                spooler.stop()
                extruder.stop()
            except Exception:
                pass
            break

if __name__ == "__main__":
    print("Starting FrED Device...")
    ui = UserInterface()
    error_signaller = GuiErrorSignaller()
    # Connect the error signal to the GUI's show_message method
    error_signaller.error_signal.connect(ui.show_message)

    time.sleep(2)
    hardware_thread = threading.Thread(target=hardware_control, args=(ui, error_signaller), daemon=True)
    hardware_thread.start()
    ui.start_gui()
    # No need to join the thread; GUI will close the app
    print("FrED Device Closed.")

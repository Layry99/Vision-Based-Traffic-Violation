import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QScrollArea, QDialog, QPushButton, QMessageBox
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QScrollArea, QDialog, QPushButton
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt5 import uic, QtSql
from PyQt5.QtGui import QPixmap, QImage
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import time

class ImageViewer(QDialog):
    def __init__(self, image_data):
        super().__init__()
        self.setWindowTitle("Image Viewer")
        layout = QVBoxLayout()
        self.label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.label.setPixmap(pixmap)
        layout.addWidget(self.label)
        self.setLayout(layout)

def open_image_viewer(image_data):
    image_viewer = ImageViewer(image_data)
    image_viewer.exec_()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    new_violation_detected_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._run_flag = True

        # Load the YOLOv8 model
        self.model = YOLO('yolov8n.pt').cuda()

        # Video path
        self.video_path = r"C:\Users\User\Desktop\Python-Project (Optimized)\Drone Video\Day Footage\Drone-1.mp4" #uncomment this if wanted to use recorded video

        #Drone-1 coordinates
        self.line_coords = np.array([[18, 338],[742, 338]])
        
        # Font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 2
        self.font_color = (255, 255, 255)  # White color

        # Set to store track IDs of vehicles that have triggered a violation
        self.captured_vehicles = set()

        # Store the track history
        self.track_history = defaultdict(lambda: [])
        # Store the start time for each detected car in the violation zone
        self.start_times = {}

    def run(self):
        # Create a database connection
        conn = sqlite3.connect('violation-database.db')
        cursor = conn.cursor()

        # Create table to store violations if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS violations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp DATETIME,
                      image BLOB)''')

        cap = cv2.VideoCapture(self.video_path) # use this if recorded video
        #cap = cv2.VideoCapture(0) # use this if live webcam
        while self._run_flag and cap.isOpened():
            success, frame = cap.read()
            if success:
                frame = self.process_frame(frame, cursor, conn)
                self.change_pixmap_signal.emit(frame)
            else:
                break
        cap.release()
        conn.close()

    def stop(self):
        self._run_flag = False
        self.wait()

    def process_frame(self, frame, cursor, conn):
        frame = cv2.resize(frame, (768, 432))

        results = self.model.track(frame, classes=[2, 3], persist=True)

        annotated_frame = frame.copy()

        # Initialize counters for cars and motorcycles
        car_count = 0
        motorcycle_count = 0

        # Check if any objects are detected
        if results is not None and results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            classes = results[0].boxes.cls.int().cpu().tolist()  # Get class IDs
            annotated_frame = results[0].plot()

            # Draw the green line on the annotated frame
            cv2.line(annotated_frame, tuple(self.line_coords[0]), tuple(self.line_coords[1]), (0, 255, 0), 2)

            for box, track_id, cls in zip(boxes, track_ids, classes):
                x, y, w, h = box

                # Increment counters based on class ID
                if cls == 2:  # Car
                    car_count += 1
                elif cls == 3:  # Motorcycle
                    motorcycle_count += 1

                if self.is_within_line(float(x), float(y), w, h):
                    if track_id not in self.start_times:
                        self.start_times[track_id] = time.time()
                    else:
                        elapsed_time = time.time() - self.start_times[track_id]
                        cv2.putText(annotated_frame, f"Time: {elapsed_time:.2f} s", (int(x), int(y) - 10), self.font, self.font_scale, self.font_color, self.font_thickness)
                        if elapsed_time > 50:
                            cv2.putText(annotated_frame, "Violation Detected", (50, 50), self.font, self.font_scale, (0, 0, 255), self.font_thickness)
                            if track_id not in self.captured_vehicles:
                                img_encoded = cv2.imencode('.jpg', frame)[1].tobytes()
                                timestamp = datetime.now().replace(microsecond=0)
                                cursor.execute("INSERT INTO violations (timestamp, image) VALUES (?, ?)", (timestamp, sqlite3.Binary(img_encoded)))
                                conn.commit()
                                self.captured_vehicles.add(track_id)
                                self.new_violation_detected_signal.emit()
                else:
                    # Reset start time if the vehicle moves out of the line
                    if track_id in self.start_times:
                        del self.start_times[track_id]

        else:
            # Draw the green line on the original frame if no objects are detected
            cv2.line(annotated_frame, tuple(self.line_coords[0]), tuple(self.line_coords[1]), (0, 255, 0), 2)

        # Display the counts of cars and motorcycles on the annotated frame at the top-right corner
        cv2.putText(annotated_frame, f"Cars: {car_count}", (annotated_frame.shape[1] - 120, 20), self.font, self.font_scale, (0, 255, 0), self.font_thickness)
        cv2.putText(annotated_frame, f"Motorcycles: {motorcycle_count}", (annotated_frame.shape[1] - 120, 40), self.font, self.font_scale, (0, 255, 0), self.font_thickness)

        current_time = datetime.now().strftime("%d/%m/%Y   %H:%M:%S")
        cv2.putText(annotated_frame, current_time, (20, frame.shape[0] - 20), self.font, self.font_scale, self.font_color, self.font_thickness)

        return annotated_frame

    def is_within_line(self, x, y, w, h):
        # Calculate the top, bottom, left, and right coordinates of the bounding box
        top_y = y - (h / 2)
        bottom_y = y + (h / 2)
        left_x = x - (w / 2)
        right_x = x + (w / 2)

        # Extract y-coordinate of the horizontal line
        line_y = self.line_coords[0][1]

        # Check if the top or bottom edge of the bounding box intersects with the line
        intersects_top = top_y <= line_y <= bottom_y
        intersects_bottom = top_y <= line_y <= bottom_y

        # Ensure any part of the bounding box is within the x-range of the line
        x1, x2 = self.line_coords[0][0], self.line_coords[1][0]
        within_x_range = (x1 <= left_x <= x2) or (x1 <= right_x <= x2) or (left_x <= x1 and right_x >= x2)

        return (intersects_top or intersects_bottom) and within_x_range


    def point_line_distance(self, x, y, x1, y1, x2, y2):
        # Calculate the distance from point (x, y) to the line segment (x1, y1)-(x2, y2)
        num = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
        den = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return num / den

class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()
        uic.loadUi("gui.ui", self)
        self.show()

        self.setWindowTitle("Vision-Based Traffic Violation Detection")

        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.new_violation_detected_signal.connect(self.display_database_data)  # Connect to display_database_data
        self.thread.start()

        # Store the current scroll position
        self.scroll_position = 0

        # Connect the valueChanged signal of the vertical scroll bar to store_scroll_position method
        scroll_area = self.ViolationDB.findChild(QScrollArea)
        if scroll_area:
            self.scroll_bar = scroll_area.verticalScrollBar()
            self.scroll_bar.valueChanged.connect(self.store_scroll_position)

        # Display database data
        self.display_database_data()

        # Setup QTimer to refresh database data every 10 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.display_database_data)
        self.timer.start(10000)  # 10 seconds interval

    def closeEvent(self, event):
        self.thread.stop()
        self.timer.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.video_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(768, 432, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def display_database_data(self):
        # Create QSqlDatabase instance outside the function to ensure it's only created once
        db = QtSql.QSqlDatabase.database()
        if not db.isValid():
            db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName("violation-database.db")
        
        if not db.open():
            print("Failed to open database")
            return

        # Prepare a query to fetch data
        query = QtSql.QSqlQuery()
        query.exec_("SELECT id, timestamp, image FROM violations")

        # Check if ViolationDB has a layout before attempting to delete it
        if self.ViolationDB.layout():
            self.ViolationDB.layout().deleteLater()

        # Create a container widget for the scroll area
        scroll_container = QWidget()

        # Create a layout for the container widget
        container_layout = QVBoxLayout(scroll_container)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)

        # Display fetched data in QLabel inside the scroll area
        while query.next():
            id = query.value(0)
            timestamp = query.value(1)
            image_data = query.value(2)

            # Convert QByteArray to QPixmap
            image = QPixmap()
            image.loadFromData(image_data)

            # Resize the image
            max_width = 370
            max_height = 370
            image = image.scaled(max_width, max_height, Qt.KeepAspectRatio)

            # Create a container widget for each item
            item_container = QWidget()
            item_layout = QVBoxLayout(item_container)

            # Create QLabel to display the image
            image_label = QLabel()
            image_label.setPixmap(image)
            item_layout.addWidget(image_label)

            # Create QLabel to display ID and timestamp
            info_label = QLabel(f"ID: {id}, Timestamp: {timestamp}\n")
            item_layout.addWidget(info_label)

            # Create QPushButton for delete action
            delete_button = QPushButton("Delete this record ?")
            delete_button.clicked.connect(lambda _, id=id: self.delete_image(id))
            item_layout.addWidget(delete_button)

            # Create a larger image viewer window
            def open_image_viewer(image_data):
                image_viewer = ImageViewer(image_data)
                image_viewer.exec_()

            # Connect the clicked signal of the image label to open the larger image viewer window
            image_label.mousePressEvent = lambda event, image_data=image_data: open_image_viewer(image_data)

            # Add item container to scroll layout
            scroll_layout.addWidget(item_container)

        # Set maximum size for the scroll area
        scroll_area.setMaximumSize(431, 371)

        # Add scroll area to the container layout
        container_layout.addWidget(scroll_area)

        # Add the scroll container to the main layout
        self.ViolationDB.setLayout(container_layout)

        # Restore the vertical scroll position
        if hasattr(self, 'scroll_bar'):
            self.scroll_bar.setValue(self.scroll_position)

        # Close the default connection after use
        db.close()

    def delete_image(self, id):
        confirmation = QMessageBox.question(self, 'Confirm Deletion ?', 
                                            'Are you sure you want to delete this image?', 
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirmation == QMessageBox.Yes:
            # Create a QSqlDatabase instance outside the function to ensure it's only created once
            db = QtSql.QSqlDatabase.database()
            if not db.isValid():
                db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
                db.setDatabaseName("violation-database.db")

            if not db.open():
                print("Failed to open database")
                return

            query = QtSql.QSqlQuery()
            query.prepare("DELETE FROM violations WHERE id = :id")
            query.bindValue(":id", id)

            if query.exec_():
                print("Image deleted successfully")
                self.display_database_data()
            else:
                print("Failed to delete image")

            # Close the database connection after use
            db.close()
        else:
            print("Deletion canceled")

    def store_scroll_position(self, value):
        # Store the current scroll position
        self.scroll_position = value

def main():
    app = QApplication([])
    window = GUI()
    return app.exec_()

if __name__ == '__main__':
    main()

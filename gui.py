
import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

# Check if tensorflow is installed
try:
    import tensorflow as tf
except ImportError:
    print("TensorFlow not found. Please install it using: pip install tensorflow")
    sys.exit()

class PredictionGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thumbnail Predictor")
        self.setGeometry(100, 100, 400, 400)

        # --- Model Loading ---
        try:
            self.model = tf.keras.models.load_model('thumbnail_selector.keras')
        except (IOError, ImportError):
            self.result_label = QLabel("Model 'thumbnail_selector.keras' not found. Please run the training script.")
            self.result_label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(self.result_label)
            self.setLayout(layout)
            return

        # --- Image Dimensions ---
        self.image_height = 128
        self.image_width = 128

        # --- Widgets ---
        self.image_label = QLabel("Select a folder to start")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(380, 250)

        self.select_folder_button = QPushButton("Select Folder")
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.image_info_label = QLabel("Image: 0/0")
        self.image_info_label.setAlignment(Qt.AlignCenter)
        self.result_label = QLabel("Prediction: ")
        self.result_label.setAlignment(Qt.AlignCenter)

        self.process_folder_button = QPushButton("Process and Delete Bad Images")
        self.progress_bar = QProgressBar()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        # --- Layout ---
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.image_info_label)
        nav_layout.addWidget(self.next_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.select_folder_button)
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.result_label)
        main_layout.addWidget(self.process_folder_button)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.log_text)

        self.setLayout(main_layout)

        # --- Connections ---
        self.select_folder_button.clicked.connect(self.select_folder)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.process_folder_button.clicked.connect(self.process_folder)

        self.image_files = []
        self.current_image_index = -1

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            import os
            import glob
            self.image_files = []
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                self.image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if self.image_files:
                self.current_image_index = 0
                self.show_image()
            else:
                self.image_label.setText("No images found in the selected folder.")
                self.image_info_label.setText("Image: 0/0")
            self.log_text.clear()

    def show_image(self):
        if 0 <= self.current_image_index < len(self.image_files):
            image_path = self.image_files[self.current_image_index]
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.image_info_label.setText(f"Image: {self.current_image_index + 1}/{len(self.image_files)}")
            self.predict_image(image_path)

    def next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.show_image()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_image()

    def process_folder(self):
        if not self.image_files:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        self.select_folder_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.process_folder_button.setEnabled(False)

        self.progress_bar.setMaximum(len(self.image_files))
        deleted_count = 0
        self.log_text.clear()

        for i, image_path in enumerate(self.image_files):
            self.progress_bar.setValue(i + 1)
            try:
                img = tf.keras.utils.load_img(
                    image_path, target_size=(self.image_height, self.image_width)
                )
                img_array = tf.keras.utils.img_to_array(img)
                img_array = tf.expand_dims(img_array, 0) # Create a batch
                
                predictions = self.model.predict(img_array)
                score = predictions[0][0]

                if score <= 0.5:
                    import os
                    os.remove(image_path)
                    self.log_text.append(f"Deleted: {os.path.basename(image_path)}")
                    deleted_count += 1

            except Exception as e:
                self.log_text.append(f"Error processing {os.path.basename(image_path)}: {e}")

        self.select_folder_button.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.process_folder_button.setEnabled(True)

        QMessageBox.information(self, "Process Complete", f"Processed {len(self.image_files)} images.\nDeleted {deleted_count} 'bad' images.")

        # Refresh file list
        self.select_folder()

        if score > 0.5:
            prediction_text = f"good ({100 * score:.2f}% confidence)"
        else:
            prediction_text = f"bad ({100 * (1 - score):.2f}% confidence)"

        self.result_label.setText(f"Prediction: {prediction_text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PredictionGUI()
    gui.show()
    sys.exit(app.exec())

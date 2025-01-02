import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QSize

class ImageWithTextOverlay(QWidget):
    def __init__(self, image_path, text_data, parent=None):
        """
        Initialize the widget.

        :param image_path: Path to the image file.
        :param text_data: A dictionary containing text and their positions. Format:
                          {"kp": ("Kp: 1.0", (320, 215)),
                           "ki": ("Ki: 0.1", (320, 235)),
                           "kd": ("Kd: 0.01", (320, 255)),
                           "set_point": ("SP: 5.0", (160, 225)),
                           "error": ("Error: 0.5", (242, 200)),
                           "height": ("y: 2.0", (625, 200)),
                           "voltage": ("u: 5.0", (380, 210)),
                           "flow_rate": ("Qin: 13.5", (440, 200))}
        """
        super().__init__(parent)

        self.image_path = image_path
        self.text_data = text_data

        self.original_size = QSize(800, 600)  # Base size for scaling
        self.initUI()

    def initUI(self):
        # Set layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Label to display the image with text overlay
        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        # Load and display the image with overlay
        self.update_image()

        self.image_label.setScaledContents(True)  # Ensure the image scales with the widget size
        self.image_label.resizeEvent = self.handle_resize  # Overwrite resizeEvent for dynamic scaling

    def params(self, new_data):
        self.text_data = new_data
        self.update_image()

    def update_image(self):
        # Load the image
        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():  # Check if the image was loaded correctly
            print(f"Error: Unable to load image '{self.image_path}'")
            return

        self.original_pixmap = pixmap  # Store the original pixmap for scaling

        self.render_image()

    def render_image(self):
        # Scale the pixmap to match the label's current size
        scaled_pixmap = self.original_pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Create a painter to draw text on the image
        painter = QPainter(scaled_pixmap)
        if not painter.isActive():  # Ensure the painter is active
            print("Error: Painter not active")
            return

        painter.setRenderHint(QPainter.Antialiasing)

        # Set font and color
        scale_factor_x = scaled_pixmap.width() / self.original_size.width()
        scale_factor_y = scaled_pixmap.height() / self.original_size.height()

        font = QFont("Arial", int(12 * scale_factor_y))
        painter.setFont(font)
        painter.setPen(QColor("red"))

        # Draw each text at its scaled position
        for key, (text, position) in self.text_data.items():
            scaled_x = int(position[0] * scale_factor_x)
            scaled_y = int(position[1] * scale_factor_y)
            painter.drawText(scaled_x, scaled_y, text)

        painter.end()  # Ensure the painter is properly ended

        # Set the pixmap to the label
        self.image_label.setPixmap(scaled_pixmap)

    def handle_resize(self, event):
        self.render_image()
        QLabel.resizeEvent(self.image_label, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example usage
    image_path = "example_image.jpg"  # Replace with your image path
    text_data = {
        "kp": ("Kp: 1.0", (320, 215)),
        "ki": ("Ki: 0.1", (320, 235)),
        "kd": ("Kd: 0.01", (320, 255)),
        "set_point": ("SP: 5.0", (160, 225)),
        "error": ("Error: 0.5", (242, 200)),
        "height": ("y: 2.0", (625, 200)),
        "voltage": ("u: 5.0", (380, 210)),
        "flow_rate": ("Qin: 13.5", (440, 200))
    }


# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     # Example usage
#     image_path = "image.png"  # Replace with your image path
#     text_data = {
#         "kp": ("Kp: 1.0", (325, 155)),
#         "ki": ("Ki: 0.1", (325, 175)),
#         "kd": ("Kd: 0.01", (325, 195)),
#         "set_point": ("SP: 5.0", (163, 160)),
#         "error": ("Error: 0.5", (245, 125)),
#         "height": ("y: 2.0", (630, 130)),
#         "voltage": ("u: 5.0", (383, 140)),
#         "flow_rate": ("Qin: 13.5", (445, 120))
#     }

#     window = ImageWithTextOverlay(image_path, text_data)
#     window.show()

#     sys.exit(app.exec_())

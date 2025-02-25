import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import io
from PIL import Image

from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def plot_graph(
    plot_values: list[tuple],
    plot_type="line",
    title="Plot",
    x_label="X-axis",
    y_label="count",
):
    """Returns a PIL image of either a line or bar graph based on (x, y) tuples.


    Args:
        plot_values (list[tuple]): A list of (x, y) tuples where x and y are
            numeric values.
        plot_type (str, optional)
        title (str, optional)
        x_label (str, optional)
        y_label (str, optional)

    Raises:
        ValueError: Invalid plot type specified.

    Returns:
        image (PIL.image)
    """

    # Convert the list of tuples into a pandas DataFrame for easier plotting
    df = pd.DataFrame(plot_values, columns=["x", "y"])

    # num_x_ticks = len(df["x"])
    # width = max(8, int(num_x_ticks / 1.5))
    # figsize = (
    #     width,
    #     6,
    # )
    plt.figure(figsize=(10, 8))
    plt.tight_layout()
    # Create the plot based on the plot_type argument
    if plot_type == "line":
        sns.lineplot(data=df, x="x", y="y")
    elif plot_type == "bar":
        sns.barplot(data=df, x="x", y="y")
    else:
        raise ValueError("Invalid plot_type. Use 'line' or 'bar'.")

    # Set labels and title with bold, slightly larger font and padding
    plt.xlabel(x_label, fontsize=14, fontweight="bold", labelpad=15)
    plt.ylabel(y_label, fontsize=14, fontweight="bold", labelpad=15)
    plt.title(title, fontsize=16, fontweight="bold", pad=20)

    # Save the plot to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    # Read the image from the buffer using PIL
    image = Image.open(buf)

    # Return the image object
    return image


class ImageDisplayWidget(QWidget):
    def __init__(self, image):
        super().__init__()

        # Store the filename
        self.image = image

        # Create a QVBoxLayout for the widget
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a QLabel to display the image
        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        # Load and display the image
        self.display_image()

    def display_image(self):
        """Load and display the image from the filename."""
        try:
            # Open the image using PIL
            # pil_image = Image.open(self.filename)

            # Convert the PIL image to QImage
            qimage = self.pil_to_qimage(self.image)

            # Convert QImage to QPixmap and set it to the label
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap)

        except Exception as e:
            print(f"Error loading image: {e}")

    def pil_to_qimage(self, pil_image):
        """Convert a PIL image to a QImage."""
        # Convert the PIL image to RGB mode if necessary
        pil_image = pil_image.convert("RGB")

        # Get the image dimensions and data
        width, height = pil_image.size
        data = pil_image.tobytes()

        # Create a QImage from the data
        qimage = QImage(data, width, height, QImage.Format.Format_RGB888)

        return qimage

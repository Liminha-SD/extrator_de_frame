
import tensorflow as tf
import sys
import numpy as np

# Check if tensorflow is installed
try:
    import tensorflow as tf
except ImportError:
    print("TensorFlow not found. Please install it using: pip install tensorflow")
    sys.exit()

# Load the trained model
try:
    model = tf.keras.models.load_model('thumbnail_selector.keras')
except (IOError, ImportError):
    print("Trained model 'thumbnail_selector.keras' not found. Please run the training script first.")
    sys.exit()

# Image dimensions
image_height = 128
image_width = 128

# Get image path from command line arguments
if len(sys.argv) < 2:
    print("Usage: python predict.py <path_to_image>")
    sys.exit()

image_path = sys.argv[1]

# Load and preprocess the image
try:
    img = tf.keras.utils.load_img(
        image_path, target_size=(image_height, image_width)
    )
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0) # Create a batch
except Exception as e:
    print(f"Error loading or processing image: {e}")
    sys.exit()

# Predict the class
predictions = model.predict(img_array)
score = predictions[0][0]

# Print the prediction
if score > 0.5:
    print(f"The image is predicted as: good ({100 * score:.2f}% confidence)")
else:
    print(f"The image is predicted as: bad ({100 * (1 - score):.2f}% confidence)")

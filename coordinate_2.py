import cv2
import numpy as np
from scipy.interpolate import splprep, splev
import math
import matplotlib.pyplot as plt
from PIL import Image
import io


def process_image(img):
    img = np.array(img.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized_img = cv2.resize(img, (125, 90), interpolation=cv2.INTER_AREA)
    _, binary_img = cv2.threshold(resized_img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    path = []
    for contour in contours:
        for point in contour:
            x, y = int(point[0][0]), int(point[0][1])
            x = x - 62
            y = 210 - y
            path.append((x, y))
    return path


def smooth_coordinates(self, coords):
    if len(coords) < 3:
        return coords
    x, y = zip(*coords)
    try:
        if len(x) < 2 or len(y) < 2 or len(x) != len(y):
            return coords
        tck, u = splprep([x, y], s=0.5)
        u_new = np.linspace(u.min(), u.max(), len(x))
        x_new, y_new = splev(u_new, tck)
        return list(zip(map(int, x_new), map(int, y_new)))
    except Exception as e:
        print(f"Error smoothing coordinates: {e}")
        return coords


def generate_path(path):
    if not path:
        return []

    current_position = min(path, key=lambda p: (p[0] - 0) ** 2 + (p[1] - 125) ** 2)
    final_path = [current_position]
    path.remove(current_position)

    while path:
        next_position = min(path, key=lambda p: (p[0] - current_position[0]) ** 2 + (p[1] - current_position[1]) ** 2)
        distance = math.sqrt(
            (next_position[0] - current_position[0]) ** 2 + (next_position[1] - current_position[1]) ** 2)
        if distance > 20:  # Adjust this threshold as needed
            final_path.append((10000, 10000))
            final_path.append(next_position)
            final_path.append((-10000, -10000))
        else:
            final_path.append(next_position)
        path.remove(next_position)
        current_position = next_position

    return final_path
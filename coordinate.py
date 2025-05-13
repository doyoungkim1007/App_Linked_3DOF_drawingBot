import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import io

def process_image(img):
    # img = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    # print(img)
    img = np.array(img.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # img = Image.open(buffer)  # BytesIO에서 이미지를 PIL Image 객체로 읽어옴
    resized_img = cv2.resize(img, (125, 90), interpolation=cv2.INTER_AREA)
    _, thresholded = cv2.threshold(resized_img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    path = []
    for contour in contours:
        for point in contour:
            x, y = int(point[0][0]), int(point[0][1])
            x = x - 62
            y = 210 - y
            path.append((x, y))

    display_images(resized_img, path)
    return path

def display_images(*images):
    fig, axs = plt.subplots(1, len(images), figsize=(15, 5))
    for i, image in enumerate(images):
        if len(images) == 1:
            axs.imshow(image, cmap='gray')
            axs.axis('off')
        else:
            axs[i].imshow(image, cmap='gray')
            axs[i].axis('off')
    plt.show()

def generate_path(path):
    img = np.ones((90, 125), dtype=np.uint8) * 255
    current_position = min(path, key=lambda point: point[0]**2 + point[1]**2)
    generated_path = [current_position]
    img = update_image(img, current_position)

    def get_neighbors(position):
        x, y = position
        neighbors = [
            (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
            (x - 1, y),                 (x + 1, y),
            (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)
        ]
        return neighbors

    def find_next_position(current_position, path):
        for dist in range(1, 6):
            neighbors = get_neighbors(current_position)
            for nx, ny in neighbors:
                for point in path:
                    if abs(point[0] - nx) <= dist and abs(point[1] - ny) <= dist:
                        return point
        return None

    while len(path) > 1:
        next_position = find_next_position(current_position, path)
        if next_position:
            generated_path.append(next_position)
            path.remove(next_position)
            current_position = next_position
            img = update_image(img, current_position)
        else:
            generated_path.append((10000, 10000))
            next_position = min(path, key=lambda point: point[0]**2 + point[1]**2)
            generated_path.append(next_position)
            current_position = next_position
            img = update_image(img, current_position)
            generated_path.append((-10000, -10000))

    display_images(img)
    return generated_path

def update_image(img, current_position):
    x, y = current_position
    x_img = min(max(60 + x, 0), img.shape[1] - 1)
    y_img = min(max(45 + y, 0), img.shape[0] - 1)
    img[y_img, x_img] = 0
    return img

def main():
    file_path = '1.png'  #image_name
    path = process_image(file_path)
    generated_path = generate_path(path)
    print("Generated Path:", generated_path)

if __name__ == "__main__":
    main()

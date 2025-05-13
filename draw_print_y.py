import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import cv2
import math
from scipy.interpolate import splprep, splev

class ManipulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawing Robot Simulator")

        # Canvas setup
        self.canvas = tk.Canvas(root, width=500, height=500, bg='white')
        self.canvas.grid(row=0, column=0)
        #self.image_canvas = tk.Canvas(root, width=550, height=550, bg='white')
        #self.image_canvas.grid(row=0, column=1)
        self.drawing_canvas = tk.Canvas(root, width=500, height=500, bg='white')
        self.drawing_canvas.grid(row=0, column=2)

        # Robot configuration
        self.link_lengths = [95, 125]  # Length of the robot arms
        self.joint_angles1 = [math.radians(40), math.radians(85)]
        self.joint_angles2 = [math.radians(180-40), -math.radians(85)]

        # Initial pen position based on the forward kinematics
        self.pen_position = self.forward_kinematics(self.joint_angles1, self.link_lengths)

        # Draw static elements
        self.draw_axes()
        self.draw_manipulator()
        self.draw_reachable_area()

        # Control buttons
        self.create_controls()

    def create_controls(self):
        self.load_button = tk.Button(self.root, text="Load Image", command=self.load_image)
        self.load_button.grid(row=1, column=0)
        self.clear_button = tk.Button(self.root, text="Clear Points", command=self.clear_points)
        self.clear_button.grid(row=1, column=1)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            path = self.process_image(file_path)
            smooth_path = self.generate_path(path)
            self.move_pen(smooth_path)
            print("Generated Path:", smooth_path)

    def process_image(self, file_path):
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
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

    def generate_path(self, path):
        if not path:
            return []

        path_sorted_by_x = sorted(path, key=lambda p: (p[0], p[1]))
        smoothed_path = self.smooth_path(path_sorted_by_x)
        final_path = []

        for i in range(len(smoothed_path) - 1):
            final_path.append(smoothed_path[i])
            if abs(smoothed_path[i+1][0] - smoothed_path[i][0]) > 4 or abs(smoothed_path[i+1][1] - smoothed_path[i][1]) > 4:
                final_path.append((10000, 10000))
                final_path.append(smoothed_path[i+1])
                final_path.append((-10000, -10000))

        final_path.append(smoothed_path[-1])
        return final_path

    def smooth_path(self, path):
        if len(path) < 2:
            return path
        x, y = zip(*path)
        try:
            tck, u = splprep([x, y], s=3)
            unew = np.linspace(0, 1, len(x))
            out = splev(unew, tck)
            smoothed_path = list(zip(map(int, out[0]), map(int, out[1])))
            return smoothed_path
        except Exception as e:
            print(f"Error in smooth_path: {e}")
            return path

    def draw_axes(self):
        self.canvas.create_line(0, 250, 500, 250, fill="gray")
        self.canvas.create_line(250, 0, 250, 500, fill="gray")

        for i in range(0, 501, 50):
            self.canvas.create_line(i, 245, i, 255, fill="gray")
            self.canvas.create_text(i, 260, text=str(i - 250), fill="gray")
            self.canvas.create_line(245, i, 255, i, fill="gray")
            self.canvas.create_text(260, i, text=str(250 - i), fill="gray")

    def draw_reachable_area(self):
        base_x, base_y = 250, 250
        max_reach = sum(self.link_lengths)
        min_reach = abs(self.link_lengths[0] - self.link_lengths[1])
        self.canvas.create_oval(base_x - max_reach, base_y - max_reach, base_x + max_reach, base_y + max_reach, outline="blue", dash=(2, 2))
        self.canvas.create_oval(base_x - min_reach, base_y - min_reach, base_x + min_reach, base_y + min_reach, outline="red", dash=(2, 2))

    def draw_manipulator(self):
        base_x, base_y = 250, 250

        joint1_x1 = base_x + self.link_lengths[0] * math.cos(self.joint_angles1[0])
        joint1_y1 = base_y + self.link_lengths[0] * math.sin(self.joint_angles1[0])
        end_effector_x1 = joint1_x1 + self.link_lengths[1] * math.cos(self.joint_angles1[0] + self.joint_angles1[1])
        end_effector_y1 = joint1_y1 + self.link_lengths[1] * math.sin(self.joint_angles1[0] + self.joint_angles1[1])

        joint1_x2 = base_x + self.link_lengths[0] * math.cos(self.joint_angles2[0])
        joint1_y2 = base_y + self.link_lengths[0] * math.sin(self.joint_angles2[0])
        end_effector_x2 = joint1_x2 + self.link_lengths[1] * math.cos(self.joint_angles2[0] + self.joint_angles2[1])
        end_effector_y2 = joint1_y2 + self.link_lengths[1] * math.sin(self.joint_angles2[0] + self.joint_angles2[1])

        self.canvas.delete("manipulator")
        self.canvas.create_line(base_x, base_y, joint1_x1, joint1_y1, fill="red", width=5, tags="manipulator")
        self.canvas.create_line(joint1_x1, joint1_y1, end_effector_x1, end_effector_y1, fill="red", width=5, tags="manipulator")
        self.canvas.create_line(base_x, base_y, joint1_x2, joint1_y2, fill="blue", width=5, tags="manipulator")
        self.canvas.create_line(joint1_x2, joint1_y2, end_effector_x2, end_effector_y2, fill="blue", width=5, tags="manipulator")
        self.canvas.create_oval(base_x-5, base_y-5, base_x+5, base_y+5, fill="black", tags="manipulator")
        self.canvas.create_oval(joint1_x1-5, joint1_y1-5, joint1_x1+5, joint1_y1+5, fill="black", tags="manipulator")
        self.canvas.create_oval(end_effector_x1-5, end_effector_y1-5, end_effector_x1+5, end_effector_y1+5, fill="green", tags="manipulator")
        self.canvas.create_oval(joint1_x2-5, joint1_y2-5, joint1_x2+5, joint1_y2+5, fill="black", tags="manipulator")
        self.canvas.create_oval(end_effector_x2-5, end_effector_y2-5, end_effector_x2+5, end_effector_y2+5, fill="green", tags="manipulator")

    def forward_kinematics(self, joint_angles, link_lengths):
        base_x, base_y = 250, 250
        joint1_x = base_x + link_lengths[0] * math.cos(joint_angles[0])
        joint1_y = base_y + link_lengths[0] * math.sin(joint_angles[0])
        end_effector_x = joint1_x + link_lengths[1] * math.cos(joint_angles[0] + joint_angles[1])
        end_effector_y = joint1_y + link_lengths[1] * math.sin(joint_angles[0] + joint_angles[1])
        return end_effector_x, end_effector_y

    def inverse_kinematics(self, target_x, target_y, link_lengths, is_arm2=False):
        base_x, base_y = 250, 250
        dx = target_x - base_x
        dy = target_y - base_y
        distance = np.sqrt(dx**2 + dy**2)

        cos_angle2 = (dx**2 + dy**2 - link_lengths[0]**2 - link_lengths[1]**2) / (2 * link_lengths[0] * link_lengths[1])
        cos_angle2 = max(min(cos_angle2, 1), -1)
        sin_angle2 = np.sqrt(1 - cos_angle2**2)
        theta2 = math.acos(cos_angle2)

        if is_arm2:
            theta2 = -theta2

        k1 = link_lengths[0] + link_lengths[1] * cos_angle2
        k2 = link_lengths[1] * sin_angle2
        theta1 = math.atan2(dy, dx) - math.atan2(k2, k1)

        if is_arm2:
            theta1 = math.atan2(dy, dx) + math.atan2(k2, k1)

        return [theta1, theta2]

    def animate_movement(self, target_angles1, target_angles2, target_position, pen_down):
        steps = 10
        current_angles1 = np.array(self.joint_angles1, dtype=np.float64)
        current_angles2 = np.array(self.joint_angles2, dtype=np.float64)
        target_angles1 = np.array(target_angles1, dtype=np.float64)
        target_angles2 = np.array(target_angles2, dtype=np.float64)
        delta_angles1 = (target_angles1 - current_angles1) / steps
        delta_angles2 = (target_angles2 - current_angles2) / steps

        for _ in range(steps):
            current_angles1 += delta_angles1
            current_angles2 += delta_angles2
            self.joint_angles1 = current_angles1.tolist()
            self.joint_angles2 = current_angles2.tolist()
            self.pen_position = self.forward_kinematics(self.joint_angles1, self.link_lengths)
            self.draw_manipulator()
            if pen_down:
                self.drawing_canvas.create_oval(self.pen_position[0]-2, self.pen_position[1]-2, self.pen_position[0]+2, self.pen_position[1]+2, fill="black", tags="pen")
            self.canvas.update()
            self.canvas.after(10)

        self.pen_position = target_position
        self.draw_manipulator()

    def clear_points(self):
        self.canvas.delete("pen")
        self.drawing_canvas.delete("pen")

    def move_pen(self, path):
        pen_down = False
        for index, (x, y) in enumerate(path):
            try:
                if (x == 10000 and y == 10000):
                    pen_down = False
                    continue
                elif (x == -10000 and y == -10000):
                    pen_down = True
                    continue
                x += 250
                y = 250 - y
                target_angles1 = self.inverse_kinematics(x, y, self.link_lengths)
                target_angles2 = self.inverse_kinematics(x, y, self.link_lengths, is_arm2=True)
                self.animate_movement(target_angles1, target_angles2, (x, y), pen_down)
                pen_down = True
            except Exception as e:
                self.show_warning(str(e))

        self.show_completion_popup()

    def show_warning(self, message):
        warning_popup = tk.Toplevel(self.root)
        warning_popup.title("Warning")
        tk.Label(warning_popup, text=message).pack()
        tk.Button(warning_popup, text="OK", command=warning_popup.destroy).pack()

    def show_completion_popup(self):
        completion_popup = tk.Toplevel(self.root)
        completion_popup.title("Info")
        tk.Label(completion_popup, text="Drawing completed!").pack()
        tk.Button(completion_popup, text="OK", command=completion_popup.destroy).pack()

def main():
    root = tk.Tk()
    app = ManipulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

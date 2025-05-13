import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
from database import retrieve_drawing

class ViewDrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawing Visualization")
        self.root.geometry("800x600")

        # Couleur de fond 
        self.root.configure(bg='#69BB33')

        # Titre
        self.title_label = tk.Label(self.root, text="Drawing Visualization", font=("Comic Sans MS", 24, "bold"), bg='#69BB33', fg='#E7C820')
        self.title_label.pack(pady=20)

        # Demander l'ID du dessin
        self.id_label = tk.Label(self.root, text="Enter the drawing ID :", font=("Comic Sans MS", 12, "bold"), bg='#69BB33', fg='#E7C820')
        self.id_label.pack(pady=10)
        self.id_entry = tk.Entry(self.root, font=("Comic Sans MS", 12, "bold"))
        self.id_entry.pack(pady=10)

        # Bouton Visualiser
        self.view_button = tk.Button(self.root, text="View", command=self.view_drawing, bg='#c7d7e3', fg='#5d5c61', font=("Comic Sans MS", 12, "bold"), width=15)
        self.view_button.pack(pady=10)

        # Zone de dessin
        self.canvas_frame = tk.Frame(self.root, bg='#69BB33', bd=2, relief="ridge")
        self.canvas_frame.pack(pady=20)

        self.drawing_area = tk.Canvas(self.canvas_frame, bg='white', width=600, height=400, bd=0, highlightthickness=0)
        self.drawing_area.pack()

    def view_drawing(self):
        drawing_id = self.id_entry.get()
        image_data = retrieve_drawing(drawing_id)
        if image_data:
            image = Image.open(BytesIO(image_data))
            image = ImageTk.PhotoImage(image)
            self.drawing_area.create_image(0, 0, anchor=tk.NW, image=image)
            self.drawing_area.image = image
        else:
            tk.messagebox.showerror("Error", "Drawing not found")

if __name__ == "__main__":
    root = tk.Tk()
    app = ViewDrawingApp(root)
    root.mainloop()

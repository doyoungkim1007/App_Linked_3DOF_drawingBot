import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw, ImageTk, ImageSequence
import io
import os
from database import init_db, save_drawing, get_all_drawings, retrieve_drawing, check_existing_drawing, \
    add_check_drawing, count_drawing
from coordinate_2 import process_image, generate_path

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawing App")
        self.root.geometry("1000x600")
        self.current_drawing_name = "Default_Drawing"  # Nom par défaut du dessin

        # Chargement de l'image de fond
        image_path = os.path.join(os.path.dirname(__file__), 'assets', 'image1.png')
        try:
            self.background_image = Image.open(image_path)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Background image not found: {image_path}")
            self.root.destroy()
            return

        self.background_image = self.background_image.resize((1000, 600), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(self.background_image)
        self.bg_label = tk.Label(self.root, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Titre
        self.title_label = tk.Label(self.root, text="Drawing Board", font=("Comic Sans MS", 24, "bold"), bg='#000000', fg='red')
        self.title_label.pack(pady=20)

        # Cadre principal pour tout aligner horizontalement
        self.main_frame = tk.Frame(self.root, bg='#000000')
        self.main_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        # Cadre secondaire pour centrer le contenu
        self.inner_frame = tk.Frame(self.main_frame, bg='#000000')
        self.inner_frame.pack(expand=True)

        # Zone de dessin (réduite en taille)
        self.drawing_area = tk.Canvas(self.inner_frame, bg='white', width=625, height=450, bd=2, relief="ridge")
        self.drawing_area.pack(side=tk.LEFT, padx=20)
        self.drawing_area.bind('<B1-Motion>', self.paint)
        self.drawing_area.bind('<ButtonRelease-1>', self.reset)

        # Historique des lignes pour l'annulation
        self.lines = []

        # Cadre pour les boutons
        self.button_frame = tk.Frame(self.inner_frame, bg='#000000')
        self.button_frame.pack(side=tk.LEFT, padx=20)

        # Bouton Upload
        self.upload_button = tk.Button(self.button_frame, text="Upload", command=self.upload_drawing, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.upload_button.pack(pady=5)

        # Bouton Enregistrer
        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.save_button.pack(pady=5)

        # Bouton Effacer
        self.clear_button = tk.Button(self.button_frame, text="Clear", command=self.clear, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.clear_button.pack(pady=5)

        # Bouton Gomme
        self.eraser_button = tk.Button(self.button_frame, text="Eraser", command=self.use_eraser, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.eraser_button.pack(pady=5)

        # Bouton Stylo
        self.pen_button = tk.Button(self.button_frame, text="Pen", command=self.use_pen, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.pen_button.pack(pady=5)

        # Liste des dessins
        self.drawing_list_label = tk.Label(self.button_frame, text="Saved Drawings", font=("Comic Sans MS", 12, "bold"), bg='#000000', fg='red')
        self.drawing_list_label.pack(pady=10)

        self.drawing_listbox = tk.Listbox(self.button_frame, width=20, height=10)
        self.drawing_listbox.pack(pady=5)
        self.update_drawing_list()

        # Bouton Voir
        self.view_button = tk.Button(self.button_frame, text="drawing", command=self.save_to_check_drawing, bg='#000000', fg='red', font=("Comic Sans MS", 10, "bold"), width=12)
        self.view_button.pack(pady=5)

        # Lier le double clic sur la liste à la méthode view_drawing_from_listbox
        self.drawing_listbox.bind('<Double-Button-1>', self.view_drawing_from_listbox)

        # Initialisation des variables pour le dessin
        self.old_x = None
        self.old_y = None
        self.eraser_on = False
        self.image = Image.new("RGB", (500, 400), 'white')
        self.draw = ImageDraw.Draw(self.image)

        # Initialisation de la base de données
        init_db()

    def paint(self, event):
        paint_color = 'white' if self.eraser_on else 'black'
        if self.old_x and self.old_y:
            line_id = self.drawing_area.create_line(self.old_x, self.old_y, event.x, event.y, width=10 if self.eraser_on else 2, fill=paint_color, capstyle=tk.ROUND, smooth=tk.TRUE)
            self.draw.line([self.old_x, self.old_y, event.x, event.y], fill=paint_color, width=10 if self.eraser_on else 2)
            self.lines.append(line_id)
        self.old_x = event.x
        self.old_y = event.y

    def reset(self, event):
        self.old_x = None
        self.old_y = None

    def save(self):
        name = simpledialog.askstring("Input", "Enter the name of the drawing:")
        if name and name != 'none':
            # Check if the name already exists
            if name in get_all_drawings():
                messagebox.showerror("Error",
                                     "A drawing with this name already exists. Please choose a different name.")
                return

            buffer = io.BytesIO()
            self.image.save(buffer, format="PNG")
            buffer.seek(0)

            coordinates = generate_path(process_image(self.image))
            coordinates_str = ', '.join(f'({x}, {y})' for x, y in coordinates)
            print(coordinates_str)
            save_drawing(name, buffer.getvalue(), coordinates_str)
            messagebox.showinfo("Save", "The drawing has been saved in the database.")
            self.update_drawing_list()

            # Afficher l'animation GIF après l'enregistrement
            self.show_save_animation()
        else:
            messagebox.showerror("Error",
                                 "The name 'none' cannot be used.")
            return

    def show_save_animation(self):
        # Créer une fenêtre popup pour afficher l'animation GIF
        popup = tk.Toplevel(self.root)
        popup.title("Save Animation")
        popup.geometry("300x300")

        # Charger et animer le GIF
        gif_path = os.path.join(os.path.dirname(__file__), 'assets', 'save2.gif')
        try:
            gif_image = Image.open(gif_path)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Save animation GIF not found: {gif_path}")
            popup.destroy()
            return

        frames = [ImageTk.PhotoImage(frame.copy().resize((500, 500), Image.Resampling.LANCZOS)) for frame in ImageSequence.Iterator(gif_image)]
        gif_label = tk.Label(popup)
        gif_label.pack(expand=True, fill=tk.BOTH)

        def update(ind):
            frame = frames[ind]
            ind = (ind + 1) % len(frames)
            gif_label.config(image=frame)
            popup.after(60, update, ind)

            popup.update_idletasks()  # Permet à tkinter de calculer la taille du label
            gif_label_width = gif_label.winfo_width()
            gif_label_height = gif_label.winfo_height()

            # Centrer le label contenant le GIF au milieu de la fenêtre
            x = (popup.winfo_width() - gif_label_width) // 2
            y = (popup.winfo_height() - gif_label_height) // 2
            gif_label.place(x=x, y=y)

        popup.after(0, update, 0)
        popup.after(3000, popup.destroy)

    def clear(self):
        self.drawing_area.delete("all")
        self.image = Image.new("RGB", (500, 400), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.update_drawing_list()

    def use_eraser(self):
        self.eraser_on = True
        self.pen_button.config(relief=tk.RAISED)
        self.eraser_button.config(relief=tk.SUNKEN)

    def use_pen(self):
        self.eraser_on = False
        self.pen_button.config(relief=tk.SUNKEN)
        self.eraser_button.config(relief=tk.RAISED)

    def upload_drawing(self):
        # Vérifier s'il y a un dessin chargé dans la zone de dessin
        if self.image and len(self.lines) > 0:
            # Enregistrer automatiquement le dessin actuel sans demander de nom
            buffer = io.BytesIO()
            self.image.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Vérifier si le dessin existe déjà dans la base de données
            if self.current_drawing_name in get_all_drawings():
                # Mettre à jour le dessin existant avec le même nom
                save_drawing(self.current_drawing_name, buffer.getvalue())
                messagebox.showinfo("Save", f"The current drawing has been updated as {self.current_drawing_name}.")
            else:
                # Enregistrer le dessin comme nouveau s'il n'existe pas encore
                save_drawing(self.current_drawing_name, buffer.getvalue())
                messagebox.showinfo("Save", f"The current drawing has been saved as {self.current_drawing_name}.")

            # Afficher l'animation GIF après l'enregistrement
            self.show_save_animation()
            
            # Mettre à jour la liste des dessins après l'enregistrement
            self.update_drawing_list()

        # Charger un dessin depuis la base de données
        selected_name = simpledialog.askstring("Input", "Enter the name of the drawing to upload:")
        if selected_name:
            drawing_data = retrieve_drawing(selected_name)
            if drawing_data:
                self.current_drawing_name = selected_name  # Mettre à jour le nom du dessin en cours
                # Charger le dessin dans la zone de dessin principale
                self.load_drawing_from_data(drawing_data)
            else:
                messagebox.showerror("Error", "Drawing not found in the database.")

    def load_drawing_from_data(self, drawing_data):
        # Effacer la zone de dessin actuelle
        self.drawing_area.delete("all")

        # Charger l'image à partir des données binaires
        self.image = Image.open(io.BytesIO(drawing_data))
        self.draw = ImageDraw.Draw(self.image)

        # Afficher l'image dans la zone de dessin
        self.image_tk = ImageTk.PhotoImage(self.image)
        self.drawing_area.create_image(0, 0, anchor=tk.NW, image=self.image_tk)

        # Réinitialiser les lignes de l'historique
        self.lines = []

    def view_drawing(self):
        selected_name = self.drawing_listbox.get(tk.ACTIVE)
        if selected_name:
            drawing_data = retrieve_drawing(selected_name)
            if drawing_data:
                self.load_drawing_from_data(drawing_data)
            else:
                messagebox.showerror("Error", "Drawing not found in the database.")

    def view_drawing_from_listbox(self, event):
        # Récupérer l'index de l'élément sélectionné dans la liste
        selected_index = self.drawing_listbox.curselection()

        if selected_index:
            # Récupérer le nom du dessin sélectionné
            selected_name = self.drawing_listbox.get(selected_index)

            # Récupérer les données du dessin à partir de la base de données
            drawing_data = retrieve_drawing(selected_name)

            if drawing_data:
                # Charger le dessin dans la zone de dessin principale
                self.load_drawing_from_data(drawing_data)
            else:
                messagebox.showerror("Error", "Drawing not found in the database.")

    def update_drawing_list(self):
        self.drawing_listbox.delete(0, tk.END)
        drawings = get_all_drawings()
        for drawing in drawings:
            self.drawing_listbox.insert(tk.END, drawing)

    def save_to_check_drawing(self):
        # Sélectionner un dessin depuis la base de données
        selected_drawing = self.drawing_listbox.get(tk.ACTIVE)
        if selected_drawing:
            can_draw = count_drawing()
            if can_draw:
                add_check_drawing(selected_drawing)
                messagebox.showinfo("Drawing", "The selected drawing has been saved in check_drawing.")
            else:
                messagebox.showerror("Error", "Failed to retrieve drawing data.")
        else:
            messagebox.showerror("Error", "Please select a drawing from the list.")

class WelcomeApp:
    def __init__(self, root, start_drawing_app):
        self.root = root
        self.root.title("Welcome")
        self.root.geometry("1000x600")

        # Chargement du GIF
        gif_path = os.path.join(os.path.dirname(__file__), 'assets', 'amongus.gif')
        self.gif_frames = []
        try:
            gif = Image.open(gif_path)
            self.gif_frames = [ImageTk.PhotoImage(frame.copy().resize((1000, 600), Image.Resampling.LANCZOS)) for frame in ImageSequence.Iterator(gif)]
        except FileNotFoundError:
            messagebox.showerror("Error", f"GIF image not found: {gif_path}")
            self.root.destroy()
            return

        if not self.gif_frames:
            messagebox.showerror("Error", f"Failed to load GIF frames from: {gif_path}")
            return

        # Cadre pour le GIF et le bouton
        self.gif_frame = tk.Frame(self.root)
        self.gif_frame.pack(expand=True, fill=tk.BOTH)

        # Affichage du GIF
        self.label = tk.Label(self.gif_frame)
        self.label.pack(expand=True, fill=tk.BOTH)
        self.show_frame(0)

        # Bouton pour démarrer l'application principale
        self.start_button = tk.Button(self.root, text="Start Drawing App", command=start_drawing_app, font=("Comic Sans MS", 18, "bold"), fg='red', bg='black')
        self.start_button.place(relx=0.5, rely=0.9, anchor=tk.CENTER)

    def show_frame(self, frame_idx):
        frame = self.gif_frames[frame_idx]
        self.label.config(image=frame)
        self.root.after(100, self.show_frame, (frame_idx + 1) % len(self.gif_frames))

def start_drawing_app():
    welcome_root.destroy()
    main_root = tk.Tk()
    app = DrawingApp(main_root)
    main_root.mainloop()

if __name__ == "__main__":
    welcome_root = tk.Tk()
    welcome_app = WelcomeApp(welcome_root, start_drawing_app)
    welcome_root.mainloop()
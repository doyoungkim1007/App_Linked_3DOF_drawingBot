import mysql.connector

# Paramètres de connexion MySQL
config = {
    'host': 'YOUR IP',
    'user': 'USER_NAME',  # Remplacez par votre utilisateur MySQL
    'password': 'PASSWORD',  # Remplacez par votre mot de passe MySQL
    'database': 'drawing_bot'
}


# Initialisation de la connexion à MySQL
def init_db():
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

   

    c.execute('''CREATE TABLE IF NOT EXISTS check_drawing
                 (id INT AUTO_INCREMENT PRIMARY KEY,
                 name VARCHAR(10) NOT NULL,
                 drawing LONGBLOB NOT NULL,
                 coordinates TEXT NOT NULL)''')

    conn.commit()
    conn.close()


# Fonction pour sauvegarder un dessin dans la base de données
def save_drawing(name, image_data, coordinates):
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    try:
        c.execute('INSERT INTO drawings (name, drawing, coordinates) VALUES (%s, %s, %s)',
                  (name, image_data, coordinates))
        conn.commit()
        print(f"Drawing '{name}' saved successfully.")
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"Error saving drawing '{name}': {e}")
        conn.rollback()
        conn.close()
        return False

# Fonction pour récupérer tous les noms de dessins de la base de données
def get_all_drawings():
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    c.execute('SELECT name FROM drawings')
    drawings = [row[0] for row in c.fetchall()]

    conn.close()
    return drawings

# Fonction pour récupérer un dessin spécifique par son nom
def retrieve_drawing(name):
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    c.execute('SELECT drawing FROM drawings WHERE name=%s', (name,))
    drawing_data = c.fetchone()

    conn.close()
    return drawing_data[0] if drawing_data else None

# Fonction pour vérifier s'il y a déjà un dessin dans la table check_drawing
def check_existing_drawing():
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM check_drawing')
    count = c.fetchone()[0]

    conn.close()
    return count > 0

# Fonction pour ajouter un dessin dans la table check_drawing
def add_check_drawing(name):
    conn = mysql.connector.connect(**config)
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO check_drawing (name) VALUES (%s)', (name,))
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"Error adding drawing to check_drawing: {e}")
        conn.rollback()
        conn.close()
        return False

# Fonction pour supprimer un dessin de la table check_drawing
def clear_check_drawing():
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    try:
        c.execute('DELETE FROM check_drawing')
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"Error clearing check_drawing: {e}")
        conn.rollback()
        conn.close()
        return False

def count_drawing():
    conn = mysql.connector.connect(**config)
    c = conn.cursor()

    try:
        c.execute('SELECT COUNT(*) AS count FROM check_drawing')
        count = c.fetchone()[0]  # 결과에서 count 값 추출
        conn.close()
        if count == 0:
            return True
        else:
            return False
    except mysql.connector.Error as e:
        print(f"Error fetching count from check_drawing: {e}")
        conn.close()
        return False

# Appel à init_db pour initialiser la base de données au chargement du module
init_db()

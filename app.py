from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from py2neo import Graph, Node, Relationship
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración de la base de datos Neo4j
url = "bolt://localhost:7687"
username = "neo4j"
password = "PDR2024ED"
graph = Graph(url, auth=(username, password))

# Configuración para servir archivos estáticos
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static', filename)

# Lista de libros con descripciones, géneros y autores
books = [
    {"title": "Cien años de soledad", "description": "Novela de Gabriel García Márquez que narra la historia de la familia Buendía a lo largo de varias generaciones.", "genre": "Realismo mágico", "author": "Gabriel García Márquez"},
    {"title": "Don Quijote de la Mancha", "description": "Obra cumbre de la literatura española escrita por Miguel de Cervantes, relata las aventuras del ingenioso hidalgo Don Quijote.", "genre": "Aventura", "author": "Miguel de Cervantes"},
    {"title": "La sombra del viento", "description": "Novela de Carlos Ruiz Zafón ambientada en la Barcelona de mediados del siglo XX, donde un joven descubre un misterioso libro.", "genre": "Misterio", "author": "Carlos Ruiz Zafón"},
    {"title": "El amor en los tiempos del cólera", "description": "Novela de Gabriel García Márquez que narra una historia de amor que perdura a lo largo de décadas.", "genre": "Romance", "author": "Gabriel García Márquez"},
    {"title": "Ficciones", "description": "Colección de cuentos de Jorge Luis Borges que exploran temas como los laberintos, los espejos y los sueños.", "genre": "Fantasía", "author": "Jorge Luis Borges"},
    {"title": "Rayuela", "description": "Novela de Julio Cortázar que invita al lector a saltar de un capítulo a otro, creando múltiples caminos de lectura.", "genre": "Ficción", "author": "Julio Cortázar"},
    {"title": "La casa de los espíritus", "description": "Novela de Isabel Allende que narra la historia de la familia Trueba a lo largo de varias generaciones en Chile.", "genre": "Realismo mágico", "author": "Isabel Allende"},
    {"title": "Pedro Páramo", "description": "Novela de Juan Rulfo que narra la historia de un hombre que viaja al pueblo de Comala en busca de su padre.", "genre": "Realismo mágico", "author": "Juan Rulfo"},
    {"title": "Crónica de una muerte anunciada", "description": "Novela de Gabriel García Márquez que cuenta la historia del asesinato de Santiago Nasar en un pequeño pueblo colombiano.", "genre": "Ficción", "author": "Gabriel García Márquez"},
    {"title": "El túnel", "description": "Novela de Ernesto Sabato que narra la historia de un pintor obsesionado con una mujer a la que cree comprender profundamente.", "genre": "Thriller", "author": "Ernesto Sabato"},
    {"title": "La ciudad y los perros", "description": "Novela de Mario Vargas Llosa que describe la vida de los cadetes en una academia militar en Lima, Perú.", "genre": "Drama", "author": "Mario Vargas Llosa"},
    {"title": "El Principito", "description": "Novela de Antoine de Saint-Exupéry que narra la historia de un pequeño príncipe que viaja de planeta en planeta.", "genre": "Fantasía", "author": "Antoine de Saint-Exupéry"},
    {"title": "Cumbres Borrascosas", "description": "Novela de Emily Brontë que narra una historia de amor y venganza en los páramos de Yorkshire.", "genre": "Romance", "author": "Emily Brontë"},
    {"title": "Matar a un ruiseñor", "description": "Novela de Harper Lee que aborda temas de racismo e injusticia en el sur de Estados Unidos.", "genre": "Ficción", "author": "Harper Lee"},
    {"title": "1984", "description": "Novela de George Orwell que describe una sociedad distópica bajo un régimen totalitario.", "genre": "Ciencia ficción", "author": "George Orwell"},
    {"title": "El gran Gatsby", "description": "Novela de F. Scott Fitzgerald que narra la historia del misterioso millonario Jay Gatsby y su amor por Daisy Buchanan.", "genre": "Ficción", "author": "F. Scott Fitzgerald"},
    {"title": "Orgullo y prejuicio", "description": "Novela de Jane Austen que explora temas de amor y matrimonio en la sociedad inglesa del siglo XIX.", "genre": "Romance", "author": "Jane Austen"},
    {"title": "El retrato de Dorian Gray", "description": "Novela de Oscar Wilde sobre un joven cuya belleza se conserva mientras su retrato envejece.", "genre": "Fantasía", "author": "Oscar Wilde"},
    {"title": "El guardián entre el centeno", "description": "Novela de J.D. Salinger sobre las experiencias de un adolescente en Nueva York.", "genre": "Ficción", "author": "J.D. Salinger"},
    {"title": "Los miserables", "description": "Novela de Victor Hugo que narra la vida de varios personajes en la Francia del siglo XIX.", "genre": "Drama", "author": "Victor Hugo"},
    {"title": "La Odisea", "description": "Poema épico de Homero que narra las aventuras de Odiseo en su viaje de regreso a Ítaca.", "genre": "Épica", "author": "Homero"},
    {"title": "El hobbit", "description": "Novela de J.R.R. Tolkien sobre las aventuras de Bilbo Bolsón en la Tierra Media.", "genre": "Fantasía", "author": "J.R.R. Tolkien"},
    {"title": "Alicia en el País de las Maravillas", "description": "Novela de Lewis Carroll sobre las aventuras de una niña en un mundo fantástico.", "genre": "Fantasía", "author": "Lewis Carroll"},
    {"title": "Frankenstein", "description": "Novela de Mary Shelley sobre un científico que crea un ser vivo a partir de partes de cadáveres.", "genre": "Horror", "author": "Mary Shelley"},
    {"title": "Drácula", "description": "Novela de Bram Stoker sobre el conde Drácula y su intento de trasladarse a Inglaterra.", "genre": "Horror", "author": "Bram Stoker"},
]

# Crear nodos de libros en Neo4j
for book in books:
    if not graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book['title']).data():
        graph.run("CREATE (b:Book {title: $title, description: $description, genre: $genre, author: $author})",
                  title=book['title'], description=book['description'], genre=book['genre'], author=book['author'])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = graph.run("MATCH (u:User {username: $username}) RETURN u", username=username).data()
        if user and check_password_hash(user[0]['u']['password'], password):
            session['user_id'] = username
            return redirect(url_for('dashboard'))
        return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        graph.run("CREATE (u:User {username: $username, password: $password})", username=username, password=password)
        flash("Usuario registrado exitosamente")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        book_title = request.form['book_title']
        book_genre = request.form['book_genre']
        book_author = request.form['book_author']
        username = session['user_id']

        # Crear nodo de libro si no existe
        if not graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book_title).data():
            graph.run("CREATE (b:Book {title: $title, genre: $genre, author: $author})",
                      title=book_title, genre=book_genre, author=book_author)

        # Relacionar usuario con el libro leído
        query = """
        MATCH (u:User {username: $username}), (b:Book {title: $book_title})
        CREATE (u)-[:HAS_READ]->(b)
        """
        graph.run(query, username=username, book_title=book_title)

        flash("Libro agregado exitosamente")
        return redirect(url_for('dashboard'))
    return render_template('add_book.html')

@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Obtener recomendaciones de libros basadas en el género y autor de los libros leídos
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)
    WITH u, COLLECT(DISTINCT b.genre) AS genres, COLLECT(DISTINCT b.author) AS authors
    MATCH (rec:Book)
    WHERE (rec.genre IN genres OR rec.author IN authors)
    AND NOT EXISTS((u)-[:HAS_READ]->(rec))
    RETURN rec.title AS title, rec.description AS description, rec.genre AS genre, rec.author AS author
    LIMIT 5
    """
    recommendations = graph.run(query, username=username).data()

    return render_template('recommend.html', recommendations=recommendations)

@app.route('/like_book/<title>')
def like_book(title):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Verificar si el libro ya está marcado como "me gusta"
    query = """
    MATCH (u:User {username: $username})-[:LIKED]->(b:Book {title: $title})
    RETURN b
    """
    liked_book = graph.run(query, username=username, title=title).data()

    if liked_book:
        # Si el libro ya está marcado como "me gusta", eliminar la relación LIKED
        query = """
        MATCH (u:User {username: $username})-[r:LIKED]->(b:Book {title: $title})
        DELETE r
        """
        graph.run(query, username=username, title=title)
        flash("Libro removido de 'me gusta'")
    else:
        # Si el libro no está marcado como "me gusta", crear la relación LIKED
        query = """
        MATCH (u:User {username: $username}), (b:Book {title: $title})
        CREATE (u)-[:LIKED]->(b)
        """
        graph.run(query, username=username, title=title)
        flash("Libro marcado como me gusta")

    return redirect(url_for('recommend'))

@app.route('/liked_books')
def liked_books():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Obtener libros likeados
    query = """
    MATCH (u:User {username: $username})-[:LIKED]->(b:Book)
    RETURN b.title AS title, b.description AS description, b.genre AS genre, b.author AS author
    """
    liked_books = graph.run(query, username=username).data()

    return render_template('liked_books.html', liked_books=liked_books)

@app.route('/upload_photo/<title>', methods=['POST'])
def upload_photo(title):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('recommend'))

    file = request.files['photo']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('recommend'))

    if file:
        filename = title.replace(' ', '_') + '.jpg'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("Foto subida exitosamente")
        return redirect(url_for('recommend'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

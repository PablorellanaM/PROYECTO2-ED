from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from py2neo import Graph
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
app.config['UPLOAD_FOLDER'] = 'static/images'

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static', filename)

# Lista de géneros de libros
genres = [
    "Ficción", "No Ficción", "Misterio", "Romance", "Ciencia Ficción",
    "Fantasía", "Biografía", "Historia", "Autoayuda", "Negocios",
    "Poesía", "Drama", "Suspenso", "Terror", "Humor"
]

# Lista de libros con descripciones, géneros y autores
books = [
    {"title": "Cien años de soledad", "description": "Novela de Gabriel García Márquez que narra la historia de la familia Buendía a lo largo de varias generaciones.", "genre": "Ficción", "author": "Gabriel García Márquez"},
    {"title": "Don Quijote de la Mancha", "description": "Obra cumbre de la literatura española escrita por Miguel de Cervantes, relata las aventuras del ingenioso hidalgo Don Quijote.", "genre": "Ficción", "author": "Miguel de Cervantes"},
    {"title": "La sombra del viento", "description": "Novela de Carlos Ruiz Zafón ambientada en la Barcelona de mediados del siglo XX, donde un joven descubre un misterioso libro.", "genre": "Misterio", "author": "Carlos Ruiz Zafón"},
    {"title": "El amor en los tiempos del cólera", "description": "Novela de Gabriel García Márquez que narra una historia de amor que perdura a lo largo de décadas.", "genre": "Romance", "author": "Gabriel García Márquez"},
    {"title": "Ficciones", "description": "Colección de cuentos de Jorge Luis Borges que exploran temas como los laberintos, los espejos y los sueños.", "genre": "Fantasía", "author": "Jorge Luis Borges"},
    {"title": "Rayuela", "description": "Novela de Julio Cortázar que invita al lector a saltar de un capítulo a otro, creando múltiples caminos de lectura.", "genre": "Ficción", "author": "Julio Cortázar"},
    {"title": "La casa de los espíritus", "description": "Novela de Isabel Allende que narra la historia de la familia Trueba a lo largo de varias generaciones en Chile.", "genre": "Fantasía", "author": "Isabel Allende"},
    {"title": "Pedro Páramo", "description": "Novela de Juan Rulfo que narra la historia de un hombre que viaja al pueblo de Comala en busca de su padre.", "genre": "Fantasía", "author": "Juan Rulfo"},
    {"title": "Crónica de una muerte anunciada", "description": "Novela de Gabriel García Márquez que cuenta la historia del asesinato de Santiago Nasar en un pequeño pueblo colombiano.", "genre": "Ficción", "author": "Gabriel García Márquez"},
    {"title": "El túnel", "description": "Novela de Ernesto Sabato que narra la historia de un pintor obsesionado con una mujer a la que cree comprender profundamente.", "genre": "Suspenso", "author": "Ernesto Sabato"},
    {"title": "La ciudad y los perros", "description": "Novela de Mario Vargas Llosa que describe la vida de los cadetes en una academia militar en Lima, Perú.", "genre": "Ficción", "author": "Mario Vargas Llosa"},
    {"title": "1984", "description": "Una novela distópica de George Orwell que explora un futuro totalitario bajo el control del Gran Hermano.", "genre": "Ciencia Ficción", "author": "George Orwell"},
    {"title": "Orgullo y prejuicio", "description": "Una novela romántica de Jane Austen que trata sobre la vida y el amor en la sociedad inglesa del siglo XIX.", "genre": "Romance", "author": "Jane Austen"},
    {"title": "El Principito", "description": "Un cuento filosófico de Antoine de Saint-Exupéry sobre un joven príncipe que explora diferentes planetas.", "genre": "Fantasía", "author": "Antoine de Saint-Exupéry"},
    {"title": "Drácula", "description": "Una novela de terror gótica de Bram Stoker sobre el famoso vampiro Conde Drácula.", "genre": "Terror", "author": "Bram Stoker"},
    {"title": "La Odisea", "description": "Una epopeya griega atribuida a Homero que narra las aventuras de Odiseo en su regreso a Ítaca.", "genre": "Historia", "author": "Homero"},
    {"title": "El alquimista", "description": "Una novela de Paulo Coelho sobre la búsqueda espiritual de un pastor andaluz.", "genre": "Autoayuda", "author": "Paulo Coelho"},
    {"title": "El hombre en busca de sentido", "description": "Un libro de Viktor Frankl sobre su experiencia en campos de concentración nazis y su teoría de la logoterapia.", "genre": "Autoayuda", "author": "Viktor Frankl"},
    {"title": "La Divina Comedia", "description": "Una obra maestra de la literatura italiana escrita por Dante Alighieri, que describe el viaje del alma a través del Infierno, el Purgatorio y el Paraíso.", "genre": "Poesía", "author": "Dante Alighieri"},
    {"title": "Matar a un ruiseñor", "description": "Una novela de Harper Lee que aborda temas de racismo e injusticia en el sur de Estados Unidos.", "genre": "Drama", "author": "Harper Lee"},
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
        book_title = request.form['title']
        book_genre = request.form['genre']
        book_author = request.form['author']
        username = session['user_id']

        # Crear el nodo del libro si no existe
        if not graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book_title).data():
            graph.run("CREATE (b:Book {title: $title, genre: $genre, author: $author})",
                      title=book_title, genre=book_genre, author=book_author)

        # Relacionar usuario con el libro leído
        query = """
        MATCH (u:User {username: $username}), (b:Book {title: $title})
        CREATE (u)-[:HAS_READ]->(b)
        """
        graph.run(query, username=username, title=book_title)

        flash("Libro agregado exitosamente")
        return redirect(url_for('dashboard'))
    return render_template('add_book.html', genres=genres)

@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Obtener recomendaciones de libros
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)<-[:HAS_READ]-(other:User)-[:HAS_READ]->(rec:Book)
    WHERE NOT EXISTS((u)-[:HAS_READ]->(rec))
    RETURN rec.title AS title, rec.description AS description, rec.genre AS genre, rec.author AS author, COUNT(*) AS count
    ORDER BY count DESC
    LIMIT 5
    """
    recommendations = graph.run(query, username=username).data()

    return render_template('recommend.html', recommendations=recommendations)

@app.route('/like_book/<title>')
def like_book(title):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Relacionar usuario con el libro likeado
    query = """
    MATCH (u:User {username: $username}), (b:Book {title: $title})
    CREATE (u)-[:LIKED]->(b)
    """
    graph.run(query, username=username, title=title)
    flash("Libro marcado como me gusta")
    return redirect(url_for('recommend'))

@app.route('/unlike_book/<title>')
def unlike_book(title):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['user_id']

    # Eliminar relación de libro likeado
    query = """
    MATCH (u:User {username: $username})-[r:LIKED]->(b:Book {title: $title})
    DELETE r
    """
    graph.run(query, username=username, title=title)
    flash("Libro desmarcado como me gusta")
    return redirect(url_for('liked_books'))

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
        return 'No file part'

    file = request.files['photo']

    if file.filename == '':
        return 'No selected file'

    if file:
        filename = title.replace(' ', '_') + '.jpg'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("Foto subida exitosamente")
        return redirect(url_for('recommend'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

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
     # Novela
    {"title": "Cien años de soledad", "author": "Gabriel García Márquez", "genre": "Novela", "description": "Una saga familiar épica que narra la historia de la familia Buendía en el pueblo ficticio de Macondo."},
    {"title": "Don Quijote de la Mancha", "author": "Miguel de Cervantes", "genre": "Novela", "description": "Las aventuras del ingenioso hidalgo Don Quijote y su fiel escudero Sancho Panza."},
    {"title": "La casa de los espíritus", "author": "Isabel Allende", "genre": "Novela", "description": "Una historia de amor, magia y política en una familia chilena."},
    {"title": "Pedro Páramo", "author": "Juan Rulfo", "genre": "Novela", "description": "La historia de un hombre que busca a su padre en un pueblo fantasma."},
    {"title": "Crónica de una muerte anunciada", "author": "Gabriel García Márquez", "genre": "Novela", "description": "La crónica de un asesinato anunciado en un pequeño pueblo colombiano."},
    
    # Ciencia ficción
    {"title": "1984", "author": "George Orwell", "genre": "Ciencia ficción", "description": "Una distopía sobre un futuro totalitario y el control del pensamiento."},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury", "genre": "Ciencia ficción", "description": "Una sociedad donde los libros están prohibidos y son quemados."},
    {"title": "Neuromante", "author": "William Gibson", "genre": "Ciencia ficción", "description": "La novela que popularizó el concepto del ciberespacio."},
    {"title": "Dune", "author": "Frank Herbert", "genre": "Ciencia ficción", "description": "Una épica saga sobre política, religión y poder en un desierto planetario."},
    {"title": "El hombre en el castillo", "author": "Philip K. Dick", "genre": "Ciencia ficción", "description": "Una historia alternativa donde los nazis ganaron la Segunda Guerra Mundial."},
    
    # Fantasía
    {"title": "El Señor de los Anillos", "author": "J.R.R. Tolkien", "genre": "Fantasía", "description": "La épica aventura de Frodo y sus amigos para destruir el Anillo Único."},
    {"title": "Harry Potter y la piedra filosofal", "author": "J.K. Rowling", "genre": "Fantasía", "description": "La historia del joven mago Harry Potter y su primer año en Hogwarts."},
    {"title": "Juego de Tronos", "author": "George R.R. Martin", "genre": "Fantasía", "description": "La lucha por el trono de hierro en los Siete Reinos."},
    {"title": "La historia interminable", "author": "Michael Ende", "genre": "Fantasía", "description": "Un niño descubre un libro mágico que lo transporta a otro mundo."},
    {"title": "El nombre del viento", "author": "Patrick Rothfuss", "genre": "Fantasía", "description": "La historia de un legendario héroe y mago, Kvothe."},
    
    # Misterio
    {"title": "El nombre de la rosa", "author": "Umberto Eco", "genre": "Misterio", "description": "Un misterio medieval en una abadía italiana."},
    {"title": "El asesinato de Roger Ackroyd", "author": "Agatha Christie", "genre": "Misterio", "description": "Un asesinato en un pequeño pueblo inglés resuelto por Hércules Poirot."},
    {"title": "Sherlock Holmes: El sabueso de los Baskerville", "author": "Arthur Conan Doyle", "genre": "Misterio", "description": "Holmes investiga una leyenda familiar de un perro fantasma."},
    {"title": "Los hombres que no amaban a las mujeres", "author": "Stieg Larsson", "genre": "Misterio", "description": "Un periodista y una hacker investigan una desaparición."},
    {"title": "La sombra del viento", "author": "Carlos Ruiz Zafón", "genre": "Misterio", "description": "Un joven descubre un libro misterioso que lo lleva a una serie de intrigas y secretos."},
    
    # Romance
    {"title": "Orgullo y prejuicio", "author": "Jane Austen", "genre": "Romance", "description": "La historia de amor entre Elizabeth Bennet y el señor Darcy."},
    {"title": "Cumbres borrascosas", "author": "Emily Brontë", "genre": "Romance", "description": "Una trágica historia de amor y venganza en los páramos ingleses."},
    {"title": "Jane Eyre", "author": "Charlotte Brontë", "genre": "Romance", "description": "Una historia de amor y superación personal de una joven huérfana."},
    {"title": "El amor en los tiempos del cólera", "author": "Gabriel García Márquez", "genre": "Romance", "description": "Un amor que perdura a lo largo de los años."},
    {"title": "Bajo la misma estrella", "author": "John Green", "genre": "Romance", "description": "La historia de amor de dos adolescentes con cáncer."},
    
    # Thriller
    {"title": "El código Da Vinci", "author": "Dan Brown", "genre": "Thriller", "description": "Un thriller sobre un misterio religioso escondido en obras de arte."},
    {"title": "El silencio de los corderos", "author": "Thomas Harris", "genre": "Thriller", "description": "Un asesino en serie y un psiquiatra caníbal."},
    {"title": "La chica del tren", "author": "Paula Hawkins", "genre": "Thriller", "description": "Una mujer se ve involucrada en un crimen mientras observa desde el tren."},
    {"title": "Perdida", "author": "Gillian Flynn", "genre": "Thriller", "description": "La desaparición de una mujer y la sospecha sobre su esposo."},
    {"title": "La última oportunidad", "author": "Harlan Coben", "genre": "Thriller", "description": "Un médico busca a su esposa desaparecida."},
    
    # Histórica
    {"title": "Los pilares de la tierra", "author": "Ken Follett", "genre": "Histórica", "description": "La construcción de una catedral en la Inglaterra medieval."},
    {"title": "Guerra y paz", "author": "León Tolstói", "genre": "Histórica", "description": "Una épica historia sobre las guerras napoleónicas en Rusia."},
    {"title": "El médico", "author": "Noah Gordon", "genre": "Histórica", "description": "Un joven que viaja desde Inglaterra a Persia para aprender medicina."},
    {"title": "Viento del Este, Viento del Oeste", "author": "Pearl S. Buck", "genre": "Histórica", "description": "La historia de una mujer china en una época de cambio."},
    {"title": "En el nombre de la rosa", "author": "Umberto Eco", "genre": "Histórica", "description": "Un misterio medieval en una abadía italiana."},
    
    # Biografía
    {"title": "Steve Jobs", "author": "Walter Isaacson", "genre": "Biografía", "description": "La biografía del cofundador de Apple."},
    {"title": "Einstein: Su vida y su universo", "author": "Walter Isaacson", "genre": "Biografía", "description": "La biografía del famoso físico."},
    {"title": "Alexander Hamilton", "author": "Ron Chernow", "genre": "Biografía", "description": "La vida de uno de los padres fundadores de Estados Unidos."},
    {"title": "El diario de Ana Frank", "author": "Ana Frank", "genre": "Biografía", "description": "El diario de una niña judía escondida durante la Segunda Guerra Mundial."},
    {"title": "Mi historia", "author": "Michelle Obama", "genre": "Biografía", "description": "Las memorias de la ex primera dama de Estados Unidos."},
    
    # Autobiografía
    {"title": "Long Walk to Freedom", "author": "Nelson Mandela", "genre": "Autobiografía", "description": "La autobiografía del líder sudafricano."},
    {"title": "I Know Why the Caged Bird Sings", "author": "Maya Angelou", "genre": "Autobiografía", "description": "La primera parte de la autobiografía de la poeta y activista."},
    {"title": "La historia de mi vida", "author": "Helen Keller", "genre": "Autobiografía", "description": "La vida de la escritora y activista sorda y ciega."},
    {"title": "Mi vida", "author": "Bill Clinton", "genre": "Autobiografía", "description": "Las memorias del expresidente de Estados Unidos."},
    {"title": "El largo camino hacia la libertad", "author": "Nelson Mandela", "genre": "Autobiografía", "description": "La historia de lucha contra el apartheid."},
    
    # Infantil
    {"title": "Harry Potter y la piedra filosofal", "author": "J.K. Rowling", "genre": "Infantil", "description": "La historia del joven mago Harry Potter y su primer año en Hogwarts."},
    {"title": "El principito", "author": "Antoine de Saint-Exupéry", "genre": "Infantil", "description": "Las aventuras de un pequeño príncipe en distintos planetas."},
    {"title": "Charlie y la fábrica de chocolate", "author": "Roald Dahl", "genre": "Infantil", "description": "La historia de un niño que gana un tour por una increíble fábrica de chocolate."},
    {"title": "Matilda", "author": "Roald Dahl", "genre": "Infantil", "description": "Una niña prodigio con poderes telequinéticos."},
    {"title": "Alicia en el país de las maravillas", "author": "Lewis Carroll", "genre": "Infantil", "description": "Las aventuras de una niña en un mundo fantástico."},
]

# Crear nodos de libros en Neo4j
for book in books:
    graph.run("""
    MERGE (b:Book {title: $title})
    SET b.description = $description, b.genre = $genre, b.author = $author
    """, title=book['title'], description=book['description'], genre=book['genre'], author=book['author'])


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
        book_author = request.form['author']
        book_genre = request.form['genre']
        book_description = request.form['description']
        username = session['user_id']
        
        # Crear el libro si no existe
        if not graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book_title).data():
            graph.run("CREATE (b:Book {title: $title, author: $author, genre: $genre, description: $description})", 
                      title=book_title, author=book_author, genre=book_genre, description=book_description)
        
        # Relacionar usuario con el libro leído
        query = """
        MATCH (u:User {username: $username}), (b:Book {title: $book_title})
        CREATE (u)-[:HAS_READ]->(b)
        """
        graph.run(query, username=username, book_title=book_title)
        
        return redirect(url_for('dashboard'))
    return render_template('add_book.html')


@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session['user_id']
    
    # Obtener recomendaciones de libros basadas en género o autor
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)
    WITH DISTINCT u, b.genre AS genre, b.author AS author
    MATCH (other:User)-[:HAS_READ]->(rec:Book)
    WHERE (rec.genre = genre OR rec.author = author)
    AND NOT EXISTS((u)-[:HAS_READ]->(rec))
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

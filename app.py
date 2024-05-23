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
        file = request.files['image']

        # Verificar si el libro ya existe en la base de datos
        book_exists = graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book_title).data()
        
        if not book_exists:
            if file:
                filename = book_title.replace(' ', '_') + '.jpg'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = 'default.jpg'
            
            # Crear nodo de libro en Neo4j
            graph.run(
                "CREATE (b:Book {title: $title, author: $author, genre: $genre, description: $description, image: $image})", 
                title=book_title, 
                author=book_author, 
                genre=book_genre, 
                description=book_description,
                image=filename
            )
        
        username = session['user_id']
        
        # Relacionar usuario con el libro leído
        query = """
        MATCH (u:User {username: $username}), (b:Book {title: $book_title})
        CREATE (u)-[:HAS_READ]->(b)
        """
        graph.run(query, username=username, book_title=book_title)
        
        flash("Libro agregado exitosamente")
        return redirect(url_for('dashboard'))
    
    return render_template('add_book.html', genres=genres)

@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session['user_id']
    
    # Obtener el género y el autor de los libros que el usuario ha leído
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)
    RETURN b.genre AS genre, b.author AS author
    """
    user_books = graph.run(query, username=username).data()

    if not user_books:
        return render_template('recommend.html', recommendations=[])

    # Obtener los géneros y autores de los libros leídos por el usuario
    genres = [book['genre'] for book in user_books]
    authors = [book['author'] for book in user_books]

    # Obtener recomendaciones basadas en género y autor
    recommendations_query = """
    MATCH (b:Book)
    WHERE b.genre IN $genres OR b.author IN $authors
    RETURN b.title AS title, b.description AS description, b.genre AS genre, b.author AS author, b.image AS image
    LIMIT 10
    """
    recommendations = graph.run(recommendations_query, genres=genres, authors=authors).data()

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
    RETURN b.title AS title, b.description AS description, b.genre AS genre, b.author AS author, b.image AS image
    """
    liked_books = graph.run(query, username=username).data()

    return render_template('liked_books.html', liked_books=liked_books)

@app.route('/all_books')
def all_books():
    query = "MATCH (b:Book) RETURN b"
    result = graph.run(query).data()
    
    books = []
    for record in result:
        book = record['b']
        books.append({
            'title': book['title'],
            'author': book.get('author', 'Desconocido'),
            'genre': book.get('genre', 'Desconocido'),
            'description': book.get('description', 'No hay descripción disponible'),
            'image': book.get('image', 'default.jpg')
        })
    
    return render_template('all_books.html', books=books)

@app.route('/upload_photo/<title>', methods=['POST'])
def upload_photo(title):
    if 'photo' not in request.files:
        flash('No se seleccionó ningún archivo')
        return redirect(request.url)
    file = request.files['photo']
    if file.filename == '':
        flash('No se seleccionó ningún archivo')
        return redirect(request.url)
    if file:
        filename = title.replace(' ', '_') + '.jpg'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        query = "MATCH (b:Book {title: $title}) SET b.image = $filename"
        graph.run(query, title=title, filename=filename)
        flash('Foto subida exitosamente')
        return redirect(url_for('all_books'))

@app.route('/delete_book/<title>', methods=['POST'])
def delete_book(title):
    query = "MATCH (b:Book {title: $title}) DETACH DELETE b"
    graph.run(query, title=title)
    flash('Libro eliminado exitosamente')
    return redirect(url_for('all_books'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

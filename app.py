from flask import Flask, render_template, request, redirect, url_for, session
from py2neo import Graph, Node, Relationship
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Configuración de la base de datos Neo4j
url = "bolt://localhost:7687"
username = "neo4j"
password = "PDR2024ED"
try:
    graph = Graph(url, auth=(username, password))
except Exception as e:
    print(f"Error al conectar a Neo4j: {e}")

# Lista de libros con descripciones
books = [
    {"title": "Cien años de soledad", "description": "Novela de Gabriel García Márquez que narra la historia de la familia Buendía a lo largo de varias generaciones."},
    {"title": "Don Quijote de la Mancha", "description": "Obra cumbre de la literatura española escrita por Miguel de Cervantes, relata las aventuras del ingenioso hidalgo Don Quijote."},
    {"title": "La sombra del viento", "description": "Novela de Carlos Ruiz Zafón ambientada en la Barcelona de mediados del siglo XX, donde un joven descubre un misterioso libro."},
    {"title": "El amor en los tiempos del cólera", "description": "Novela de Gabriel García Márquez que narra una historia de amor que perdura a lo largo de décadas."},
    {"title": "Ficciones", "description": "Colección de cuentos de Jorge Luis Borges que exploran temas como los laberintos, los espejos y los sueños."},
    {"title": "Rayuela", "description": "Novela de Julio Cortázar que invita al lector a saltar de un capítulo a otro, creando múltiples caminos de lectura."},
    {"title": "La casa de los espíritus", "description": "Novela de Isabel Allende que narra la historia de la familia Trueba a lo largo de varias generaciones en Chile."},
    {"title": "Pedro Páramo", "description": "Novela de Juan Rulfo que narra la historia de un hombre que viaja al pueblo de Comala en busca de su padre."},
    {"title": "Crónica de una muerte anunciada", "description": "Novela de Gabriel García Márquez que cuenta la historia del asesinato de Santiago Nasar en un pequeño pueblo colombiano."},
    {"title": "El túnel", "description": "Novela de Ernesto Sabato que narra la historia de un pintor obsesionado con una mujer a la que cree comprender profundamente."},
    {"title": "La ciudad y los perros", "description": "Novela de Mario Vargas Llosa que describe la vida de los cadetes en una academia militar en Lima, Perú."},
]

# Crear nodos de libros en Neo4j si no existen
for book in books:
    if not graph.run("MATCH (b:Book {title: $title}) RETURN b", title=book['title']).data():
        graph.run("CREATE (b:Book {title: $title, description: $description})", title=book['title'], description=book['description'])

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        username = session['user_id']
        
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
    print(f"Usuario actual: {username}")
    
    # Obtener recomendaciones de libros
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)<-[:HAS_READ]-(other:User)-[:HAS_READ]->(rec:Book)
    WHERE NOT (u)-[:HAS_READ]->(rec)
    RETURN rec.title AS title, rec.description AS description, COUNT(*) AS count
    ORDER BY count DESC
    LIMIT 10
    """
    recommendations = graph.run(query, username=username).data()
    
    print("Recomendaciones obtenidas:", recommendations)  # Añadir impresión para verificar los datos
    
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
    
    return redirect(url_for('recommend'))

@app.route('/liked_books')
def liked_books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session['user_id']
    
    # Obtener libros likeados
    query = """
    MATCH (u:User {username: $username})-[:LIKED]->(b:Book)
    RETURN b.title AS title
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
        return redirect(url_for('recommend'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

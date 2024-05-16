from flask import Flask, request, render_template, redirect, url_for, session
from py2neo import Graph
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Conectar a Neo4j
url = "bolt://localhost:7687"
username = "neo4j"
password = "PDR2024ED"
graph = Graph(url, auth=(username, password))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        # Insertar el usuario en la base de datos
        query = """
        CREATE (u:User {user_id: $user_id, username: $username, password: $password})
        """
        graph.run(query, user_id=user_id, username=username, password=password)
        
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verificar el usuario en la base de datos
        user = graph.run("MATCH (u:User {username: $username}) RETURN u", username=username).data()
        if user and check_password_hash(user[0]['u']['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        
        return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        book_title = request.form['book_title']
        username = session['username']
        
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
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # Obtener recomendaciones de libros
    query = """
    MATCH (u:User {username: $username})-[:HAS_READ]->(b:Book)<-[:HAS_READ]-(other:User)-[:HAS_READ]->(rec:Book)
    WHERE NOT (u)-[:HAS_READ]->(rec)
    RETURN rec.title AS title, COUNT(*) AS count
    ORDER BY count DESC
    LIMIT 5
    """
    recommendations = graph.run(query, username=username).data()
    
    return render_template('recommend.html', recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

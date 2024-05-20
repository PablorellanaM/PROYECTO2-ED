from flask import Flask, render_template, request, redirect, url_for, session
from py2neo import Graph, Node, Relationship
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

url = "bolt://localhost:7687"
username = "neo4j"
password = "PDR2024ED"
graph = Graph(url, auth=(username, password))

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

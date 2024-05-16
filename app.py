from flask import Flask, request, render_template, redirect, url_for
from py2neo import Graph

app = Flask(__name__)

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
        password = request.form['password']
        
        # Insertar el usuario en la base de datos
        query = """
        CREATE (u:User {user_id: $user_id, username: $username, password: $password})
        """
        graph.run(query, user_id=user_id, username=username, password=password)
        
        return redirect(url_for('index'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)

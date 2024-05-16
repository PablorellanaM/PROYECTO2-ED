from py2neo import Graph
import sys

url = "bolt://localhost:7687"  # Asegúrate de que esta URL sea correcta
username = "neo4j"
password = "PDR2024ED"
graph = Graph(url, auth=(username, password))

# Función para recomendar libros basada en contenido y colaboración
def recomendar_libros(usuario_id):
    # Filtrado colaborativo: Encontrar usuarios con gustos similares y sus recomendaciones
    query_similares = """
    MATCH (u1:User)-[:RATED]->(b)<-[:RATED]-(u2:User)
    WHERE u1.user_id = $usuario_id AND u1 <> u2
    RETURN u2, count(b) AS sharedBooks
    ORDER BY sharedBooks DESC LIMIT 5
    """
    similares = graph.run(query_similares, usuario_id=usuario_id).data()
    
    # Filtrado basado en contenido: Recomendar libros con tags similares a los que el usuario ha valorado
    query_recomendaciones = """
    MATCH (u:User)-[:RATED]->(b:Book)-[:TAGGED_WITH]->(t:Tag),
          (b2:Book)-[:TAGGED_WITH]->(t) WHERE u.user_id = $usuario_id AND NOT (u)-[:RATED]->(b2)
    RETURN b2 AS book, COLLECT(t.description) AS tags, AVG(b2.rating) AS avgRating
    ORDER BY avgRating DESC LIMIT 5
    """
    recomendaciones = graph.run(query_recomendaciones, usuario_id=usuario_id).data()
    
    # Combinar resultados y eliminar duplicados
    libros_recomendados = {rec['book']['title']: rec for rec in recomendaciones}
    for similar in similares:
        usuario_similar = similar['u2']['user_id']
        recs_de_similar = graph.run(query_recomendaciones, usuario_id=usuario_similar).data()
        for rec in recs_de_similar:
            libro = rec['book']['title']
            if libro not in libros_recomendados:
                libros_recomendados[libro] = rec
    
    return libros_recomendados.values()

# Ejemplo de uso
usuario_id = 1  # Supongamos que este es el ID de un usuario en la base de datos
recomendaciones = recomendar_libros(usuario_id)
for rec in recomendaciones:
    print(f"Libro: {rec['book']['title']}, Tags: {rec['tags']}, Rating Promedio: {rec['avgRating']}")
# python3 function_tools.py

from anthropic import Anthropic
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import models, QdrantClient
from qdrant_client.models import PointStruct

import os
import pandas as pd
import pytz
import streamlit as st
import time

deploy = False

if deploy:
    anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
    MODEL_NAME = st.secrets["ANTHROPIC_MODEL_NAME"]
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    OPENAI_EMBEDDINGS_MODEL = st.secrets["OPENAI_EMBEDDINGS_MODEL"]
    VECTOR_DIMENSION = int(st.secrets["VECTOR_DIMENSION"])
    N_SIMILARITY = int(st.secrets["N_SIMILARITY"])
    QDRANT_URL = st.secrets["QDRANT_URL"]
    QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]
    QDRANT_COLLECTION_NAME = st.secrets["QDRANT_COLLECTION_NAME"]

else:
    load_dotenv()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME")
    openai_api_key = os.getenv('OPENAI_API_KEY')
    OPENAI_EMBEDDINGS_MODEL = os.getenv('OPENAI_EMBEDDINGS_MODEL')
    VECTOR_DIMENSION = int(os.getenv('VECTOR_DIMENSION', 1024))
    N_SIMILARITY = int(os.getenv('N_SIMILARITY', 3))
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

client = Anthropic(api_key=anthropic_api_key)
openai_client = OpenAI(api_key=openai_api_key)
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

dict_clientes_datos = {}

def categorizador_datosCompletos(tool_input, client=client, MODEL_NAME=MODEL_NAME):
    system_prompt = f"""
    Vas a recibir los datos de un cliente que esta haciendo una cita para mas informes. Tienes 
    dos tareas:

    -Determinar si los datos estàn completos o no. Un dato completo es aquel distinto de <UNKNOWN> y debe 
    contener al menos un nombre y un apellido. 'Usuario' no es un nombre completo.
    -Si no están completos, indicar qué datos son los faltantes.

    Unicamente response info_completa en caso de tener todos los datos o Datos incompletos, falta
    el dato 'dato_faltante'.

    """

    datos_cliente = f"""
    Los datos son: 
    -nombre_completo: {tool_input['nombre_completo']}
    -correo: {tool_input['correo']}
    -fecha_cita: {tool_input['fecha_cita']}

    """

    message = {
        'role': 'user',
        'content': f'Datos del cliente: \n\n {datos_cliente}'
    }

    answer = client.messages.create(
        model=MODEL_NAME,
        messages=[message],
        max_tokens=5192,
        system=system_prompt,
        temperature=0.1
    )

    response = answer.content[0].text
    return {
        'answer':response
    }

def create_embeddings(texto, client=openai_client, model=OPENAI_EMBEDDINGS_MODEL, dim=VECTOR_DIMENSION):
    respuesta = client.embeddings.create(
        input=texto,
        model=model,
        dimensions=dim,
    )

    return {
        'answer':respuesta.data[0].embedding
    }

def insert_info_business(secciones, client_qdrant=qdrant_client, COLECCION = QDRANT_COLLECTION_NAME, dim=VECTOR_DIMENSION):

    collections = client_qdrant.get_collections().collections
    collection_names = [collection.name for collection in collections]

    if COLECCION not in collection_names:
        client_qdrant.create_collection(
            collection_name=COLECCION,
            vectors_config={
                "embeddings": {
                    "size": dim,
                    "distance": "Cosine"
                }
            }
        )
        print(f"Colección '{COLECCION}' creada exitosamente.")

    puntos = []

    for index, seccion in enumerate(secciones):

        vector = create_embeddings(seccion["texto"]) 

        punto = PointStruct(
            id=index,
            vector={"embeddings": vector['answer']},
            payload={
                "nombre": seccion["nombre"],
                "texto": seccion["texto"]
            }
        )

        puntos.append(punto)

    client_qdrant.upsert(collection_name=COLECCION, points=puntos)
    print(f"{len(puntos)} secciones insertadas en Qdrant.")

def get_text_by_relevance(consulta, cliente=qdrant_client, coleccion=QDRANT_COLLECTION_NAME, n=N_SIMILARITY):
    texto_relevante = []
    embedding = create_embeddings(consulta)

    search_params = models.SearchParams(
        hnsw_ef=128,
        exact=False
    )

    resultado_busqueda = cliente.search(
        collection_name=coleccion,
        query_vector= models.NamedVector(
            name="embeddings",
            vector=embedding['answer']
        ),
        search_params=search_params,
        limit=n
    )
    print(resultado_busqueda)

    for resultado in resultado_busqueda:
        texto_relevante.append(
            (resultado.payload["nombre"], resultado.payload["texto"], resultado.score)
        )

    texto_relevante.sort(key=lambda x: x[2], reverse=True)
    return texto_relevante[:n]

def get_mexico_city_time():
    timestamp = time.time()
    utc_time = datetime.utcfromtimestamp(timestamp)
    mexico_city_timezone = pytz.timezone('America/Mexico_City')
    mexico_city_time = utc_time.astimezone(mexico_city_timezone)
    formatted_time = mexico_city_time.strftime('%A, %Y-%m-%d %H:%M')
    return formatted_time

def agregar_punto_individual(texto, nombre, client_qdrant=qdrant_client, COLECCION=QDRANT_COLLECTION_NAME):
    try:
        # Obtener el último ID de la colección
        resultado = client_qdrant.scroll(
            collection_name=COLECCION,
            limit=1,
            with_payload=False,
            with_vectors=False,
            order_by="id"
        )

        # Si hay puntos, tomar el último ID y sumar 1, sino empezar en 0
        if resultado[0]:
            ultimo_id = max([punto.id for punto in resultado[0]]) if resultado[0] else -1
            nuevo_id = ultimo_id + 1
        else:
            nuevo_id = 0

        vector = create_embeddings(texto)

        punto = PointStruct(
            id=nuevo_id,
            vector={"embeddings": vector['answer']},
            payload={
                "nombre": nombre,
                "texto": texto
            }
        )

        client_qdrant.upsert(collection_name=COLECCION, points=[punto])

        return {"success": True, "id": nuevo_id, "message": "Información agregada de forma exitosa."}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def read_spreadsheets_data_and_generate_dict_embeds(file_path):
    df = pd.read_excel(file_path)

    puntos_embeds = []
    for _, row in df.iterrows():
        texto_embed = f"""Enfermedad: {row['Enfermedad']} \n
        Variedad: {row['Variedad']} \n
        Ubicación: {row['Ubicacion']} \n
        Patógeno: {row['Patogeno']}
        """

        dict_por_enfermedad = {
            'texto_embeddings': texto_embed,
            'datos_completos_punto': {
                'enfermedad': row['Enfermedad'],
                'variedad': row['Variedad'],
                'ubicacion': row['Ubicacion'],
                'municipio': row['Municipio'],
                'sintomas': row['Sintomas'],
                'patogeno': row['Patogeno'],
                'cultivo': row['Cultivo'],
                'competencia': row['Competencia'],
                'grado_dificultad_erradicar': row['Grado de dificultad para erradicar']
            }
        }
        puntos_embeds.append(dict_por_enfermedad)

    return puntos_embeds

def insert_datos_pauta(secciones, client_qdrant=qdrant_client, COLECCION=QDRANT_COLLECTION_NAME, dim=VECTOR_DIMENSION):
    collections = client_qdrant.get_collections().collections
    collection_names = [collection.name for collection in collections]

    if COLECCION not in collection_names:
        client_qdrant.create_collection(
            collection_name=COLECCION,
            vectors_config={
                "embeddings": {
                    "size": dim,
                    "distance": "Cosine"
                }
            }
        )
        print(f"Colección '{COLECCION}' creada exitosamente.")

    puntos = []
    for index, seccion in enumerate(secciones):
        vector = create_embeddings(seccion["texto_embeddings"]) 

        punto = PointStruct(
            id=index,
            vector={"embeddings": vector['answer']},
            payload=seccion['datos_completos_punto']
            # payload={
            #     "nombre": seccion["nombre"],
            #     "texto": seccion["texto"]
            # }
        )
        puntos.append(punto)

    client_qdrant.upsert(collection_name=COLECCION, points=puntos)
    print(f"{len(puntos)} secciones insertadas en Qdrant.")

if __name__ == "__main__":

    file_path = "datos_pauta.xlsx"
    datos_embeddear = read_spreadsheets_data_and_generate_dict_embeds(file_path)
    insert_datos_pauta(datos_embeddear)
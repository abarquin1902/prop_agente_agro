# python3 function_tools.py

from anthropic import Anthropic
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import models, QdrantClient
from qdrant_client.models import PointStruct

import os
import pytz
import streamlit as st
import time

deploy = True

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

if __name__ == "__main__":

    informacion = [
        {
            "nombre": "Información General del Negocio",
            "texto": """
            Nosotros somos Agrobotanix , una empresa dedicada a brindar soluciones 
            para poder curar las enfermedades de berries mas comunes en cultivos 
            y garantizamos que no hacen daño a los polinizadores ni dejan 
            infertil la tierra.
            Nuestro producto Agroquer , garantiza que con dos simples 
            aplicaciones a tus cultivos, podrás eliminar enfermedades como la 
            microfamina y la phytoptora.
            """
        },
        {
            "nombre": "PHYTOPHTHORA",
            "texto": """
            Phytophthora es un género de oomicetos (organismos similares a hongos) 
            que causa enfermedades devastadoras en berries. Es conocido como "el 
            destructor de plantas" y prospera en condiciones de humedad.

            Síntomas por Cultivo:
            FRESA:

            Marchitez súbita de plantas
            Pudrición de corona (color café-rojizo)
            Raíces con apariencia de "rata comida" (raicillas laterales muertas)
            Pudrición de frutos (manchas café con textura correosa)
            Hojas viejas se tornan rojas o amarillas

            ARÁNDANO:

            Crecimiento débil y amarillamiento
            Pudrición de raíces (color negro, textura blanda)
            Marchitez en temporada de calor
            Muerte regresiva de ramas
            Reducción drástica de producción

            FRAMBUESA/ZARZAMORA:

            Pudrición de raíz y corona
            Marchitez de cañas
            Amarillamiento progresivo
            Muerte de plantas en manchones

            Productos existentes preventivos (que se suelen aplicar antes de la infección):

            Fosetil-Al (Aliette)
            Ácidos fosforosos (Fosphite, K-Phite)
            Metalaxil/Mefenoxam (Ridomil)
            Fluopicolide + Fosetil-Al (Presidio)

            Si el usuario menciona que usa cualquiera de estos o si pregunta por los 
            mas comunes en el mercado , debes de mencionar estos, pero mencionar 
            que el agroquer va a ahorrarles millones de pesos y aparte hace que el conocimiento 
            sobre como sobrevivir al producto no se pase geneticamente a las futuras generaciones.

            Regiones de riesgo en México:

            Michoacán, Jalisco, Guanajuato: Temporada de lluvias (junio-octubre)
            Baja California: Menos problema por clima seco
            Zonas con riego por gravedad o aspersión: Mayor riesgo

            Puedes mencionar estas si el usuario pregunta y si el usuario 
            menciona que es de alguna de estas regiones, debes de decirle que 
            le recomiendas agendar una cita para poder prevenir problemas en 
            sus cultivos.

            """
        },
        {
            "nombre": "Xanthomonas",
            "texto": """
            Xanthomonas es un género de bacterias gram-negativas 
            que causa enfermedades en muchos cultivos. En berries, la 
            especie más importante es: Xanthomonas fragariae (fresa)

            Síntomas en :
            Manchas pequeñas café oscuro en aquenios (semillas)
            Puede afectar calidad y vida de anaquel
            En casos severos: pudrición secundaria de frutos

            Productos existentes:
            Hidróxido de cúprico (Kocide, Champion)
            Oxicloruro de cobre
            Sulfato de cobre pentahidratado

            Si el usuario menciona que usa cualquiera de estos o si pregunta por los 
            mas comunes en el mercado , debes de mencionar estos, pero mencionar 
            que el agroquer va a ahorrarles millones de pesos y aparte hace que el conocimiento 
            sobre como sobrevivir al producto no se pase geneticamente a las futuras generaciones.

            Regiones de mayor riesgo:
            Michoacán (Zamora, Los Reyes): Temporada fresca y lluviosa
            Guanajuato (Irapuato): Primavera-otoño
            Baja California (Zona costa): Menos problema pero puede ocurrir
            Jalisco: En zonas de riego por aspersión

            Puedes mencionar estas si el usuario pregunta y si el usuario 
            menciona que es de alguna de estas regiones, debes de decirle que 
            le recomiendas agendar una cita para poder prevenir problemas en 
            sus cultivos.

            """
        }
    ]
    
    insert_info_business(informacion)

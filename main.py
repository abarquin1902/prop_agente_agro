# streamlit run main.py

from anthropic import Anthropic
from dotenv import load_dotenv
from function_tools import (
    get_text_by_relevance,
    get_mexico_city_time, 
    categorizador_datosCompletos, 
    agregar_punto_individual
)
from supabase import create_client, Client
from system_prompt import prompt_first_response, prompt_saludo
from tools import tools

import base64
import httpx
import os
import streamlit as st
import time
import uuid

deploy = False

if deploy:
    anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
    MODEL_NAME = st.secrets["ANTHROPIC_MODEL_NAME"]
    supabase_api_key = st.secrets["SUPABASE_API_KEY"]
    supabase_url = st.secrets["SUPABASE_URL"]

else:
    load_dotenv()
    anthropic_api_key: str = os.getenv('ANTHROPIC_API_KEY')
    MODEL_NAME = os.getenv('ANTHROPIC_MODEL_NAME')
    supabase_api_key = os.getenv('SUPABASE_API_KEY')
    supabase_url = os.getenv('SUPABASE_URL')

client = Anthropic(api_key=anthropic_api_key)
WEBHOOK_RENDER = ""
supabase_client: Client = create_client(supabase_url, supabase_api_key)

def guardar_mensaje(session_id, telefono, tipo, mensaje,supabase=supabase_client):
    supabase.table('tbl_agrobotanix').insert({
        'session_id': session_id,
        'telefono': telefono,
        'tipo': tipo,
        'mensaje': mensaje
    }).execute()
    print("Menssaje almacenado con éxito en Supabase.")

prompt_first_response += f'Esta es la fecha actual: {get_mexico_city_time()}'

def responder_usuario(messages, query, telefono="555555555", id_conversacion="", system_prompt=prompt_first_response, model_name=MODEL_NAME, url_base=WEBHOOK_RENDER):

    data = {"body": query}

    new_messages = messages + [
        {"role": "user", "content": data["body"]}
    ]

    input_tokens = 0
    output_tokens = 0

    response = client.messages.create(
        system=system_prompt,
        model=model_name,
        messages=new_messages,
        max_tokens=4096,
        tools=tools,
        tool_choice={"type": "any"}
    )

    input_tokens += response.usage.input_tokens
    output_tokens += response.usage.output_tokens

    while response.stop_reason == 'tool_use':

        new_messages.append(
            {"role": "assistant", "content": response.content})

        try:
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input
            # print('tool_use', tool_use)
            # print('tool_name', tool_name)
        except:
            print('Error')

        if 'saludo' in tool_name.lower():
            content = prompt_saludo

        elif 'informacion_general' in tool_name.lower():
            # print('Estoy en info gral')
            texto = tool_input['consulta']
            content = str(get_text_by_relevance(texto))
            print(content)

        elif 'reservar' in tool_name.lower():
            ans_cat = categorizador_datosCompletos(tool_input)['answer']
            if 'info_completa' in ans_cat.lower():
                user_data = {
                    "nombre": tool_input['nombre_completo'],
                    "email": tool_input['correo'],
                    "fecha_cita": tool_input['fecha_cita'],
                    "telefono": telefono
                }

                # content = "Lo siento, no hay habitaciones disponibles del tipo solicitado para esas fechas. ¿Quieres probar con otro tipo o en otras fechas?"
                content = "Tu cita ha sido agendada de forma exitosa."
            else:
                content = ans_cat
        # print('content', content)
        tool_response = {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": content
                    }
                ]
            }
        new_messages.append(tool_response)

        response = client.messages.create(
            system=system_prompt,
            model=model_name,
            messages=new_messages,
            max_tokens=4096,
            tools=tools,
        )
        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens
        # print(response)
    
    return response.content[0].text, new_messages

    # return {
    #     "answer": response.content[0].text,
    #     "output": response.content,
    #     "input_tokens": input_tokens,
    #     "output_tokens": output_tokens,
    #     'model_name':model_name,
    #     'id_conversacion':id_conversacion
    # }

st.set_page_config(page_title="Agente Agrobotanix", layout="wide")

with st.sidebar:
    st.header("🔧 Conocimientos del Agente")
    
    with st.expander("➕ Agregar información"):
        nuevo_nombre = st.text_input("Nombre/Título:", key="nombre_nuevo")
        nuevo_texto = st.text_area("Texto a agregar:", height=150, key="texto_nuevo")
        
        if st.button("💾 Guardar en colección", type="primary"):
            if nuevo_texto and nuevo_nombre:
                with st.spinner("Guardando..."):
                    resultado = agregar_punto_individual(nuevo_texto, nuevo_nombre)
                    
                    if resultado["success"]:
                        st.success(f"✅ Información agregada con ID: {resultado['id']}")
                        # Limpiar campos
                        st.session_state.nombre_nuevo = ""
                        st.session_state.texto_nuevo = ""
                    else:
                        st.error(f"❌ {resultado['message']}")
            else:
                st.warning("⚠️ Por favor completa ambos campos")
    
    with st.expander("🗑️ Eliminar información"):
        # Falta la funcion de qdrant para poder eliminar un punto 
        pass

st.title("Conversa conmigo - Agrobotanix")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "telefono" not in st.session_state:
    st.session_state.telefono = "555555555"

for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu mensaje"):
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    guardar_mensaje(st.session_state.session_id, st.session_state.telefono, 'user', prompt)

    with st.chat_message("assistant"):
        response_text, updated_messages = responder_usuario(st.session_state.messages, prompt)
        st.markdown(response_text)

    st.session_state.messages = updated_messages
    st.session_state.display_messages.append({"role": "assistant", "content": response_text})

    guardar_mensaje(st.session_state.session_id, st.session_state.telefono, 'assistant', response_text)
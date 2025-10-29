# python3 agente_agro.py

from anthropic import Anthropic
from dotenv import load_dotenv
from system_prompt import prompt_first_response, prompt_saludo
from function_tools import (
    get_text_by_relevance,
    get_mexico_city_time, 
    categorizador_datosCompletos
)
from tools import tools

import base64
import httpx
import os
import time

load_dotenv()

anthropic_api_key: str = os.getenv('ANTHROPIC_API_KEY')
MODEL_NAME = os.getenv('ANTHROPIC_MODEL_NAME')
client = Anthropic(api_key=anthropic_api_key)
WEBHOOK_RENDER = ""

prompt_first_response += f'Esta es la fecha actual: {get_mexico_city_time()}'

def responder_usuario(messages, data, telefono, id_conversacion="", system_prompt=prompt_first_response, model_name=MODEL_NAME, url_base=WEBHOOK_RENDER):

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
            print('Estoy en info gral')
            # print(tool_use)
            texto = tool_input['consulta']
            content = str(get_text_by_relevance(texto))
            print(content)

        elif 'reservar' in tool_name.lower():
            ans_cat = categorizador_datosCompletos(tool_input)
            if 'info_completa' in ans_cat.lower():
                fecha_inicio = tool_input['fecha_inicio']
                fecha_fin = tool_input['fecha_fin']
                huesped_data = {
                    "nombre": tool_input['nombre_completo'],
                    "email": tool_input['correo'],
                    "telefono": telefono,
                    "documento": ''
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

    return {
        "answer": response.content[0].text,
        "output": response.content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        'model_name':model_name,
        'id_conversacion':id_conversacion
    }

if __name__ == "__main__":

    messages = []
    while True:
        query = input("\nUsuario (escribe 'salir' para terminar): ")

        if query.lower().strip() in ['salir']:
            print("¡Hasta luego!")
            break

        data = {
            'type': 'text',
            'body': query
        }

        answer = responder_usuario(
            messages=messages,
            data=data,
            telefono="5566098295",
            id_conversacion="fff"
        )

        respuesta = answer
        print(f"\nAsistente: {respuesta['answer']}")
        # messages.append({'role': 'assistant', 'content': answer['answer']['respuesta']})
        messages.append({'role': 'assistant', 'content': answer['answer']})

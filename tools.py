# python3 tools.py

tools = [
    {
        'name': 'saludo',
        'description': 'Función para saludar al usuario inicialmente.',
        'input_schema': {
                'type': 'object',
                'properties': {
                    'saludo': {
                        'type': 'string',
                        'description': 'Saludo del cliente.'
                    }
                },
            'required': ['saludo']
        }
    },
    {
        'name': 'informacion_general',
        'description': 'Función para ofrecer información general del negocio / responder dudas al cliente.',
        'input_schema': {
                'type': 'object',
                'properties': {
                    'consulta': {
                        'type': 'string',
                        'description': 'Consulta del cliente sobre el negocio / dudas sobre cultivos/plagas.'
                    }
                },
            'required': ['consulta']
        }
    },
    {
        'name': 'reservar',
        'description': 'Función para obtener la informacion del cliente cuando quiere reservar una habitacion',
        'input_schema': {
            'type': 'object',
            'properties': {
                'nombre_completo': {
                    'type': 'string',
                    'description': 'Nombre completo del cliente. Al menos un nombre y un apellido'
                },
                'correo': {
                    'type': 'string',
                    'description': 'Correo electronico del cliente.'
                },
                'fecha_cita': {
                    'type': 'string',
                    'description': 'Fecha y hora propuesta para la cita. Formato: YYYY-MM-DD HH:MM',
                }
            },
            'required': ['nombre_completo', 'correo', 'fecha_cita']
        }
    },
]

registrar_gastos_tools = [
    {
        'name': 'obtener_datos_gasto',
        'description': 'Función para obtener los datos relacionados con un gasto,',
        'input_schema': {
                'type': 'object',
                'properties': {
                    'categoria': {
                        'type': 'string',
                        'description': 'El nombre de la categoría'
                    },
                    'categoria_id': {
                        'type': 'string',
                        'description': 'El id de la categoría elegida, dado por las opciones presentadas.'
                    },
                    'cuenta': {
                        'type': 'string',
                        'description': 'El nombre de la cuenta'
                    },
                    'cuenta_id': {
                        'type': 'string',
                        'description': 'El id de la cuenta, dado por las opciones presentadas.'
                    },
                    'monto': {
                        'type': 'string',
                        'description': 'El monto del gasto a registrar en MXN. ex. 50 MXN, etc.'
                    },
                    'razonamiento_categoria': {
                        'type': 'string',
                        'description': 'La razón de por qué se eligió la categoría.'
                    },
                    'se_encontraron_todos_los_datos': {
                        'type': 'boolean',
                        'description': 'True si se encontraron correctamente todas las cuentas y ids de la lista de cuentas, False si no.'
                    },
                    'razonamiento_se_encontraron_todos_los_datos': {
                        'type': 'string',
                        'description': 'La razón de por qué se eligió True o False en "se_encontraron_todos_los_datos".'
                    },
                },
            'required': ['categoria', 'categoria_id', 'cuenta', 'cuenta_id', 'monto', 'razonamiento_categoria', 'se_encontraron_todos_los_datos', 'razonamiento_se_encontraron_todos_los_datos']
        }
    },
]

registrar_lugar_o_alimento = [
    {
        'name': 'obtener_datos_lugar_o_alimento',
        'description': 'Función para obtener los datos relacionados con el registro de restaurante, lugar de entretenimiento o un alimento.',
        'input_schema': {
                'type': 'object',
                'properties': {
                    'nombre': {
                        'type': 'string',
                        'description': 'Nombre del lugar, alimento que se desea registrar. ex. "Don Horacio", "Hachas MX", "pechugas empanizadas", etc.'
                    },
                    'tipo_registro': {
                        'type': 'string',
                        'enum': ['restaurante', 'lugar de entretenimiento', 'alimento'],
                        'description': 'El tipo de registro que se está realizando. Si es asados don abel es un restaurante, si es Go Karts es lugar de entretenimiento, si es baguette de jamón y queso es un alimento.'
                    },
                    'ubicacion': {
                        'type':'string',
                        'description': 'Lugar donde se encuentra el restaurante, lugar de entretenimiento. ex. "Condesa, CDMX", "Santa Maria La Ribera, CDMX", "Pachuca, Hidalgo", etc.'
                    }, 
                    'tipo_comida': {
                        'type': 'string',
                        'description': 'Si el tipo_registro es restaurante, entonces el tipo de comida puede ser: "italiana", "mexicana", "variada", etc. Si no es restaurante , solo se asigna: "None"'
                    }, 
                    'horario_alimento': {
                        'type': 'string',
                        'enum': ['desayuno', 'comida', 'cena'], 
                        'description': 'Si el tipo_registro es alimento, entonces se debe de especificar el horario de ese alimento, No es necesario un valor único de la lista. ex. huevos rancheros son desayuno, bisteces a la mexicana es comida, cereal puede ser desayuno y cena, etc. Si el tipo_registro no es "alimento" solo asigna un "None"'
                    },
                    'se_encontraron_todos_los_datos': {
                        'type': 'boolean',
                        'description': 'True si se encontraron correctamente el nombre y el tipo_registro, False si no.'
                    },
                    'razonamiento_se_encontraron_todos_los_datos': {
                        'type': 'string',
                        'description': 'La razón de por qué se eligió True o False en "se_encontraron_todos_los_datos".'
                    },
                },
            'required': ['nombre', 'tipo_registro', 'razonamiento_categoria', 'se_encontraron_todos_los_datos', 'razonamiento_se_encontraron_todos_los_datos']
        }
    },
]

cuenta_tools = [
    {
        'name': 'elegir_cuenta_financiera',
        'description': 'Función para dado un movimiento financiero, elegir la cuenta del usuario.',
        'input_schema': {
                'type': 'object',
                'properties': {
                    'cuenta': {
                        'type': 'string',
                        'description': 'El nombre de la cuenta'
                    },
                    'cuenta_id': {
                        'type': 'string',
                        'description': 'El id de la cuenta origen, dado por las opciones presentadas.'
                    },
                    'razonamiento': {
                        'type': 'string',
                        'description': 'La razón de por qué se eligieron las cuentas dadas.'
                    },
                    'se_encontraron_todos_los_datos': {
                        'type': 'boolean',
                        'description': 'True si se encontraron correctamente los datos de la cuenta en la lista proporcionada, False si no.'
                    },
                },
            'required': ['cuenta', 'cuenta_id', 'razonamiento', 'se_encontraron_todos_los_datos']
        }
    },
]

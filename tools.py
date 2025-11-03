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
    }
]

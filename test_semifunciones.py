# En este archivo pruebo pedazos de codigo para saber si funcioinan
def test_map_to_new_format():
    import json

    # JSON original
    original_json = [
        {
            "nombre_funcion": "consultar_proyectos",
            "descripcion": "cosulta los proyectos de la constructora dadas unas condiciones, siempre la debes usar cuando hablas de proyectos",
            "argumentos": {
                "id_ciudad": {
                    "tipo": "string",
                    "descripcion": "El id de la ciudad , e.g. 19, en caso de enviar un 'all' en este parametro se consultaran para todas las ciudades",
                    "es_obligatorio": True
                },
                "id_sector": {
                    "tipo": "string",
                    "descripcion": "El id del sector , e.g. 209, en caso de enviar un 'all' en este parametro se consultaran para todos los sectores",
                    "es_obligatorio": True
                },
                "id_tipo_vivienda": {
                    "tipo": "string",
                    "descripcion": "El id del tipo de vivienda , e.g. 1, en caso de enviar un 'all' en este parametro se consultaran para todos los tipos de vivienda",
                    "es_obligatorio": True
                }
            },
            "objeto_funcion": ""
        }
    ]

    # Función para mapear el JSON original al nuevo formato
    def mapear_a_nuevo_formato(json_original):
        nuevo_formato = []

        for funcion in json_original:
            nueva_funcion = {
                "tipo": "funcion",
                "funcion": {
                    "nombre": funcion["nombre_funcion"],
                    "descripcion": funcion["descripcion"],
                    "parametros": {
                        "tipo": "objeto",
                        "propiedades": {},
                        "requeridos": []
                    }
                }
            }

            for nombre_arg, detalles_arg in funcion["argumentos"].items():
                nueva_funcion["funcion"]["parametros"]["propiedades"][nombre_arg] = {
                    "tipo": detalles_arg["tipo"],
                    "descripcion": detalles_arg["descripcion"]
                }
                if detalles_arg["es_obligatorio"]:
                    nueva_funcion["funcion"]["parametros"]["requeridos"].append(nombre_arg)

            nuevo_formato.append(nueva_funcion)

        return nuevo_formato

    # Mapeo del JSON original al nuevo formato
    new_json = mapear_a_nuevo_formato(original_json)

    # Impresión del nuevo JSON en formato legible
    print(json.dumps(new_json, indent=4, ensure_ascii=False))



if __name__ == "__main__":
    test_map_to_new_format()
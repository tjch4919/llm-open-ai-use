import json
import os

from serpapi import GoogleSearch

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Charger les variables d'environnement à partir du fichier .env
_ = load_dotenv(find_dotenv())

# Récupérer les clés d'API depuis les variables d'environnement pour Serpapi
serpapi_api_key = os.getenv("SERPAPI_API_KEY")

# Créer une instance de l'API OpenAI
client = OpenAI()


def print_json(data):
    """Afficher les données en format JSON (si c'est un dict ou list) ou bien afficher la valeur directe"""
    if hasattr(data, 'model_dump_json'):
        data = json.loads(data.model_dump_json())

    if isinstance(data, list):
        for item in data:
            print_json(item)
    elif isinstance(data, dict):
        print(json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ))
    else:
        print(data)


def get_location_coordinate(poi_query):
    """Récupérer les coordonnées géographiques (gps) d'une adresse d'après la requête d'utilisateur
     à partir de l'API de Serpapi en utilisant Google maps"""
    params = {
        "q": poi_query,
        "engine": "google_maps",
        "type": "search",
        "api_key": serpapi_api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    if "local_results" in results.keys():
        return results["local_results"][0]["gps_coordinates"]
    if "place_results" in results.keys():
        return results["place_results"]["gps_coordinates"]
    return None


def search_nearby_pois(latitude, longitude, keyword, total_results=15, language="fr"):
    """Récupérer les points d'intérêt (magasins, restaurant...) à proximité d'une adresse (avec les coordonnées
     géographiques) à partir de l'API de Serpapi en utilisant Google maps"""
    params = {
        "q": keyword,
        "ll": f"@{latitude},{longitude},14z",
        "engine": "google_maps",
        "type": "search",
        "hl": language,
        "api_key": serpapi_api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    locations = results["local_results"][:total_results]
    interesting_fields = ["title", "gps_coordinates", "rating", "reviews", "type", "address", "open_state", "phone",
                          "operating_hours", "website", "description"]
    # extraire les champs intéressants
    return list(map(lambda item: {field: item.get(field) for field in interesting_fields}, locations))


def get_completion(input_messages, model="gpt-3.5-turbo"):
    gpt_response = client.chat.completions.create(
        model=model,
        messages=input_messages,
        temperature=0,  # température à 0 pour obtenir des réponses cohérentes
        seed=1024,  # seed pour obtenir des réponses cohérentes
        tool_choice="auto",  # valeur par défaut, c'est chatpgt qui décide s'il doit utiliser des outils(fonctions)
        # ou non
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_location_coordinate",
                    "description": "Récupérer les coordonnées géographiques (gps) d'une adresse d'après la requête "
                                   "d'utilisateur à partir de l'API de Serpapi en utilisant Google maps",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "poi_query": {
                                "type": "string",
                                "description": "La requête de l'utilisateur pour chercher les coordonnées gps d'un "
                                               "point d'intérêt, c'est souvent une adresse ou bien un nom de lieu",
                            }
                        },
                        "required": ["poi_query"],
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_nearby_pois",
                    "description": "Récupérer les points d'intérêt (magasins, restaurant...) à proximité d'une adresse "
                                   "(avec les coordonnées géographiques) à partir de l'API de Serpapi en utilisant "
                                   "Google maps",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "string",
                                "description": "latitude de l'adresse"
                            },
                            "longitude": {
                                "type": "string",
                                "description": "longitude de l'adresse"
                            },
                            "keyword": {
                                "type": "string",
                                "description": "Le mot-clé pour chercher les points d'intérêt à proximité de l'adresse"
                            },
                            "total_results": {
                                "type": "integer",
                                "description": "Le nombre total de résultats à retourner"
                            },
                            "language": {
                                "type": "string",
                                "description": "La langue des résultats"
                            }
                        },
                        "required": ["latitude", "longitude", "keyword"],
                    }
                }
            }]
    )
    return gpt_response.choices[0].message


instruction = """
Tu es un assistant pour aider les clients à trouver des points d'intérêt à proximité d'une adresse.
Ton travail est de reconnaître l'adresse demandé par l'utilisateur et de lui fournir une liste des
infos détaillées sur les points d'intérêt à proximité de cette adresse.
"""

output_format = """
Les infos détaillées comprennent : le nom du point d'intérêt, les coordonnées gps, la note, le nombre d'avis,
le type de point d'intérêt, l'adresse, l'état d'ouverture, les heures d'ouverture, le numéro de téléphone, le site web, 
et la description. 
Chaque point d'intérêt doit être indexé dans la liste, et lister les infos détaillées occupe ligne par ligne.
"""

examples = """
Utilisateur: J'aimerais trouver un café à proximité du gare lille Flandre. Peux-tu me donner une liste avec 2 cafés qui 
sont ouverts maintenant avec les infos détaillées ?

=>
Café 1:
Nom: Café de la Gare
Coordonnées gps: 50.6363,3.0703
Note: 4.5
Nombre d'avis: 150
Type: Café
Adresse: 1 Place des Buisses, 59800 Lille, France
État d'ouverture: Ouvert maintenant
Heures d'ouverture: 
    Lundi: fermé
    Mardi: 7h - 20h
    Mercredi: 7h - 20h
    Jeudi: 7h - 20h
    Vendredi: 7h - 20h
    Samedi: 7h - 20h
    Dimanche: 7h - 20h
Numéro de téléphone: +33 3 20 06 06 06
Site web: http://www.cafedelagare.fr/
Description: Un café sympa à proximité de la gare Lille Flandre.

Café 2:
Nom: Café du Coin
Coordonnées gps: 50.6365,3.0701
Note: 4.2
Nombre d'avis: 120
Type: Café
Adresse: 2 Place des Buisses, 59800 Lille, France
État d'ouverture: Ouvert maintenant
Heures d'ouverture: 
    Lundi: fermé
    Mardi: fermé
    Mercredi: 8h - 20h
    Jeudi: 8h - 20h
    Vendredi: 8h - 20h
    Samedi: 8h - 20h
    Dimanche: 8h - 20h
Numéro de téléphone: +33 3 20 06 06 07
Site web: http://www.cafeducoin.fr/
Description: Un café convivial à proximité de la gare Lille Flandre.
"""

user_request = ("J'aimerais trouver un restaurant à proximité de la tour Eiffel, Paris qui est ouvert maintenant,"
                " veuillez me donner une liste de 5 restaurants à proximité avec les infos détaillés.")

prompt = f"""
{output_format}

{examples}

Analyser étape par étape la requête de l'utilisateur suivant et vous pouvez appeler des fonctions pour obtenir les
résultats de recherche sur map:
{user_request}
"""

messages = [
    {"role": "system", "content": instruction},
    {"role": "user", "content": prompt}
]

response = get_completion(messages)
messages.append(response)  # Il faut ajouter la réponse de l'IA dans la liste des messages
print("=====Réponse de GPT=====")
print_json(response)

while response.tool_calls is not None:
    for tool_call in response.tool_calls:  # il peut passer plusieurs appels de fonctions
        args = json.loads(tool_call.function.arguments)
        print("Les arguments passés：")
        print_json(args)

        result = None
        if tool_call.function.name == "get_location_coordinate":
            print("Call: get_location_coordinate")
            result = get_location_coordinate(**args)
        elif tool_call.function.name == "search_nearby_pois":
            print("Call: search_nearby_pois")
            result = search_nearby_pois(**args)

        if result is not None:
            print("=====Ce qui est retourné par la fonction=====")
            print_json(result)

            messages.append({
                "tool_call_id": tool_call.id,  # ID pour identifier l'appel de fonction
                "role": "tool",
                "name": tool_call.function.name,
                "content": str(result)  # la valeur de result doit être convertie en chaîne
            })

    response = get_completion(messages)
    messages.append(response)  # La réponse de l'IA doit être ajoutée à la liste des messages

print("=====Réponse finale=====")
print(response.content)
print("=====L'histoire de conversation=====")
print_json(messages)

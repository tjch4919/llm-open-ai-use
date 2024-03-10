from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Charger les variables d'environnement à partir du fichier .env
_ = load_dotenv(find_dotenv())

# Créer une instance de l'API OpenAI
client = OpenAI()


def get_completion(system_message, user_message, model="gpt-3.5-turbo"):  # le modèle gpt-3.5-turbo est suffisant
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]  # créer un message avec le prompt
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content  # retourner le contenu de la première réponse


# Instructions de l'utilisateur,
# Un message avec le rôle 'system' est pratique pour donner l'objectif de la conversation
instruction = """
Tu es un assistant pour aider les clients à choisir un forfait de mobile chez nous.
Ton travail est de reconnaître les critères de choix des utilisateurs.
Chaque critère dispose de 4 champs : nom(name), prix mensuel(price), quantité de données
 mensuelles(data), forfait de 4G/5G (type) . 
En fonction de l'entrée de l'utilisateur, détermine les préférences de l'utilisateur pour les trois attributs ci-dessus.
"""


# Format de sortie avec beaucoup de contraintes
# Si on veut ajouter des contraintes sur le format de sortie, on peut ajouter des instructions comme ci-dessous
output_format = """
La sortie doit être en format JSON et avec les champs suivants :
 1. Le champ 'name' doit être de type string, et doit être l'une des valeurs suivantes : 'forfait économique',
 'forfait standard', 'forfait illimité', 'forfait 5G', 'forfait 5G illimité' ou null ;

 2. Le champ 'price' doit être de type objet ou null, et cet objet doit contenir deux champs :
 (1) operator, de type string, et peut prendre les valeurs suivantes : '<=' (inférieur ou égal),
 '>=' (supérieur ou égal), '==' (égal) ;
 (2) value, de type float ;

 3. Le champ 'data' doit être de type objet ou null, et cet objet doit contenir deux champs :
 (1) operator, de type string, et peut prendre les valeurs suivantes : '<=' (inférieur ou égal),
 '>=' (supérieur ou égal), '==' (égal) ;
 (2) value, de type int ou string, et la valeur de string ne peut qu'être 'no limit' ;
 
 4. Le champ 'type' doit être de type string, et peut prendre les valeurs suivantes : '5G', '4G', ou null ;

 5. Le champ 'sort' doit être de type objet ou null, et cet objet doit contenir deux champs :
 (1) ordering, de type string, et peut prendre les valeurs suivantes : 'descend' (descendant), 'ascend' (ascendant) ;
 (2) value, de type string, et peut prendre les valeurs suivantes : 'price', 'data' ou null.

 La sortie ne doit pas contenir de champs supplémentaires qui ne sont pas mentionnés ci-dessus.
 Ne faites pas de suppositions sur les valeurs des champs non mentionnés par l'utilisateur.
 Ne pas inclure de valeurs null dans la sortie.
"""

# Format de sortie sans précision
# output_format = """
# La sortie doit être en format JSON.
# """


# exemples sont très utiles pour aider le modèle à comprendre ce que l'on attend de lui
examples = """
Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: Quels sont les forfaits avec données de 100 Go?
=>
{"data":{"operator":">=","value":100}}


Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: Quels sont les forfaits avec données au minimum de 100 Go?
Assistant: On a un forfait 'standard' de 100 Go à 30 euros par mois.
utilisateur: C'est trop cher, avez-vous des forfaits inférieurs à 25 euros?
=>
{"data":{"operator":">=","value":100},"price":{"operator":"<=","value":25.0}}


Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: J'aimerais un forfait plus économique mais avec 50 Go de données mensuelles.
=>
{"data":{"operator":">=","value":50},"sort":{"ordering"="ascend","value"="price"}}


Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: J'aimerais un forfait avec des données illimitées.
=>
{"data":{"operator":"==","value":"no limit"}}


Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: J'aimerais un forfait 5G.
=>
{"name":"forfait 5G"}


Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur: J'aimerais profiter un forfait pour mon iPhone15 avec 5G.
=>
{"type":"5G"}
"""


# Entrée de l'utilisateur
input_text = """
J'aimerais un forfait avec une quantité de données mensuelles supérieure à 100 Go
"""

# input_text = "J'aimerais un forfait le moins cher possible"
# input_text = "Est-ce que vous avez des forfaits avec des données illimitées"


# Le contexte de la conversation est souvent utile pour le modèle
context = f"""
Assistant: Bonjour, qu'est-ce que je peux faire pour vous?
Utilisateur:  Bonjour, j'aimerais chercher un forfait chez vous, j'ai mon budget à 30 euros par mois.
Assistant: Nous avons des forfaits économiques et forfait standards, avez-vous une préférence?
Utilisateur：{input_text}
"""


# prompt
prompt = f"""
{output_format},

{examples},

{context}
"""

# appel de la fonction get_completion avec le prompt
chat_response = get_completion(instruction, prompt)
print(chat_response)

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

client = OpenAI()


instruction = """
VOus êtes un superviseur de service clientèle. Vous aller recevoir des conversations entre un client et un assistant   
d'agent concernant les forfaits de téléphonie mobile. Votre tâche consiste à juger de l'exactitude des informations sur 
produit introduites par le service clientèle.

Lors de la présentation des forfaits de données aux utilisateurs, le personnel du service clientèle doit mentionner
correctement le nom du produit, le prix mensuel, la quantité de données mensuelles, et si le forfait est de type 5G, il
faut également le mentionner, mais si c'est un forfait 4G (par défaut), on peut ignorer cette info.
Si une information est manquante ou si les informations ne correspondent pas à la réalité, cela signifie que les
informations ne sont pas exactes.

Les forfaits connus comprennent :

forfait économique : 10 euros par mois, 4G Internet avec quantité de données 40 Go par mois
forfait standard : 25 euros par mois, 4G Internet avec quantité de données 100 Go par mois
forfait illimité : 39.9 euros par mois, 4G Internet avec quantité de données illimitées
forfait 5G : 29.9 euros par mois, 5G Internet avec quantité de données 140 Go par mois
forfait 5G illimité : 49.9 euros par mois, 5G Internet avec quantité de données illimitées
"""


def get_completion(prompt_msg, model="gpt-3.5-turbo"):
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": prompt_msg}
    ]
    chatgpt_response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.8  # si on augmente la température, on obtient des réponses plus variées
    )
    return chatgpt_response.choices[0].message.content


# Format de sortie avec des contraintes
output_format = """
La sortie doit être en format JSON.
Si les informations sont exactes, la sortie doit être : {"accurate":true}
Si les informations ne sont pas exactes, la sortie doit être : {"accurate":false}
"""

example = """
Utilisateur: Quels sont les forfaits avec beaucoup de données Internet ?
Assistant: Nous avons le forfait standard, 100 Go par mois, le frais mensuel est de 25 euros.
=> {"accurate":true}

Utilisateur: Vous avez forfait 5G ?
Assistant: Oui, nous avons le forfait 5G, 29.9 euros par mois, 140 Go par mois. Et si vous avez besoin de plus de
données, nous avons aussi le forfait 5G illimité, 49.9 euros par mois, données illimitées. Ces deux forfaits sont
compatibles avec la 5G.
=> {"accurate":true}

Utilisateur: Je préfère un forfait pas cher, mais avec beaucoup de données.
Assistant: Nous avons le forfait économique, 10 euros par mois, 40 Go données par mois.
Je ne sais pas si cela vous convient.
=> {"accurate":true}

Utilisateur: Je veux un forfait 5G, mais mon budget est 30 euros par mois.
Assistant: Désolé, nous n'avons pas de forfait 5G à ce prix-là.
=> {"accurate":false}

Utilisateur: Je veux un forfait 5G, mais mon budget est 30 euros par mois.
Assistant: Nous avons le forfait 5G, 29.9 euros par mois, 140 Go par mois, il est presque dans votre budget et c'est 5G.
=> {"accurate":true}
"""

context = """
Utilisateur : Quels sont les forfaits avec beaucoup de données Internet ?
Assistant : Nous avons le forfait standard, 100 Go par mois, vous payeriez 25 euros par mois, et normalement cela 
satisfait les besoins de la plupart des utilisateurs.

Utilisateur : Mais j'ai besoin de faire une diffusion en direct en extérieur sur instagram, 100 Go me semble un peu
juste, il n'y a pas d'autres options ?
Assistant : Alors dans ce cas-là, nous recommandons le forfait illimité, 39.9 euros par mois, données illimitées.

Utilisateur : Très bien, et si c'est un forfait 5G ou pas ? J'espère que ma vitesse Internet est suffisamment rapide.
Assistant : Non, mais par contre on a un forfait 5G illimité, 49.9 euros par mois, pareil vous avec des données
illimitées, mais vous pouvez profiter Internet 5G.
"""

# analyser étape par étape, c'est une parole magique pour demander à l'IA de décomposer les étapes et générer plus des
# détails
prompt = f"""
{output_format}

Vous pouvez faire référence aux exemples suivants :
{example}

Veuillez analyser étape par étape :
{context}
"""

# on essaye 5 fois pour voir les réponses générées, et on peut voter pour la réponse finale d'après la majorité
for _ in range(5):
    print(f"------N°{_+1}------")
    # si on utilise le modèle 3.5-turbo, on peut obtenir des réponses incorrectes
    # donc on ne doit pas toujours faire confiance à l'IA
    response = get_completion(prompt)
    # mais si on utilise le modèle 4, on peut obtenir des réponses correctes, plus cher, mais plus fiable
    # response = get_completion(prompt, model="gpt-4-turbo-preview")
    print(response)

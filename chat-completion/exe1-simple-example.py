from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Charger les variables d'environnement à partir du fichier .env
_ = load_dotenv(find_dotenv())

# Créer une instance de l'API OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",  # gpt-3.5-turbo le nom du modèle
  messages=[
    # rôle du système, vous êtes un assistant poétique, compétent pour expliquer des concepts de programmation avec
    # une touche créative.
    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts "
                                  "with creative flair."},
    # rôle de l'utilisateur, composez un poème qui explique le concept de récursivité en programmation.
    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming"
                                # ", please use chinese as output language."
    },
  ],
  # temperature=0  # 0 pour des réponses avec une variabilité la plus faible possible, valeur possible 0~2
  # seed=1024  # seed pour la génération de texte, pour obtenir des réponses reproductibles
  # max_tokens=150  # nombre maximum de tokens dans la réponse
  # n=1  # nombre de réponses à générer pour chaque message
  # stop=["\n"]  # caractère de fin de la réponse
  # tools=[]  # une list d'objet qui représentent les outils à utiliser, un objet comprend deux champs dedans :
  #                                                    type (maintenant seulement 'function'),
  #                                                    function (une fonction à utiliser)
  # tool_choice="none"  # choix de l'outil, 'none' : on va pas utiliser d'outil, 'auto' : on va laisser OpenAI choisir,
  #          objet {"type": "function", "function": {"name": "my_function"}}: forcer l'utilisation d'un function calling
  # none est le choix par défaut quand aucune fonction n'est présente. auto est le choix par défaut si des fonctions
  # sont présentes.

  # pour plus de détails sur les paramètres, voir https://platform.openai.com/docs/api-reference/chat/create
)

print(completion.choices[0].message.content)

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
  # max_tokens=150  # nombre maximum de tokens dans la réponse
  # n=1  # nombre de réponses à générer pour chaque message
  # stop=["\n"]  # caractère de fin de la réponse
)

print(completion.choices[0].message.content)

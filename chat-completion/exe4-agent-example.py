import copy
import json
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# Charger les variables d'environnement à partir du fichier .env
_ = load_dotenv(find_dotenv())

# Créer une instance de l'API OpenAI
client = OpenAI()

# Instructions de l'utilisateur,
# Un message avec le rôle 'system' est pratique pour donner l'objectif de la conversation
instruction = """
Tu es un assistant pour aider les clients à choisir un forfait de mobile chez nous.
Ton travail est de reconnaître les critères de choix des utilisateurs.
Chaque critère dispose de trois champs : nom(name), prix mensuel(price), quantité de données
 mensuelles(data) . 
En fonction de l'entrée de l'utilisateur, détermine les préférences de l'utilisateur pour les trois attributs ci-dessus.
"""

# Format de sortie
# Si on veut ajouter des contraintes sur le format de sortie, on peut ajouter des instructions comme ci-dessous
output_format = """
La sortie doit être en format JSON et avec les champs suivants :
 1. Le champ 'name' doit être de type string, et doit être l'une des valeurs suivantes : 'forfait économique',
 'forfait standard', 'forfait illimité', 'forfait 5G', 'forfait 5G illimité', ou null ;

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
 /Attention!\\ Ne pas inclure de valeurs null dans la sortie, si un champ de type objet contient un champ dedans qui est 
 null, il faut considère c'est un champ null et le supprimer.
"""

examples = """
Le forfait le moins chèr：
{"sort":{"ordering"="ascend","value"="price"}}

Le forfait avec les données illimités：
{"data":{"operator":"==","value":"no limit"}}

Avec le plus de données：
{"sort":{"ordering"="descend","value"="data"}}

Quel est le forfait le moins chèr avec plus de 100G de données：
{"sort":{"ordering"="ascend","value"="price"},"data":{"operator":">=","value":100}}

Le forfait avec le prix mensuel inférieur à 25 euros：
{"price":{"operator":"<=","value":25.0}}

Je veux le forfait à 20 euros par mois：
{"price":{"operator":"==","value":20.0}}

Je veux un forfait avec les données illimités et 5G：
{"type":"5G", "data":{"operator":"==","value":"no limit"}}
"""


# Natural Language Understanding
class NLU:
    def __init__(self):
        self.prompt_template = f"{output_format}\n\n{examples}\n\nEntrée de l'utilisateur: ：\n__INPUT__"

    def _get_completion(self, user_message, model="gpt-3.5-turbo"):
        messages = [{"role": "user", "content": user_message}]  # créer un message avec le prompt
        nlu_response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        semantics = json.loads(nlu_response.choices[0].message.content)
        return {k: v for k, v in semantics.items() if v is not None}

    def parse(self, user_input):
        prompt = self.prompt_template.replace("__INPUT__", user_input)
        return self._get_completion(prompt)


# Dialogue State Tracker
class DST:
    def __init__(self):
        pass

    def update(self, state, nlu_semantics):
        """Pour chaque entrée de l'utilisateur, mettre à jour l'état du dialogue pour que le vrai besoin est bien
        présenté."""
        if "name" in nlu_semantics:
            # si l'utilisateur a mentionné le nom du forfait qu'il veut, simplement enlever tous les autres critères
            # comme c'est suffisant pour identifier un forfait
            state.clear()
        if "sort" in nlu_semantics:
            # si l'utilisateur a mentionné un critère de tri, et que ce critère est déjà présent dans l'état avec
            # l'opérateur égal, if faut ignorer ce critère (on va montrer tous les forfaits triés par ce critère)
            slot = nlu_semantics["sort"]["value"]
            if slot in state and state[slot]["operator"] == "==":
                del state[slot]
        for k, v in nlu_semantics.items():
            state[k] = v
        return state


# Action generation (Dialog Policy)
class MockedDB:
    def __init__(self):
        self.data = [
            {"name": "forfait économique", "price": 10.0, "data": 40, "type": "4G"},
            {"name": "forfait standard", "price": 25.0, "data": 100, "type": "4G"},
            {"name": "forfait illimité", "price": 39.9, "data": 10000, "type": "4G"},
            {"name": "forfait 5G", "price": 29.9, "data": 140, "type": "5G"},
            {"name": "forfait 5G illimité", "price": 49.9, "data": 10000, "type": "5G"}
        ]

    def retrieve(self, **kwargs):
        records = []
        for r in self.data:
            select = True
            for k, v in kwargs.items():
                if k == "sort":  # pour le critère de tri, on ne le compare pas, on le garde tout simplement
                    continue
                if k == "data" and v["value"] == "no limit":  # pour le cas de données illimitées
                    if r[k] != 10000:
                        select = False
                        break
                    else:
                        continue
                if "operator" in v:  # pour les critères de prix et de données, on compare avec l'opérateur
                    if not eval(str(r[k]) + v["operator"] + str(v["value"])):
                        select = False
                        break
                elif str(r[k]) != str(v):  # pour le cas de type et name, on compare simplement les valeurs
                    select = False
                    break
            if select:
                records.append(r)
        if len(records) <= 1:
            return records

        # trier les enregistrements selon le critère de tri
        key = "price"
        reverse = False
        if "sort" in kwargs:
            key = kwargs["sort"]["value"]
            reverse = kwargs["sort"]["ordering"] == "descend"
        return sorted(records, key=lambda x: x[key], reverse=reverse)


prompt_templates = {
    "recommend": "Utilisateur：__INPUT__ \n\nPrésenter les forfaits suivant à "
                 "l'utilisateur：__NAME__，prix:__PRICE__ euros，quantité de données mensuelles: __DATA__ Go，"
                 "type: __TYPE__",
    "not_found": "Utilisateur：__INPUT__ \n\nOn n'a pas trouvé le forfait qui satisfait les besoins d'utilisateur comme:"
                 "name: __NAME__，prix: __PRICE__ euro, quantité de données mensuelles:__DATA__Go， type:__TYPE__，"
                 "Il faut demander à l'utilisateur s'il veut changer ses critères de choix."
}

# Définir les besoins de parole. "NO COMMENTS. NO ACKNOWLEDGEMENTS." est un prompt courant, qui signifie
# "si vous avez quelque chose à dire, dites-le, sinon, n'affirmées rien."
ext = ("Exprimer la résultat de façon naturel, simple et direct. Donner directement la réponse. "
       " Et si on ne trouve pas de forfait, il faut pas imaginer une réponse. NO COMMENTS. NO ACKNOWLEDGEMENTS.")
# on ajoute l'extension à chaque prompt
prompt_templates = {k: v + ext for k, v in prompt_templates.items()}


# NLG(Natural Language Generation) + ChatGPT
class DialogManager:
    def __init__(self, nlg_prompt_templates):
        self.state = {}
        self.session = [
            {
                "role": "system",
                "content": instruction
            }
        ]
        self.nlu = NLU()
        self.dst = DST()
        self.db = MockedDB()
        self.prompt_templates = nlg_prompt_templates

    def _wrap(self, user_input, records):
        """D'après l'état actuel et les résultats de la recherche dans la base de données, assembler le prompt"""
        if records:
            prompt = self.prompt_templates["recommend"].replace("__INPUT__", user_input)
            # on ne prend que le premier enregistrement pour générer le prompt (pratique pour les cas le plus/le moins)
            r = records[0]
            for k, v in r.items():
                prompt = prompt.replace(f"__{k.upper()}__", str(v))
        else:
            prompt = self.prompt_templates["not_found"].replace("__INPUT__", user_input)
            for k, v in self.state.items():
                if "operator" in v:
                    prompt = prompt.replace(
                        f"__{k.upper()}__", v["operator"] + str(v["value"]))
                else:
                    prompt = prompt.replace(f"__{k.upper()}__", str(v))
        return prompt

    def _call_chatgpt(self, prompt, model="gpt-3.5-turbo"):
        """Appeler chatgpt pour obtenir une réponse plus naturelle"""
        session = copy.deepcopy(self.session)
        session.append({"role": "user", "content": prompt})
        nlg_response = client.chat.completions.create(
            model=model,
            messages=session,
            temperature=0,
        )
        return nlg_response.choices[0].message.content

    def clear_state(self):
        self.state.clear()

    def run(self, user_input):
        """C'est la fonction principale pour exécuter le système de dialogue. Elle prend l'entrée de l'utilisateur,
         mettre à jour l'état du dialogue, rechercher dans la base de données, appeler chatgpt pour obtenir une réponse
          plus naturelle, et retourner la réponse."""

        # Appeler NLU pour obtenir l'analyse sémantique
        semantics = self.nlu.parse(user_input)
        print("===semantics===")
        print(semantics)

        # Appeler DST pour mettre à jour l'état du dialogue
        self.state = self.dst.update(self.state, semantics)
        print("===state===")
        print(self.state)

        # D'après l'état de dialogue actuel, rechercher dans la base de données pour obtenir les enregistrements
        records = self.db.retrieve(**self.state)

        # Assembler le prompt pour appeler chatgpt
        prompt_for_chatgpt = self._wrap(user_input, records)
        print("===nlg-prompt===")
        print(prompt_for_chatgpt)

        # Appeler chatgpt pour obtenir une réponse plus naturelle
        dialog_response = self._call_chatgpt(prompt_for_chatgpt)

        # Intégrer l'entrée de l'utilisateur et la réponse du système dans la session de chatgpt
        self.session.append({"role": "user", "content": user_input})
        self.session.append({"role": "assistant", "content": dialog_response})
        return dialog_response


# Exemple d'utilisation
dm = DialogManager(prompt_templates)

print("====question 1===")
response = dm.run("Le forfait le moins chèr")
print("====response 1===")
print(response)

print("====question 2===")
dm.clear_state()
response = dm.run("J'aimerais profiter un forfait de 5G et avec 100Go de données au minimum")
print("====response 2===")
print(response)

print("====question 3===")
# si on n'efface pas l'état, le critère de dernière question est gardé, et il est utilisé pour cette question aussi
# dm.clear_state()
response = dm.run("Vous avez un forfait avec les données illimités?")
print("====response 3===")
print(response)

print("====question 4===")
dm.clear_state()
response = dm.run("J'ai un budget de 25 euros par mois, je veux un forfait avec le plus de données possibles")
print("====response 4===")
print(response)

print("====question 5===")
dm.clear_state()
response = dm.run("Vous avez un forfait de 5G avec le prix mensuel inférieur à 25 euros?")
print("====response 5===")
print(response)

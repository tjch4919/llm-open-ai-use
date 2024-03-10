# Pour tester les exercises, faire les préparations suivantes

## Assurer les dépendances `openai`, `google-search-results`, et `dotenv` sont bien installées, sinon exécutez les commandes suivantes :

`pip install --upgrade openai`

`pip install --upgrade dotenv`

`pip install --upgrade google-search-results`

## Il faut que vous ayez un compte sur OpenAI et que vous ayez créé une API key

### Après avoir créé votre compte, vous pouvez créer une API key si vous n'en avez pas déjà une via ce [lien](https://platform.openai.com/account/api-keys)

### Copiez cette clé et collez-la dans un fichier `.env` à la racine de votre projet et nommez la variable `OPENAI_API_KEY` comme ceci

`OPENAI_API_KEY=YOUR_API_KEY`


## Il faut que vous ayez un compte sur SerpApi et que vous avez une clé d'API

### Après avoir créé votre compte, vous pouvez trouver API key dans cette [page](https://serpapi.com/manage-api-key)
### Et puis comme pour OpenAI, copiez cette clé et collez-la dans un fichier `.env` à la racine de votre projet et nommez la variable `SERPAPI_API_KEY` comme ceci

`SERPAPI_API_KEY=YOUR_API_KEY`
# Exemples d'apprentissage en français

Tous les cas ci-dessous sont fictifs et destinés à l'apprentissage. Une révision n'utilise que les informations présentes dans l'extrait.

## 1. Réviser un texte financier

Entrée : « Le chiffre d'affaires du trimestre atteint 1,2 million d'euros, en hausse de 8 % sur un an. La marge brute passe de 20 % à 23 %. La direction estime que la demande pourrait se redresser, sans fournir de données de commandes. »

Version acceptable : « Le chiffre d'affaires du trimestre atteint 1,2 million d'euros, en hausse de 8 % sur un an. La marge brute progresse de 20 % à 23 %, soit 3 points de pourcentage. La direction estime que la demande pourrait se redresser, sans fournir de données de commandes. »

Version inacceptable : « Portée par un net rebond des commandes, la demande devrait se redresser franchement, et la marge brute bondit de 3 %. »

Raison : l'extrait ne contient aucune donnée de commandes ; « pourrait » devient une certitude et les 3 points de pourcentage se transforment en 3 %. La version acceptable garde les chiffres, l'attribution et le doute.

Note régionale : en France, on écrit `1 234,5` et `8 %` avec des espaces insécables. Au Québec, l'espace devant `%` reste, mais pas devant `;`, `!` ou `?`. La version publiée doit suivre la variété du document, pas une règle unique.

## 2. Réviser un commentaire de code

Entrée :

```python
def should_retry(status):
    # Vérifie l'état pour décider s'il faut réessayer
    return status == 429
```

Commentaire seul, code inchangé : `# Renvoie True quand le statut vaut 429, ce qui indique qu'une nouvelle tentative peut être utile.`

Inacceptable : `# Réessaie automatiquement jusqu'à obtenir une réponse valide.`

Raison : la fonction se contente de comparer une valeur ; elle ne lance aucune tentative et ne fixe ni délai ni nombre d'essais. Le code reste identique.

## 3. Condenser un prompt

Entrée : « Tu es un expert de renommée mondiale en synthèse. Mobilise toute ton expertise pour résumer {{text}} en trois points, avec 50 mots maximum par point. Si le matériel est insuffisant, pose une seule question et attends la réponse avant de rédiger. »

Version acceptable : « Résume {{text}} en trois points de 50 mots maximum chacun. Si le matériel manque, pose une seule question et attends la réponse avant de rédiger. »

Version inacceptable : « Fais une synthèse détaillée et pertinente de {{text}}, en t'appuyant sur tes connaissances. »

Raison : la version acceptable conserve la variable, le nombre de points, la limite de mots et la condition d'attente. L'autre supprime le format et la limite, et élargit la source aux connaissances du modèle.

## 4. Transférer un style vers un nouveau prompt

Échantillon : « D'abord, vérifier que le service répond. Ensuite, chercher l'appel le plus lent. Tant qu'on n'a pas mesuré, on ne conclut pas. »

Traits transférables : phrases brèves, ordre explicite, verbes d'action, incertitude conservée.

Nouvelle tâche : écrire un prompt pour examiner {{log}}.

Version acceptable : « D'abord, repérer les erreurs dans {{log}}. Ensuite, les classer par ordre d'apparition. Ne retenir que ce que le journal contient. Si une cause n'est pas démontrée, l'indiquer comme telle. »

Version inacceptable : « J'ai analysé des milliers de journaux dans ma carrière : je trouverai toujours la cause exacte d'une panne. »

Raison : la seconde version invente une expérience et une garantie absentes de l'échantillon. La première reprend le rythme et la prudence sans ajouter de faits.

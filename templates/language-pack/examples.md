# Exemples pédagogiques en français

Modèle de contribution non publié. Tous les scénarios sont fictifs ; chaque révision utilise uniquement les informations fournies.

## 1. Réviser un paragraphe financier

Entrée : Le chiffre d'affaires de la période est de 12 millions d'euros, soit 8 % de plus qu'à la même période l'an dernier. La marge brute passe de 20 % à 23 %. L'entreprise pense que la demande pourrait se redresser, mais ne fournit pas de données sur les commandes.

Acceptable : Le chiffre d'affaires de la période atteint 12 millions d'euros, en hausse de 8 % sur un an. La marge brute passe de 20 % à 23 %, soit une hausse de 3 points de pourcentage. L'entreprise estime que la demande pourrait se redresser, sans fournir de données sur les commandes.

Inacceptable : La forte hausse des commandes confirme la reprise durable de la demande.

Raison : Cette version invente des données et transforme une possibilité en certitude.

## 2. Réviser un commentaire de code

Entrée :

```python
def should_retry(status):
    # Ici, on vérifie intelligemment si cet état nécessite une nouvelle tentative.
    return status == 429
```

Modifier uniquement le commentaire : `# Renvoie True pour le statut 429 afin d'indiquer qu'une nouvelle tentative est nécessaire.`

Inacceptable : `# Réessaie automatiquement toutes les erreurs serveur jusqu'au succès.`

Raison : Le code vérifie une valeur ; il n'effectue aucune nouvelle tentative et n'en fixe pas le nombre. La fonction et le code restent inchangés.

## 3. Alléger un prompt

Entrée : Tu es le meilleur expert mondial du résumé. Utilise tes capacités exceptionnelles pour résumer uniquement {{text}} en trois points de 20 mots maximum chacun. Si le contenu est insuffisant, pose une question et attends la réponse avant de résumer.

Acceptable : Résume uniquement {{text}} en trois points de 20 mots maximum chacun. Si le contenu est insuffisant, pose une question de clarification et attends la réponse avant de résumer.

Inacceptable : Utilise tes connaissances pour expliquer le sujet en détail.

Raison : Cette version perd la variable, la restriction des sources, le nombre de points, la longueur et la condition d'attente.

## 4. Transférer le style d'un extrait

Extrait : Vérifie d'abord que cela fonctionne. Ensuite, cherche ce qui ralentit. Si tu n'as pas testé un point, ne conclus pas encore.

Choix transférables : phrases courtes, ordre explicite, actions directes, incertitude conservée.

Nouvelle tâche : rédiger un prompt pour examiner des journaux fournis.

Acceptable : Repère les erreurs dans {{log}}. Classe-les dans leur ordre d'apparition. Utilise seulement le journal. Signale ce que tu ne peux pas déterminer.

Inacceptable : J'ai réparé des centaines de serveurs, tu peux donc croire mon diagnostic.

Raison : Cette version invente une expérience et une identité au lieu de transférer la structure de l'extrait.

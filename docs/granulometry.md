# Granulométrie et Dépôt

Génération de dépôts granulaires réalistes.

## Paramètres
- Nombre de particules
- Rayon min/max
- Seed (reproductibilité)
- Type de conteneur : Box2D, Disk2D
- Avatar modèle (sélectionné parmi les avatars manuels)
- Couleur des particules
- Option : créer murs autour (Box2D)
- Option : stocker dans groupe nommé

## Fonctionnement
1. Utilise `granulo_Random` pour les rayons
2. Utilise `depositInBox2D` ou `depositInDisk2D`
3. Recrée fidèlement l’avatar modèle avec taille variable

> À compléter : capture avant/après génération
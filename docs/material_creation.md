# Création d'un Matériau

Cette section explique comment créer et configurer un matériau dans LMGC90_GUI.

## Interface
- Onglet **Matériau** vous sert à créer votre matériau,
- Champs principaux :
  - **Nom** : Nom unique du matériau (ex: `TDURx`, `steel`)
  - **Type** : Liste déroulante avec les types supportés
  - **Densité** : Valeur en kg/m³
  - **Propriétés** : Champ texte pour paramètres avancés

## Types de matériaux disponibles
Vous pourriez créer différents types de matériaux, ceux qui sont inclus sont :
- **RIGID** : Corps rigide (densité obligatoire)
- **ELAS** : Élastique linéaire isotrope
- **ELAS_DILA** : Élastique avec dilatation thermique
- **VISCO_ELAS** : Viscoélastique
- **ELAS_PLAS** : Élastoplastique
- **THERMO_ELAS** : Thermoélastique
- **PORO_ELAS** : Poroélastique

## Exemple de création
1. Sélectionnez le type (ex: ELAS), 
2. LMGC90_GUI vous chargera automatiquement les paramètres de ce matériau, il vous suffira seulement de modifier les valeurs dans le champs propriétés  :
   - elas='standard', young=0.1e+15, nu=0.2, anisotropy='isotropic'
3. Cliquez ensuite sur bouton **Créer**

## Astuces
- Le champ Propriétés accepte la syntaxe Python-like
- Utilisez les variables dynamiques si définies (menu Outils)

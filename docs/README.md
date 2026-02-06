# Concorde Vision Solver

Interface graphique pour le solveur TSP Concorde - Solution optimale garantie.

## Installation

### Prerequis
- Python 3.8+
- WSL2 avec Ubuntu-Concorde installe

### Installation des dependances
`ash
pip install -r requirements.txt
`

## Utilisation

`ash
py -3 Concorde_Vision_Solver.py
`

### Workflow
1. Selectionner un fichier Excel/CSV avec coordonnees GPS
2. Verifier les colonnes (ID, Latitude, Longitude)
3. Cliquer sur "LANCER OPTIMISATION"
4. Attendre la solution optimale
5. Visualiser les resultats (Excel, Carte)

## Structure du projet

`
Concorde_Graphique/
- Concorde_Vision_Solver.py  # Application principale
- requirements.txt           # Dependances Python
- python_scripts/
  - tsp_converter.py        # Conversion Excel <-> TSP
  - visualize_tour.py       # Visualisation carte
- data/
  - input/                  # Fichiers TSP
  - output/                 # Solutions .sol
- Excel/
  - Imported/              # Excel importes
  - results/               # Excel resultats
- Map_view/                 # Cartes HTML
- icon/                     # Icone application
`

## Precision

Ce projet utilise la **projection Euclidienne** pour convertir les coordonnees GPS en metres:
- Precision millimetrique
- Reference au centroide des donnees
- Format EUC_2D pour Concorde

## Developpeur

(c) 2026 iM@Des - Tous droits reserves

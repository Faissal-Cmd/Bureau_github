import itertools
import sys
import gurobipy as gp
from gurobipy import GRB

def lire_fichier_entree(fichier_entree):
    """
    Lire le fichier d'entrée et organiser les photos en horizontales ou verticales.
    """
    with open(fichier_entree, "r") as fichier:
        lignes = fichier.read().strip().split("\n")

    N = int(lignes[0])  # Nombre de photos
    photos_horizontales = []
    photos_verticales = []

    for i in range(1, N + 1):
        donnees = lignes[i].split()
        orientation = donnees[0]
        etiquettes = set(donnees[2:])

        if orientation == "H":
            photos_horizontales.append({"id": i - 1, "etiquettes": etiquettes})
        elif orientation == "V":
            photos_verticales.append({"id": i - 1, "etiquettes": etiquettes})

    return photos_horizontales, photos_verticales

def combiner_photos_verticales(photos_verticales):
    """
    Combiner les photos verticales en paires optimales pour former des diapositives.
    """
    diapositives = []
    while len(photos_verticales) > 1:
        photo1 = photos_verticales.pop(0)
        photo2 = photos_verticales.pop(-1)
        etiquettes_combinees = photo1["etiquettes"].union(photo2["etiquettes"])
        diapositives.append({
            "ids": [photo1["id"], photo2["id"]],
            "etiquettes": etiquettes_combinees
        })
    return diapositives

def calculer_facteur_interet(etiquettes1, etiquettes2):
    """
    Calculer le facteur d'intérêt entre deux ensembles d'étiquettes.
    """
    etiquettes_communes = len(etiquettes1.intersection(etiquettes2))
    etiquettes_uniques_1 = len(etiquettes1 - etiquettes2)
    etiquettes_uniques_2 = len(etiquettes2 - etiquettes1)
    return min(etiquettes_communes, etiquettes_uniques_1, etiquettes_uniques_2)

def optimiser_diaporama(diapositives):
    """
    Optimisation du diaporama avec Gurobi.
    """
    modele = gp.Model("Diaporama")
    n_diapositives = len(diapositives)

    Z = modele.addVars(n_diapositives, n_diapositives, vtype=GRB.BINARY, name="Z")

    # Contrainte: Chaque diapositive est utilisée exactement une fois
    for i in range(n_diapositives):
        modele.addConstr(gp.quicksum(Z[i, j] for j in range(n_diapositives) if i != j) == 1)
        modele.addConstr(gp.quicksum(Z[j, i] for j in range(n_diapositives) if i != j) == 1)

    # Fonction objectif: maximiser l'intérêt total
    modele.setObjective(
        gp.quicksum(
            calculer_facteur_interet(diapositives[i]["etiquettes"], diapositives[j]["etiquettes"]) * Z[i, j]
            for i in range(n_diapositives) for j in range(n_diapositives) if i != j
        ),
        GRB.MAXIMIZE
    )

    modele.optimize()
    ordre = []
    if modele.Status == GRB.OPTIMAL:
        for i in range(n_diapositives):
            for j in range(n_diapositives):
                if i != j and Z[i, j].x > 0.5:
                    ordre.append((i, j))
    return ordre

def ecrire_fichier_sortie(fichier_sortie, ordre, diapositives):
    """
    Écrire le fichier de sortie au format attendu.
    """
    with open(fichier_sortie, "w") as fichier:
        fichier.write(f"{len(diapositives)}\n")
        diapositives_utilisees = set()
        for i, j in ordre:
            id_diapositive = tuple(diapositives[i]["ids"])  # Convertir en tuple pour vérification d'unicité
            if id_diapositive not in diapositives_utilisees:
                fichier.write(" ".join(map(str, id_diapositive)) + "\n")
                diapositives_utilisees.add(id_diapositive)

def principal():
    fichier_entree = "data/Projet/PetPics-20.txt"
    fichier_sortie = "data/Projet/Resultat.txt"

    photos_horizontales, photos_verticales = lire_fichier_entree(fichier_entree)
    diapositives = []
    diapositives.extend([{ "ids": [photo["id"]], "etiquettes": photo["etiquettes"] } for photo in photos_horizontales])
    diapositives.extend(combiner_photos_verticales(photos_verticales))

    ordre = optimiser_diaporama(diapositives)
    ecrire_fichier_sortie(fichier_sortie, ordre, diapositives)
    print(f"Diaporama généré dans le fichier : {fichier_sortie}")

if __name__ == "__main__":
    principal()

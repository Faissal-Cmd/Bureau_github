import itertools
import sys
import gurobipy as gp
from gurobipy import GRB

def read_input_file(input_file):
    """
    Lire le fichier d'entrée et organiser les photos en horizontales ou verticales.
    """
    with open(input_file, "r") as file:
        lines = file.read().strip().split("\n")

    N = int(lines[0])  # Nombre de photos
    photos_horizontal = []
    photos_vertical = []

    for i in range(1, N + 1):
        data = lines[i].split()
        orientation = data[0]
        tags = set(data[2:])

        if orientation == "H":
            photos_horizontal.append({"id": i - 1, "tags": tags})
        elif orientation == "V":
            photos_vertical.append({"id": i - 1, "tags": tags})

    return photos_horizontal, photos_vertical

def combine_vertical_photos(photos_vertical):
    """
    Combiner les photos verticales en paires optimales pour former des diapositives.
    """
    slides = []
    while len(photos_vertical) > 1:
        photo1 = photos_vertical.pop(0)
        photo2 = photos_vertical.pop(-1)
        combined_tags = photo1["tags"].union(photo2["tags"])
        slides.append({
            "ids": [photo1["id"], photo2["id"]],
            "tags": combined_tags
        })
    return slides

def compute_interest_factor(tags1, tags2):
    """
    Calculer le facteur d'intérêt entre deux ensembles de tags.
    """
    common_tags = len(tags1.intersection(tags2))
    tags_in_1_not_2 = len(tags1 - tags2)
    tags_in_2_not_1 = len(tags2 - tags1)
    return min(common_tags, tags_in_1_not_2, tags_in_2_not_1)

def optimize_slideshow(slides):
    """
    Optimisation du diaporama avec Gurobi.
    """
    model = gp.Model("Slideshow")
    n_slides = len(slides)

    Z = model.addVars(n_slides, n_slides, vtype=GRB.BINARY, name="Z")

    # Contrainte: Chaque diapositive est utilisée exactement une fois
    for i in range(n_slides):
        model.addConstr(gp.quicksum(Z[i, j] for j in range(n_slides) if i != j) == 1)
        model.addConstr(gp.quicksum(Z[j, i] for j in range(n_slides) if i != j) == 1)

    # Fonction objectif: maximiser l'intérêt total
    model.setObjective(
        gp.quicksum(
            compute_interest_factor(slides[i]["tags"], slides[j]["tags"]) * Z[i, j]
            for i in range(n_slides) for j in range(n_slides) if i != j
        ),
        GRB.MAXIMIZE
    )

    model.optimize()
    order = []
    if model.Status == GRB.OPTIMAL:
        for i in range(n_slides):
            for j in range(n_slides):
                if i != j and Z[i, j].x > 0.5:
                    order.append((i, j))
    return order

def write_output_file(output_file, order, slides):
    """
    Écrire le fichier de sortie au format attendu.
    """
    with open(output_file, "w") as file:
        file.write(f"{len(slides)}\n")
        used_slides = set()
        for i, j in order:
            slide_id = tuple(slides[i]["ids"])  # Convertir en tuple pour vérification d'unicité
            if slide_id not in used_slides:
                file.write(" ".join(map(str, slide_id)) + "\n")
                used_slides.add(slide_id)


def main():
    input_file = "data/Projet/PetPics-20.txt"
    output_file = "data/Projet/Resultat.txt"

    photos_horizontal, photos_vertical = read_input_file(input_file)
    slides = []
    slides.extend([{ "ids": [photo["id"]], "tags": photo["tags"] } for photo in photos_horizontal])
    slides.extend(combine_vertical_photos(photos_vertical))

    order = optimize_slideshow(slides)
    write_output_file(output_file, order, slides)
    print(f"Diaporama généré dans le fichier : {output_file}")

if __name__ == "__main__":
    main()

# Tous les nœuds de l'agent

class Node:
    def __init__(self, name):
        self.name = name

    def execute(self):
        print(f"Exécution du nœud {self.name}")
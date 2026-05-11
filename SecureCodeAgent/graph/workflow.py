# Construction du graphe

from .nodes import Node

class Workflow:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def run(self):
        for node in self.nodes:
            node.execute()
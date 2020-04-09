import networkx as nx
import numpy as np
import math
from circuit_analyzer import circuit_amperages
from circuit_check import solution_check
import matplotlib.pyplot as plt

def graph_show(G, T, S, U):
    plt.figure(figsize=(15,15))
    solved = circuit_amperages(G, S, T, U)
    solution_check(G, T, S, solved, U, epsilon=U/100000)
    for (u, v) in list(G.edges()).copy():
        if solved[(u,v)] < 0:
            solved[(v,u)] = -solved[(u,v)]
            w = G.get_edge_data(u,v)['R']
            G.remove_edge(u,v)
            G.add_edge(v,u, R = w)
            del(solved[(u,v)])


    min_R = min([w for (_,_,w) in G.edges(data='R')])
    max_R = max([w for (_,_,w) in G.edges(data='R')])


    G_labels = {i: i for i in G.nodes()}
    G_labels[S] = "V"
    G_labels[T] = "G"

    roots = [T, S]
    other_nodes = list(G.nodes())
    other_nodes.remove(T)
    other_nodes.remove(S)

    pos = nx.shell_layout(
        G,
        nlist = [other_nodes, roots],
    )

    min_I = min(solved.values())
    max_I = max(solved.values())

    layout_weights = dict()

    for key in solved.keys():
        layout_weights[key] = -math.log((solved[key] - min_I + 0.01)/(max_I - min_I + 0.2))

    nx.set_edge_attributes(G, layout_weights, 'LW')

    pos[T] = min(pos.values(), key = lambda p: p[0])
    pos[S] = max(pos.values(), key = lambda p: p[0])

    pos = nx.spring_layout(
        G.to_undirected(),
        pos = pos,
        k = 8 / np.sqrt(G.number_of_nodes()),
        fixed = [T, S],
        iterations = 200,
        weight='LW'
    )

    min_x = min(pos.values(), key = lambda p: p[0])[0]
    max_x = max(pos.values(), key = lambda p: p[0])[0]

    offset = (max_x - min_x) / 3 

    pos[T][0] = min_x - offset
    pos[S][0] = max_x + offset

    pos[T][1] = 0
    pos[S][1] = 0

    nx.draw_networkx(
        G,
        pos = pos,
        width = [(2 / (max_R - min_R)) * (max_R - G.get_edge_data(u, v)['R']) + 1 for u, v in G.edges()],
        edge_cmap = plt.cm.inferno, 
        edge_color = [solved[e] for e in G.edges()], 
        edge_vmin=min(solved.values()), 
        edge_vmax=max(solved.values()),
        nlist = [other_nodes, roots],
        with_labels = True,
        labels = G_labels
    )

    plt.show()

import networkx as nx
import numpy as np

def mesh2d_graph(n, m, low_R = 100, high_R = 1000):
    G = nx.grid_graph([n,m]).to_directed()
    G = nx.relabel_nodes(G, {(i, j): i * 10 + j for (i, j) in G.nodes()})

    for (u, v) in list(G.edges()):
        if G.has_edge(u, v) and G.has_edge(v, u):
            G.remove_edge(u, v)

    nx.set_edge_attributes(G, {e: np.random.randint(low_R, high_R) for e in G.edges()}, 'R')
    return G

def regular_graph(d, n, low_R = 100, high_R = 1000):
    G = nx.generators.random_regular_graph(d, n)
    R_dict = {e: np.random.randint(low_R, high_R) for e in G.edges()}
    nx.set_edge_attributes(G, R_dict, name='R')
    return G

def graph_with_bridges(n, components = 2, low_R = 100, high_R = 1000):
    G = nx.DiGraph()

    pivots = [int(i * n / components) for i in range(components + 1)]

    for p in range(1, len(pivots)):
        for i in range(pivots[p-1], pivots[p]):
            for j in range(pivots[p-1], pivots[p]):
                if i != j and not G.has_edge(j, i) and np.random.randint(0, 5) == 0:
                    G.add_edge(i, j, R = np.random.randint(low_R, high_R))

    for p in range(2, len(pivots)):
        u = np.random.randint(pivots[p-2], pivots[p-1]-1)
        v = np.random.randint(pivots[p-1], pivots[p]-1)
        R = np.random.randint(low_R, high_R)
        G.add_edge(u, v, R=R)

    return G


def connected_graph(n, low_R = 100, high_R = 1000):
    G = graph_with_bridges(n, 1, low_R, high_R)
    CC = list(nx.algorithms.connected_components(G.to_undirected()))
    for c in range(1, len(CC)):
        u_i = np.random.randint(0, len(CC[c-1])-1)
        v_i = np.random.randint(0, len(CC[c])-1)
        R = np.random.randint(low_R, high_R)
        G.add_edge(CC[u_i], CC[v_i], R=R)
    return G


def graph_to_file(G, filename, S = None, T = None, U = None):
    with open(filename, "w") as file:
        file.flush()
        if S is not None and T is not None and U is not None:
            file.write(f"STU {S} {T} {U}\n")
        for (u, v, R) in G.edges.data("R"):
            file.write(f"{u} {v} {R}\n")
        file.close()


# Generating 3-regular graphs
graph_to_file(regular_graph(3, 20), "reg3_20", 0, 19, 230)
graph_to_file(regular_graph(3, 50), "reg3_50", 0, 49, 230)
graph_to_file(regular_graph(3, 90), "reg3_90", 0, 89, 230)

graph_to_file(graph_with_bridges(60, 3), "bridges3_60", 0, 59, 230)
graph_to_file(graph_with_bridges(60, 2), "bridges2_60", 0, 59, 230)

graph_to_file(connected_graph(20), "connected_20", 0, 19, 230)
graph_to_file(connected_graph(60), "connected_60", 0, 59, 230)
graph_to_file(connected_graph(100), "connected_100", 0, 99, 230)

graph_to_file(mesh2d_graph(5,5), "mesh5_5", 0, 24, 230)
graph_to_file(mesh2d_graph(10, 10), "mesh10_10", 0, 99, 230)
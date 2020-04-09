import networkx as nx
import numpy as np 
import scipy as sp
from networkx.algorithms.components import connected_components
from collections import defaultdict
     
def del_single(G, v, S, T):
    if G.has_node(v) and v != S and v != T:
        if G.degree(v) == 1:
            e = (list(G.in_edges(v)) + list(G.out_edges(v)))[0]
            G.remove_edge(e[0], e[1])
            G.remove_node(v)
            u = e[0] if e[1] == v else e[1]
            del_single(G, u, S, T)
        if G.degree(v) == 0:
            G.remove_node(v) 


def single_dfs(G, node, T, visited):
    if not visited[node]:
        visited[node] = True
        if node == T:
            return [node]
        else:
            for u, _ in G.in_edges(node):
                path = single_dfs(G, u, T, visited)
                if path:
                    return [node] + path 
            for _, u in G.out_edges(node):
                path = single_dfs(G, u, T, visited)
                if path:
                    return [node] + path
        visited[node] = False
    return []
    

def circuit_amperages(G, S, T, U):
    # Removing connected components without connection to S and T
    und_G = G.to_undirected()
    for component in connected_components(und_G):
        if S not in component or T not in component:
            for vertex in component:
                for (u, v) in und_G.edges[vertex]:
                    if G.has_edge(u, v): 
                        G.remove_edge(u, v)
                    else:
                        G.remove_edge(v, u)
                G.remove_node(vertex)

    # If every node was removed -> No connection between S and T
    if len(G.nodes) == 0:
        raise RuntimeError("No connection between S and T")

    # Deleting nodes with degree 1
    for v in list(G.nodes):
        del_single(G, v, S, T)

    # Mapping (u, v) -> index
    A = []
    B = []
    size = len(G.edges())
    edge_to_ind = {}
    ind_to_edge = []
    for (i, e) in enumerate(G.edges()):
        edge_to_ind[e] = i
        ind_to_edge.append(e)

    for v in G:
        if v != S and v != T:
            neighbrs_in = G.in_edges(v)
            neighbrs_out = G.out_edges(v)
            line = [0]*size
            for e in neighbrs_in:
                line[edge_to_ind[e]] = 1
            for e in neighbrs_out:
                line[edge_to_ind[e]] = -1
            A.append(line)
            B.append(0)
    
    line = np.zeros(shape = size)

    for (u, v) in list(G.in_edges(T)) + list(G.in_edges(S)):
        if (u != S or v != T) and (u != T or v != S):
            line[edge_to_ind[(u,v)]] = 1
    for (u, v) in list(G.out_edges(T)) + list(G.out_edges(S)):
        if (u != S or v != T) and (u != T or v != S):
            line[edge_to_ind[(u,v)]] = -1
    A.append(line)
    B.append(0)

    cycles = nx.cycle_basis(G.to_undirected())

    for cycle in cycles:
        line = np.zeros(shape = size)
        for i in range(len(cycle) - 1):
            if G.has_edge(cycle[i], cycle[i+1]):
                d = G.get_edge_data(cycle[i], cycle[i+1])
                line[edge_to_ind[(cycle[i], cycle[i+1])]] = d["R"]
            else:
                d = G.get_edge_data(cycle[i+1], cycle[i])
                line[edge_to_ind[(cycle[i+1], cycle[i])]] = -d["R"]
        if G.has_edge(cycle[-1], cycle[0]):
            d = G.get_edge_data(cycle[-1], cycle[0])
            line[edge_to_ind[(cycle[-1], cycle[0])]] = d["R"]
        else:
            d = G.get_edge_data(cycle[0], cycle[-1])
            line[edge_to_ind[(cycle[0], cycle[-1])]] = -d["R"]
        A.append(line)
        B.append(0)

    path = single_dfs(G, S, T, defaultdict(lambda: False))

    line = [0]*size
    for i in range(len(path) - 1):
        if G.has_edge(path[i], path[i+1]):
            d = G.get_edge_data(path[i], path[i+1])
            line[edge_to_ind[(path[i], path[i+1])]] = d["R"]
        else:
            d = G.get_edge_data(path[i+1], path[i])
            line[edge_to_ind[(path[i+1], path[i])]] = -d["R"]  
    
    A.append(line)
    B.append(U)  

    solve = sp.linalg.lstsq(A, B)[0] 

    return {ind_to_edge[i]: solve[i] for i in range(size)}

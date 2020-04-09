import networkx as nx

def circuit_from_file(filename):
    with open(filename, "r") as file:
        G = nx.DiGraph()
        S = None
        T = None
        U = None
        line = file.readline()
        while line:
            args = line.split(" ")
            if args[0] == "STU":
                S = int(args[1])
                T = int(args[2])
                U = int(args[3])
            else:
                u = int(args[0])
                v = int(args[1])
                R = int(args[2])
                G.add_edge(u, v, R=R)
            line = file.readline()
        return (G, S, T, U)

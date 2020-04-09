import networkx as nx

def solution_check(G, T, S, solution, U, epsilon = 10**(-10)):
    common_nodes = list(G.nodes())
    common_nodes.remove(T)
    common_nodes.remove(S)

    pass_msg = "passed"
    fail_msg = "failure"
    print_result = lambda passed: print(f"{pass_msg if passed else fail_msg}")

    print(f"Testing solution for circuit G ({G.number_of_nodes()} nodes, {len(G.edges())} edges)")
    print("Kirchhof's first law: ", end='')

    passed = True
    for node in common_nodes:
        i_sum = 0
        for e in G.in_edges(node):
            i_sum += solution[e]
        for e in G.out_edges(node):
            i_sum -= solution[e]
        if abs(i_sum) > epsilon:
            passed = False
            break
 
    print_result(passed)

    passed = True
    print("Kirchhof's second law: ", end='')

    G_copy = G.to_undirected()

    for _ in range(int(G.number_of_nodes() / 10)):
        u_sum = 0
        # path = single_dfs(G_copy, S, T, defaultdict(lambda: False))
        try:
            path = nx.shortest_path(G_copy, S, T)
        except nx.exception.NetworkXNoPath:
            break
        for i in range(len(path) - 1):
            if G.has_edge(path[i], path[i+1]):
                e = (path[i], path[i+1])
                d = G_copy.get_edge_data(e[0], e[1])
                u_sum += d["R"] * solution[e]
            else:
                e = (path[i+1], path[i])
                d = G_copy.get_edge_data(e[0], e[1])
                u_sum -= d["R"] * solution[e]
            G_copy.remove_edge(e[0], e[1])
        if abs(u_sum - U) > epsilon:
            passed = False
            break
    
    print_result(passed)
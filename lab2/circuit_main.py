from circuit_plotter import graph_show
from circuit_reader import circuit_from_file
from circuit_analyzer import circuit_amperages
from circuit_check import solution_check
import sys


if len(sys.argv) > 1:
    for file in sys.argv[1:]:
        (G, S, T, U) = circuit_from_file(file)
        print(f"Solving {file}")
        graph_show(G, S, T, U)

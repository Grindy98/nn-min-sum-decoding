import networkx as nx
import numpy as np

def get_tanner_graph(h_mat):
    def interp(x, n0, n1, m0, m1):
        return (x-n0) / (n1-n0) * (m1 - m0) + m0
    n_c, n_v = h_mat.shape
    t_graph = nx.Graph()
    
    t_graph.add_edges_from(( ('c'+str(c), 'v'+str(v)) for c, v in np.transpose(np.where(h_mat == 1)) ))
    # Positions for drawing
    pos_c = {'c'+str(i): (interp(i, 0, n_c-1, 0, 2), 1)for i in range(n_c)}
    pos_v = {'v'+str(i): (interp(i, 0, n_v-1, 0, 2), 0)for i in range(n_v)}
    return t_graph, {**pos_c, **pos_v}
    
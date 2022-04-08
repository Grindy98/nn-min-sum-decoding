import networkx as nx
import numpy as np
import tensorflow as tf

def get_tanner_graph(h_mat):
    def interp(x, n0, n1, m0, m1):
        return (x-n0) / (n1-n0) * (m1 - m0) + m0
    n_c, n_v = h_mat.shape
    t_graph = nx.Graph()
    
    t_graph.add_edges_from(( (f'c{c}', f'v{v}') for c, v in np.transpose(np.where(h_mat == 1)) ))
    # Positions for drawing
    pos_c = {f'c{i}': (interp(i, 0, n_c-1, 0, 2), 1)for i in range(n_c)}
    pos_v = {f'v{i}': (interp(i, 0, n_v-1, 0, 2), 0)for i in range(n_v)}
    return t_graph, {**pos_c, **pos_v}


def prob_to_llr(x):
    # y = 1/(1 + e^-x)
    # 1/y = 1 + e^-x
    # 1/y - 1 = e^-x
    # ln(1/y - 1) = -x
    # ln(y/(1-y)) = x
    assert(0 < x and x < 1)
    return tf.math.log(x/(1 - x))

def llr_to_prob(x):
    return tf.math.sigmoid(x)


def encode(gen_matrix, dataword):
    return np.mod(dataword @ gen_matrix, 2)

def parity_check(parity_matrix, codeword):
    return np.mod(codeword @ parity_matrix, 2)
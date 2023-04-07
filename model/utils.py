from itertools import count

import networkx as nx
import numpy as np
import tensorflow as tf
import galois
import scipy
import yaml

import layers

def get_tanner_graph(h_mat):
    def interp(x, n0, n1, m0, m1):
        return (x-n0) / (n1-n0) * (m1 - m0) + m0
    n_c, n_v = h_mat.shape
    t_graph = nx.Graph()
    
    t_graph.add_edges_from(( (f'c{c}', f'v{v}') for c, v in np.transpose(np.where(h_mat == 1)) ))
    # Positions for drawing
    pos_c = {f'c{i}': (0, interp(i, 0, n_c-1, 2, 0))for i in range(n_c)}
    pos_v = {f'v{i}': (1, interp(i, 0, n_v-1, 2, 0))for i in range(n_v)}
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

def get_bias_arr(model):
    bias_list = []
    for i in count(start=1):
        try:
            l = model.get_layer(f'hl_{i * 2}')
            bias_list.append(l.get_weights()[0])
        except ValueError:
            break
    bias_arr = np.concatenate(bias_list, axis=0)
    return bias_arr

def set_bias_arr(model, bias_arr):
    bias_list = np.split(bias_arr, bias_arr.shape[0], axis=0)
    for i, b in enumerate(bias_list):
        l = model.get_layer(f'hl_{(i + 1) * 2}')
        l.bias.assign(b)

def convert_to_int(arr, decimal_point_bit, llr_width):
    arr = arr * (2 ** decimal_point_bit)
    arr = np.clip(arr, -2**(llr_width - 1) + 1, 2**(llr_width - 1) - 1)
    arr = np.rint(arr)
    return arr.astype('int32')

def generate_adj_matrix_data(tanner_graph):
    data_out = {
        'odd_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'v'),
        'odd_inp_layer_mask': layers._create_input_layer_mask(tanner_graph),
        'even_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'c'),
        'output_mask': layers._create_final_layer_mask(tanner_graph),
    }
    return {k: np.array(v, dtype=int) for k, v in data_out.items()}


def get_gen_mat_dict():
    def swap_form(matrix):
        rows = matrix.shape[0]
        return np.concatenate((matrix[:, rows:], matrix[:, :rows]), axis=1)
    const_dict = scipy.io.loadmat('../data/constants.mat')
    
    return {
        'H_32_44': swap_form(np.array(const_dict['H_32_44'])),
        'H_4_7': swap_form(np.array(const_dict['H_4_7'])),

        'BCH_16_31': np.array(tf.constant(
        galois.generator_to_parity_check_matrix(
            galois.poly_to_generator_matrix(31, galois.BCH(31, 16).generator_poly)))),
        'BCH_11_15': np.array(tf.constant(
        galois.generator_to_parity_check_matrix(
            galois.poly_to_generator_matrix(15, galois.BCH(15, 11).generator_poly)))),
        'BCH_4_7': np.array(tf.constant(
        galois.generator_to_parity_check_matrix(
            galois.poly_to_generator_matrix(7, galois.BCH(7, 4).generator_poly)))),
    }

def get_params():
    with open('model_params.yml', 'r') as in_yaml:
        params = yaml.safe_load(in_yaml)
    params['DEFAULT_LLR_F'] = -prob_to_llr(params['CROSS_P']).numpy().tolist()
    params['DEFAULT_LLR'] = convert_to_int(params['DEFAULT_LLR_F'], params['DECIMAL_POINT_BIT'], params['LLR_WIDTH']).tolist()
    return params
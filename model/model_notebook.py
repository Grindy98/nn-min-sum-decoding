# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: py_new
#     language: python
#     name: py_new
# ---

# %%
# %config Completer.use_jedi = False
# %load_ext autoreload
# %autoreload 2

# %% [markdown]
# # Model Implementation and Configuration

# %% [markdown]
# ## Imports and Data Load

# %%
import tensorflow as tf
import scipy.io

import numpy as np
import galois
import networkx as nx
from matplotlib import pyplot as plt


# %%
def swap_form(matrix):
    rows = matrix.shape[0]
    return np.concatenate((matrix[:, rows:], matrix[:, :rows]), axis=1)


# %%
const_dict = scipy.io.loadmat('../data/constants.mat')
H_32_44 = swap_form(np.array(const_dict['H_32_44']))
H_4_7 = swap_form(np.array(const_dict['H_4_7']))

# %%
BCH_16_31 = np.array(tf.constant(
    galois.generator_to_parity_check_matrix(
        galois.poly_to_generator_matrix(31, galois.BCH(31, 16).generator_poly))))

# %% [markdown]
# ## Function Definitions

# %%
from keras.layers import Input
from keras.models import Model

from layers import OutputLayer

# %%
from keras.layers import Input
from keras.models import Model

from layers import OddLayerFirst, OddLayer, EvenLayer, OutputLayer
import layers

def create_model(tanner_graph, iters = 1):
    n_v = len([n for n in tanner_graph.nodes if n.startswith('v')])
    
    # Create input of shape corresponding to v-node number
    inp = Input(shape=(n_v,), name='in')
    
    # First pair of Odd-Even layer is mandatory 
    pipe = OddLayerFirst(tanner_graph, 'hl_1')(inp)
    pipe = EvenLayer(tanner_graph, 'hl_2')(pipe)
    # If number of iterations greater than 1, intermediary pairs 
    # will be added corresponding with another iteration of BP
    for i in range(3, 2 * iters, 2):
        pipe = OddLayer(tanner_graph, f'hl_{i}')([inp, pipe])
        pipe = EvenLayer(tanner_graph, f'hl_{i + 1}')(pipe)
    
    # Final output layer
    outp = OutputLayer(tanner_graph, 'out')([inp, pipe])
    return Model(inp, outp), n_v
    


# %%
from utils import prob_to_llr, llr_to_prob

def loss_wrapper(n_v, e_clip=1e-10):
    def inner(y_true, y_pred):
        # Fix for None, None shape
        y_true = tf.reshape(y_true, [-1, n_v])
        y_pred = tf.reshape(y_pred, [-1, n_v])
        
        y_true = tf.where(y_true <= 0, 0.0, 1.0)
        y_pred = llr_to_prob(y_pred)
        N = y_true.shape[1]
        out = y_true * tf.math.log(tf.clip_by_value(y_pred, e_clip, 1.0))
        out += (1 - y_true) * tf.math.log(tf.clip_by_value(1 - y_pred, e_clip, 1.0))
        out = tf.math.reduce_sum(out, axis=1)
        out = -1/N * out
        return out
    return inner


# %%
import keras.backend as K 
from utils import encode

# Generator matrix for shape and creation of codewords
def datagen_creator(gen_matrix, data_limit=1000000):
    def datagen(batch_size, p, zero_only=True):
        neg_llr = prob_to_llr(0.01)
        pos_llr = -neg_llr
        for _ in range(data_limit):
            input_shape = (batch_size, gen_matrix.shape[0])
            if zero_only:
                y = galois.GF2(np.zeros(input_shape, dtype=int))
            else:
                y = galois.GF2(np.random.choice([0, 1], size=input_shape))

            # Transform dataword to codeword
            y = y @ gen_matrix

            # This is the binary symmetric channel mask
            mask = galois.GF2(np.random.choice([0, 1], size=y.shape, p=[1-p, p]))
            x = y + mask

            # Transform from bool to llr
            x = np.where(x, pos_llr, neg_llr)
            y = np.where(y, pos_llr, neg_llr)
            x = x.astype('float32')
            y = y.astype('float32')
            yield x, y
    return datagen;
        


# %%
model, n_v = create_model(G, 5)
# model.summary()

# %%
def generate_adj_matrix_data(tanner_graph):
    data_out = {
        'odd_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'v'),
        'odd_inp_layer_mask': layers._create_input_layer_mask(tanner_graph),
        'even_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'c'),
        'output_mask': layers._create_final_layer_mask(tanner_graph),
    }
    return {k: np.array(v, dtype=int) for k, v in data_out.items()}
        


# %%
np.savez('../data/adj_matrices.npz', **generate_adj_matrix_data(G))

# %%
# tf.keras.utils.plot_model(model, show_shapes=True)

# %%
from tensorflow.keras.optimizers import Adam

from metrics import BER, FER

def get_compiled_model(tanner_graph, iters = 1):
    model, n_v = create_model(G, BF_ITERS)
    adam = Adam(learning_rate=0.1)
    model.compile(
        optimizer=adam,
        loss=loss_wrapper(n_v),
        metrics = [
            BER(),
            FER()
        ]
    )
    return model, n_v


# %%
from itertools import count
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


# %%
def convert_to_int(arr):
    arr = arr * (2 ** DECIMAL_POINT_BIT)
    arr = np.clip(arr, -2**(INT_SIZE - 1), 2**(INT_SIZE - 1) - 1)
    arr = np.rint(arr)
    return arr.astype('int32')


# %%
import keras.backend as K 
from utils import encode

# Generator matrix for shape and creation of codewords
def datagen_creator(gen_matrix, data_limit=1000000):
    def datagen(batch_size, p, zero_only=True, test_int=False):
        neg_llr = prob_to_llr(p)
        pos_llr = -neg_llr
        for _ in range(data_limit):
            input_shape = (batch_size, gen_matrix.shape[0])
            if zero_only:
                y = galois.GF2(np.zeros(input_shape, dtype=int))
            else:
                y = galois.GF2(np.random.choice([0, 1], size=input_shape))

            # Transform dataword to codeword
            y = y @ gen_matrix

            # This is the binary symmetric channel mask
            mask = galois.GF2(np.random.choice([0, 1], size=y.shape, p=[1-p, p]))
            x = y + mask

            # Transform from bool to llr
            x = np.where(x, pos_llr, neg_llr)
            y = np.where(y, pos_llr, neg_llr)
            x = x.astype('float64')
            y = y.astype('float64')
            if test_int:
                x = convert_to_int(x)
                y = convert_to_int(y)
            yield x, y
    return datagen;


# %%
def generate_adj_matrix_data(tanner_graph):
    data_out = {
        'odd_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'v'),
        'odd_inp_layer_mask': layers._create_input_layer_mask(tanner_graph),
        'even_prev_layer_mask': layers._create_prev_layer_mask(tanner_graph, 'c'),
        'output_mask': layers._create_final_layer_mask(tanner_graph),
    }
    return {k: np.array(v, dtype=int) for k, v in data_out.items()}
        


# %% [markdown]
# ## Configurations

# %%
# active_mat = H_32_44
active_mat = BCH_16_31

DECIMAL_POINT_BIT = 4
INT_SIZE = 8

BF_ITERS = 5

p = 0.01

# %% [markdown]
# # Model training and testing
#

# %% [markdown]
# ## Tanner Graph

# %%
from utils import get_tanner_graph

G, pos = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))

nx.draw_networkx(G, pos)

# %%
np.savez('../data/adj_matrices.npz', **generate_adj_matrix_data(G))

# %% [markdown]
# ## Model Compile and Fit
#
# **RERUN FROM HERE IF MODEL PARAMETERS ALTERED**

# %%
model, n_v = get_compiled_model(G, BF_ITERS)
# model.summary()

# %%
# tf.keras.utils.plot_model(model, show_shapes=True)

# %%
gen = datagen_creator(gen_mat)(120, p)

# %%
history = model.fit(
    x=gen,
    epochs=10,
    verbose="auto",
    callbacks=None,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    class_weight=None,
    sample_weight=None,
    initial_epoch=0,
    steps_per_epoch=50,
    validation_steps=None,
    validation_batch_size=None,
    validation_freq=1,
    max_queue_size=10,
    workers=1,
    use_multiprocessing=False,
)

# %%
model.evaluate(
    x=datagen_creator(gen_mat)(120, p, zero_only=False),
    steps=100 
)

# %% [markdown]
# ## Bias Extraction and Integer Cast Evaluation

# %%
# Extract biases
bias_arr = get_bias_arr(model)
bias_arr_casted = convert_to_int(bias_arr)
bias_arr_casted.dtype


# %%
# Test biases
int_model, n_v = get_compiled_model(G, BF_ITERS)
set_bias_arr(int_model, bias_arr_casted.astype('float64'))

        G, pos = get_tanner_graph(mat)
        gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(mat))
        if not identity:
            model, n_v = create_model(G, 5)
            model.compile(
                optimizer=adam,
                loss=loss_wrapper(n_v)
            )
            gen = datagen_creator(gen_mat)(120, p)
            model.fit(
                x=gen,
                epochs=10,
                verbose="auto",
                callbacks=None,
                validation_split=0.0,
                validation_data=None,
                shuffle=True,
                class_weight=None,
                sample_weight=None,
                initial_epoch=0,
                steps_per_epoch=50,
                validation_steps=None,
                validation_batch_size=None,
                validation_freq=1,
                max_queue_size=10,
                workers=1,
                use_multiprocessing=False,
            )
            stats.append(get_stats_model(model, datagen_creator(gen_mat), p))
        else:
            # Mockup model with no change
            stats.append(get_stats_model(None, datagen_creator(gen_mat), p))
    return stats


# %%
int_model.evaluate(
    x=datagen_creator(gen_mat)(120, p, zero_only=False, test_int=True),
    steps=100 
)


# %%
# Save biases
np.save('../data/biases.npy', bias_arr_casted)

# %%

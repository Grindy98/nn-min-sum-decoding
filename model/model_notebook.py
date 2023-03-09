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
import json
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
BCH_4_7 = np.array(tf.constant(
    galois.generator_to_parity_check_matrix(
        galois.poly_to_generator_matrix(7, galois.BCH(7, 4).generator_poly))))

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
    arr = np.clip(arr, -2**(LLR_WIDTH - 1), 2**(LLR_WIDTH - 1) - 1)
    arr = np.rint(arr)
    return arr.astype('int32')


# %%
import keras.backend as K 
from utils import encode

# Generator matrix for shape and creation of codewords
def datagen_creator(gen_matrix, data_limit=1000000):
    def datagen(batch_size, p, zero_only=True, test_int=False):
        pos_llr = -prob_to_llr(p)
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
            if not test_int:
                x = np.where(x, pos_llr, -pos_llr)
                y = np.where(y, pos_llr, -pos_llr)
            else:
                x = np.where(x, DEFAULT_LLR, -DEFAULT_LLR)
                y = np.where(y, DEFAULT_LLR, -DEFAULT_LLR)
            x = x.astype('float64')
            y = y.astype('float64')
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
#
# **RERUN FROM HERE FOR CHANGES IN PARAMETERS**

# %%
print(H_4_7)

# %%
print(BCH_4_7)

# %%
# Generator matrix

# active_mat = H_32_44
# active_mat = BCH_16_31
active_mat = BCH_4_7

# active_mat = np.array(tf.constant(
#     galois.generator_to_parity_check_matrix(
#         galois.poly_to_generator_matrix(15, galois.BCH(15, 7).generator_poly))))

# INT CONVERSION
DECIMAL_POINT_BIT = 4
LLR_WIDTH = 8

# HW
INT_SIZE = 8 # FOR COUNTER
RESET_VAL = 1
AXI_WIDTH = 8
EXTENDED_BITS = 4 # FOR SATURATION

# MODEL METAPARAMS
BF_ITERS = 5

CROSS_P = 0.01

# %% [markdown]
# # Model training and testing
#

# %% [markdown]
# ## Tanner Graph

# %%
from utils import get_tanner_graph

G, pos = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))

fig, ax = plt.subplots(figsize=[8, 12])
nx.draw_networkx(G, pos, ax=ax, node_size=300, font_size=9)
plt.show()

# %% [markdown]
# ## LLR Value

# %%
DEFAULT_LLR = int(convert_to_int(-prob_to_llr(CROSS_P).numpy()))

# %% [markdown]
# ## Model Compile and Fit
#
# **RERUN FROM HERE FOR MODEL REFRESH**

# %%
model, n_v = get_compiled_model(G, BF_ITERS)
model.summary()

# %%
# tf.keras.utils.plot_model(model, show_shapes=True)

# %%
gen = datagen_creator(gen_mat)(120, CROSS_P)

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
    x=datagen_creator(gen_mat)(120, CROSS_P, zero_only=False),
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

# %%
int_model.evaluate(
    x=datagen_creator(gen_mat)(120, CROSS_P, zero_only=False, test_int=True),
    steps=100 
)

# %% [markdown]
# # EXPORTS

# %%
# Matrix data
adj_matrix_dict = generate_adj_matrix_data(G)
np.savez('../data/adj_matrices.npz', **adj_matrix_dict)
np.save('../data/generator.npy', gen_mat)

# %%
# Parameters
par_dict = {
    'N_V': adj_matrix_dict['odd_inp_layer_mask'].shape[0], 
    'E': adj_matrix_dict['odd_prev_layer_mask'].shape[0], 
    'DECIMAL_POINT_BIT': DECIMAL_POINT_BIT,
    'INT_SIZE': INT_SIZE,
    'BF_ITERS': BF_ITERS,
    'CROSS_P': CROSS_P,
    'RESET_VAL': RESET_VAL,
    'AXI_WIDTH': AXI_WIDTH,
    'LLR_WIDTH': LLR_WIDTH,
    'EXTENDED_BITS': EXTENDED_BITS,
    'DEFAULT_LLR': DEFAULT_LLR,
}
with open('../data/params.json', 'w') as jout:
    json.dump(par_dict, jout, indent=2)

# %%
# Save biases
np.save('../data/biases.npy', bias_arr_casted)

# %% [markdown]
# # DEBUG / IMPORTS
#
# **ONLY RUN WITHOUT RUNNING THE EXPORTS SECTION**

# %%
bias_arr_casted = np.load('../data/biases.npy')
set_bias_arr(int_model, bias_arr_casted.astype('float64'))
int_model.evaluate(
    x=datagen_creator(gen_mat)(120, CROSS_P, zero_only=False, test_int=True),
    steps=100 
)

# %%
x = np.array([int(x) for x in list('0100101')]).reshape(1, 7)
x = np.where(x, DEFAULT_LLR, -DEFAULT_LLR)
x = x.astype('float32')
y = int_model.predict(x)
np.where(x > 0, 1, 0)

# %%
y

# %%
hl_1 = int_model.get_layer(name='hl_1')(x)
hl_1

# %%
hl_2 = int_model.get_layer(name='hl_2')(hl_1)
hl_2

# %%
int_model.get_layer(name='hl_2').bias

# %%
hl_3 = int_model.get_layer(name='hl_3')([x, hl_2])
hl_3

# %%
hl_4 = int_model.get_layer(name='hl_4')(hl_3)
hl_4

# %%
int_model.get_layer(name='hl_4').bias

# %%
hl_5 = int_model.get_layer(name='hl_5')([x, hl_4])
hl_5

# %%
hl_6 = int_model.get_layer(name='hl_6')(hl_5)
hl_6

# %%
hl_7 = int_model.get_layer(name='hl_7')([x, hl_6])
hl_7

# %%
hl_8 = int_model.get_layer(name='hl_8')(hl_7)
hl_8

# %%
hl_9 = int_model.get_layer(name='hl_9')([x, hl_8])
hl_9

# %%
hl_10 = int_model.get_layer(name='hl_10')(hl_9)
hl_10

# %%
out = int_model.get_layer(name='out')([x, hl_10])
out

# %%
tf.keras.utils.plot_model(int_model, show_shapes=True)

# %%

# %%

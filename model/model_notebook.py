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

# %%

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

# %%
from utils import get_tanner_graph

# active_mat = H_32_44
active_mat = BCH_16_31

G, pos = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))

nx.draw_networkx(G, pos)

# %%
from keras.layers import Input
from keras.models import Model

from layers import OutputLayer

# %%
from keras.layers import Input
from keras.models import Model

from layers import OddLayerFirst, OddLayer, EvenLayer, OutputLayer

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
# tf.keras.utils.plot_model(model, show_shapes=True)

# %%
from tensorflow.keras.optimizers import Adam
adam = Adam(learning_rate=0.1)


model.compile(
    optimizer=adam,
    loss=loss_wrapper(n_v)
)

# %%
p = 0.01
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


# %%
def get_stats_model(model, datagen, p):
    def update_tuple(tup, tensor):
        total = tf.reduce_sum(tf.ones(tensor.shape)).numpy()
        total_neg = tf.math.count_nonzero(~tensor).numpy()
        return tup[0] + total_neg, tup[1] + total
    
    datagen = datagen(100, p, zero_only=False)
    # Gather data until there are more than 100 errors
    ber = (0, 0)
    fer = (0, 0)
    for x, y_true in datagen:
        if model:
            y_pred = model.predict(x)
        else:
            y_pred = x
        y_true = tf.where(llr_to_prob(y_true) > 0.5, 1, 0)
        y_pred = tf.where(llr_to_prob(y_pred) > 0.5, 1, 0)
        compare = tf.equal(y_true, y_pred)
        reduced = tf.reduce_all(compare, axis=1)
        ber = update_tuple(ber, compare)
        fer = update_tuple(fer, reduced)
        print(ber, fer)
        if fer[0] > 100:
            break
    return ber[0]/ber[1], fer[0]/fer[1]
        
        
        

# %%
get_stats_model(model, datagen_creator(gen_mat), p)


# %%
def generate_stats_for_matrix(mat, p_range, identity = False):
    stats = []
    for p in p_range:

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
from tabulate import tabulate
def create_text_table(fname, prob, data):
    with open(fname, 'w') as outf:
        outf.write(tabulate(np.concatenate([prob.reshape(-1, 1), data], axis=1), headers=['Probability', 'BER', 'FER']))


# %%
# Log range from 0.25 to 2^-12
p_range = np.logspace(-2, -12, num=10, base=2)
p_range

# %%
BCH_16_31_stats = generate_stats_for_matrix(BCH_16_31, p_range)

# %%
H_32_44_stats = generate_stats_for_matrix(H_32_44, p_range)

# %%
identity_stats = generate_stats_for_matrix(H_32_44, p_range, True)

# %%
H_4_7_stats

# %%
# with open("stats.npz", 'wb') as outf:
#     np.savez(outf, **{
#         'p_range' : p_range,
#         'H_32_44' : H_32_44_stats,
#         'H_4_7': H_4_7_stats,
#         'BCH_16_31': BCH_16_31_stats,
#         'identity': identity_stats
#     })

# %%
with np.load("stats.npz") as data:
    fig = plt.figure(figsize=(10,10))
    plt.xlabel('BER')
    plt.ylabel('Crossover probability')
    plt.loglog(data['H_32_44'][:, 0], data['p_range'], "r", label="H_32_44 BER")
    plt.loglog(data['BCH_16_31'][:, 0], data['p_range'], "g", label="BCH_16_31 BER")
    plt.loglog(data['identity'][:, 0], data['p_range'], "b", label="identity BER")
    plt.gca().invert_xaxis()
    plt.grid(visible=True, which='major', linewidth=1, linestyle='-')
    plt.grid(visible=True, which='minor', linewidth=0.5, linestyle='--')
    plt.legend()
    fig.savefig('BER.svg')

# %%
with np.load("stats.npz") as data:
    fig = plt.figure(figsize=(10,10))
    plt.xlabel('FER')
    plt.ylabel('Crossover probability')
    plt.loglog(data['H_32_44'][:, 1], data['p_range'], "r", label="H_32_44 FER")
    plt.loglog(data['BCH_16_31'][:, 1], data['p_range'], "g", label="BCH_16_31 FER")
    plt.loglog(data['identity'][:, 1], data['p_range'], "b", label="identity FER")
    plt.gca().invert_xaxis()
    plt.grid(visible=True, which='major', linewidth=1, linestyle='-')
    plt.grid(visible=True, which='minor', linewidth=0.5, linestyle='--')
    plt.legend()
    fig.savefig('FER.svg')

# %%
with np.load("stats.npz") as data:
    create_text_table('H_32_44.txt', data['p_range'], data['H_32_44'])
    create_text_table('BCH_16_31.txt', data['p_range'], data['BCH_16_31'])

# %%

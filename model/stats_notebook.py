# ---
# jupyter:
#   jupytext:
#     formats: py:percent
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
# ## Configurations

# %%
import json
import yaml
import tensorflow as tf
import scipy.io
from scipy.special import erfc
from scipy.stats import binom
import itertools

import numpy as np
import galois
import networkx as nx
from matplotlib import pyplot as plt

import utils as utils_module
from utils import prob_to_llr, llr_to_prob, get_bias_arr, get_params,\
    set_bias_arr, generate_adj_matrix_data, get_gen_mat_dict, get_tanner_graph

from model import get_compiled_model, datagen_creator

def convert_to_int(arr):
    return utils_module.convert_to_int(arr, params['DECIMAL_POINT_BIT'], params['LLR_WIDTH'])


# %%
gen_mat_dict = get_gen_mat_dict()

active_mat = gen_mat_dict['BCH_16_31']
params = get_params()
params

# %%
G, _ = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))
model, n_v = get_compiled_model(G, params['BF_ITERS'])
model.summary()

# %%
callbacks = [tf.keras.callbacks.EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)]

# %%
gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)

# %%
history = model.fit(
    x=gen,
    epochs=15,
    verbose="auto",
    callbacks=callbacks,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    class_weight=None,
    sample_weight=None,
    initial_epoch=0,
    steps_per_epoch=100,
    validation_steps=None,
    validation_batch_size=None,
    validation_freq=1,
    max_queue_size=10,
    workers=1,
    use_multiprocessing=False,
)

# %%
from tensorflow.keras.optimizers import Adam
import tensorflow.keras.layers as layers_k
from tensorflow.keras.models import Model
from metrics import BER, FER

def get_ident_model(n):
    inp = layers_k.Input(shape=(n,))
    model_id = Model(inp, inp)

    adam = Adam(learning_rate=0.1)
    model_id.compile(adam, metrics=[BER(), FER()])
    return model_id


# %%
def compute_ber(EbN0):
    return 0.5*erfc(np.sqrt(10 ** (EbN0/10)))
compute_ber(np.array([8, 9, 10]))

# %%
X_theory = np.arange(-5, 9)
X_sim = np.arange(-5, 9)

# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.semilogy(X_theory, compute_ber(X_theory),marker='',linestyle='-',label='BPSK Theory')
ax.set_xlabel('$E_b/N_0(dB)$');ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.set_xlim(-5,13);ax.grid(True);
ax.legend();plt.show()

# %%
binom.sf(4,40,0.01)


# %%

# %% [markdown]
# ## Model Stats

# %%
def model_stats(eval_fun):
    def wrapper(probs, gen_mat, model_dict, step_factor=20):
        stat_list = []
        n_v = gen_mat.shape[1]
        for p in probs:
            steps = max(int(1/p/n_v * step_factor), 51)
            eval_res = eval_fun(p, steps, model_dict, gen_mat)
            stat_list.append((p, eval_res))
        dict_return = {}
        for x in stat_list: 
            for k, v in x[1].items():
                if k not in dict_return:
                    dict_return[k] = []
                dict_return[k].append(v) 
        return [x[0] for x in stat_list], dict_return
    return wrapper


# %%
@model_stats
def BCH_model(p, steps, model_dict, gen_mat):
    ret = {}
    gen = datagen_creator(gen_mat)(200, p, params['DEFAULT_LLR_F'], zero_only=False)
    gen_list = itertools.tee(gen , len(model_dict))
    for i, (k, m) in enumerate(model_dict.items()):
        print(f'For {k} - {p}')
        ret[k] = m.evaluate(gen_list[i], steps=steps, return_dict=True)
    return ret

#BCH_model(compute_ber(X_sim))


# %%
def multiple_stats(probs, key_list):
    ret_tup = None
    for k in key_list:
        if isinstance(k, tuple):
            k, step_weight = k[0], k[1] 
        else:
            k, step_weight = k, 20
        active_mat = gen_mat_dict[k]
        G, _ = get_tanner_graph(active_mat)
        gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))
        model, n_v = get_compiled_model(G, params['BF_ITERS'])
        gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)
        model.fit(
            x=gen,
            epochs=15,
            callbacks=callbacks,
            steps_per_epoch=100,
        )
        stat_tup = BCH_model(probs, gen_mat, {f'{k}_m': model, f'{k}_i': get_ident_model(n_v)}, step_weight)
        if not ret_tup:
            ret_tup = stat_tup
            continue
        assert(ret_tup[0] == stat_tup[0])
        ret_tup[1].update(stat_tup[1])
    return ret_tup


# %%
multiple_stats(np.geomspace(1e-1, 1e-3, 5), ['BCH_16_31']*2)

# %%
import itertools

x, y = itertools.tee(datagen_creator(galois.GF2(np.eye(4, dtype=int)))(1, 0.1, 1, zero_only=False), 2)
print(next(x))
print(next(x))
print(next(x))
print(next(x))
print(next(y))
print(next(y))

# %%
p = stat_list[4][0]
int(convert_to_int(-prob_to_llr(p).numpy()))
stat_list[4][1]

# %%
[(x[1]['BER'], y) for x, y in zip(stat_list, X_sim)]

# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.semilogy(X_theory, compute_ber(X_theory),marker='',linestyle='-',label='BPSK Theory')
ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list],marker='X',linestyle='-', color='b', label='BPSK Theory')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.set_xlim(-5,13)
ax.grid(True)
ax.legend()

plt.show()


# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.set_xlim(-5,13)
ax.grid(True)
ax.legend()

plt.show()

# %%
stat_list = BCH_model(np.geomspace(1e-1, 1e-3, 5), {'bch': model, 'ident': model_id})

# %%
stat_list


# %%
def extract(stats, key, what):
    return stats[0], [x[what] for x in stats[1][key]]

fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
ax.loglog(*extract(stat_list, 'bch', 'BER'), '-r', label='Decoder')
ax.loglog(*extract(stat_list, 'ident', 'BER'), '--b', label='Identity')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.grid(True)
ax.legend()
ax.invert_xaxis()


plt.show()

# %%
all_stats = multiple_stats(np.geomspace(1e-1, 5e-5, 7), ['H_32_44', 'H_4_7', 'BCH_11_15', 'BCH_16_31'])

# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
# ax.loglog(*extract(all_stats, 'BCH_16_31_m', 'BER'), '-r', label='Decoder')
# ax.loglog(*extract(all_stats, 'BCH_16_31_i', 'BER'), '--r', label='Identity')
# ax.loglog(*extract(all_stats, 'BCH_11_15_m', 'BER'), '-k', label='Decoder')
# ax.loglog(*extract(all_stats, 'BCH_11_15_i', 'BER'), '--k', label='Identity')
ax.loglog(*extract(all_stats, 'H_32_44_m', 'BER'), '-b', label='Decoder')
ax.loglog(*extract(all_stats, 'H_32_44_i', 'BER'), '--b', label='Identity')
ax.loglog(*extract(all_stats, 'H_4_7_m', 'BER'), '-g', label='Decoder')
ax.loglog(*extract(all_stats, 'H_4_7_i', 'BER'), '--g', label='Identity')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.grid(True)
ax.legend()
ax.invert_xaxis()

# %%
all_stats_2 = multiple_stats(np.geomspace(1e-1, 5e-5, 7), [('H_4_7', 100), ('BCH_11_15', 40)] )

# %%
 

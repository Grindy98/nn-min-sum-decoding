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
import pickle
import tensorflow as tf
import scipy.io
from scipy.special import erfc
from scipy.stats import binom
import itertools
import pathlib
import re
import traceback

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

# %%

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

@model_stats
def BCH_model(p, steps, model_dict, gen_mat):
    ret = {}
    gen = datagen_creator(gen_mat)(200, p, params['DEFAULT_LLR_F'], zero_only=False)
    gen_list = itertools.tee(gen , len(model_dict))
    for i, (k, m) in enumerate(model_dict.items()):
        print(f'For {k} - {p}')
        ret[k] = m.evaluate(gen_list[i], steps=steps, return_dict=True)
    return ret


def multiple_stats(probs, key_list, try_cache = True, update_cache = True):
    key_list = [x if isinstance(x, tuple) else (x, 20) for x in key_list ]
    key_list = key_list_orig = set(key_list)
    PATH = '../data/stats/pystats.pkl'
    def extract_ret(ret):
        return {k: v for k, v in ret.items() if k in key_list_orig}
    
    ret_dict = {}
    if try_cache:
        try:
            with open(PATH, 'rb') as infile:
                data = pickle.load(infile)
            ret_dict.update(data)
            key_list -= data.keys()
            if not key_list:
                # All already cached
                return extract_ret(ret_dict)
            print(f'Loaded from cache: {list(data.keys())}')
        except Exception as e:
            print(f'Cannot load cache: {e}')
            print(traceback.format_exc())

    for k, step_weight in key_list:
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
        print(f'Get stats for {k}')
        stat_tup = BCH_model(probs, gen_mat, {'m': model, 'i': get_ident_model(n_v)}, step_weight)
        stat_dict = stat_tup[1]
        stat_dict['p'] = stat_tup[0]
        ret_dict.update({(k, step_weight): stat_dict})
        # Also dump updated data in case of crash
        if update_cache:
            with open(PATH, 'wb') as outfile:
                pickle.dump(ret_dict, outfile)
    return extract_ret(ret_dict)


def get_c_stats(): 
    ret_dict = {}
    for p in pathlib.Path('../data/stats/').iterdir():
        if match := re.match(r'stats_(.*)\.json', p.name):
            key = match.group(1)
            with p.open('rb') as infile:
                c_stats = json.load(infile)
            ret_dict[(f'{key}_C', -1)] = {'m': [{'BER': x['ber'], 'FER': x['fer']} for x in c_stats],
                                          'p': [x['p'] for x in c_stats]}
    return ret_dict

def extract(stats, key, what, ident=False):
    key_lst = [x for x in stats.keys() if x[0] == key]
    key_lst.sort(key=lambda x: x[1], reverse=True)
    key = key_lst[0]
    x_lst = stats[key]['p']
    y_lst = [x[what] for x in stats[key]['i' if ident else 'm']]
    return x_lst, y_lst


# %%

# %%
all_stats = multiple_stats(np.geomspace(1e-1, 5e-5, 7), ['H_32_44', 'H_4_7', 'BCH_11_15', 'BCH_16_31'])
all_stats

# %%
with open('../data/stats/pystats.pkl', 'rb') as infile:
    z = pickle.load(infile)
    print(list(z[1].keys()))

# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
# ax.loglog(*extract(all_stats, 'BCH_16_31_m', 'BER'), '-r', label='Decoder')
# ax.loglog(*extract(all_stats, 'BCH_16_31_i', 'BER'), '--r', label='Identity')
# ax.loglog(*extract(all_stats, 'BCH_11_15_m', 'BER'), '-k', label='Decoder')
# ax.loglog(*extract(all_stats, 'BCH_11_15_i', 'BER'), '--k', label='Identity')
ax.loglog(*extract(all_stats, 'H_32_44', 'BER'), '-b', label='Decoder')
ax.loglog(*extract(all_stats, 'H_32_44', 'BER', ident=True), '--b', label='Identity')
ax.loglog(*extract(all_stats, 'H_4_7', 'BER'), '-g', label='Decoder')
ax.loglog(*extract(all_stats, 'H_4_7', 'BER', ident=True), '--g', label='Identity')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.grid(True)
ax.legend()
ax.invert_xaxis()

# %%
all_stats_2 = multiple_stats(np.geomspace(1e-1, 5e-5, 7), [('H_4_7', 100), ('BCH_11_15', 40)] )

# %%
c_stats = get_c_stats()
c_stats


# %%
merge_stats = all_stats | c_stats
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.loglog(*extract(merge_stats, 'BCH_16_31', 'BER', ident=True), '--b', label='Identity')
ax.loglog(*extract(merge_stats, 'BCH_16_31', 'BER'), '-b', label='Decoder')
ax.loglog(*extract(merge_stats, 'BCH_16_31_C', 'BER'), '-g', label='Decoder C')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.set_title('Probability of Bit Error for BPSK over AWGN channel')
ax.grid(True)
ax.legend()
ax.invert_xaxis()

# %%

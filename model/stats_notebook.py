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
#     display_name: Python [conda env:nn]
#     language: python
#     name: conda-env-nn-py
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
import os

import numpy as np
import galois
import networkx as nx
from matplotlib import pyplot as plt

import utils as utils_module
from utils import prob_to_llr, llr_to_prob, get_bias_arr, get_params, convert_to_int,\
    set_bias_arr, generate_adj_matrix_data, get_gen_mat_dict, get_tanner_graph, get_bias_path

from model import get_compiled_model, datagen_creator

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
gen_mat_dict = get_gen_mat_dict()

active_mat = gen_mat_dict['BCH_11_15']
params = get_params()
params

callbacks = []

# %%
G, G_pos = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))
model, n_v = get_compiled_model(G, params['BF_ITERS'])
model.summary()

# %%
plotted_model, _ = get_compiled_model(G, 2)
tf.keras.utils.plot_model(plotted_model, show_shapes=True, rankdir='TB', to_file='images/model.pdf')

# %%
fig, ax = plt.subplots(figsize=[7, 7])
nx.draw_networkx(G, G_pos, ax=ax, node_size=400, font_size=10)
plt.savefig('images/tanner.pdf', bbox_inches="tight")
plt.show()

# %%
from layers import _stdize
def calc_edge_props(G, edge, cnode=True):
    edge_color = []
    edge_width = []
    matching_edges = set(_stdize(x) for x in G.edges(edge[0] if cnode else edge[1]))
    matching_edges -= set([edge])
    
    for e in G.edges():
        e = _stdize(e)
        if e in matching_edges:
            edge_color.append('blue')
            edge_width.append(2.0)
        elif e == edge:
            edge_color.append('red')
            edge_width.append(4.0)
        else:
            edge_color.append('black')
            edge_width.append(1.0)
    return {'edge_color': edge_color, 'width':edge_width}

fig, axs = plt.subplots(figsize=[7, 7], ncols=2)
nx.draw_networkx(G, G_pos, ax=axs[0], node_size=400, font_size=10, **calc_edge_props(G, ('c2', 'v2'), True))
nx.draw_networkx(G, G_pos, ax=axs[1], node_size=400, font_size=10, **calc_edge_props(G, ('c2', 'v2'), False))
# plt.subplots_adjust(wspace=0, hspace=0)
plt.savefig('images/tanner_highlight.pdf', bbox_inches="tight")
plt.show()

# %%
gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)

# %%
history = model.fit(
    x=gen,
    epochs=10,
    verbose="auto",
    callbacks=callbacks,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    class_weight=None,
    sample_weight=None,
    initial_epoch=0,
    steps_per_epoch=200,
    validation_steps=None,
    validation_batch_size=None,
    validation_freq=1,
    max_queue_size=10,
    workers=1,
    use_multiprocessing=False,
)


# %% [markdown]
# ## Theoretical BER stats

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

@model_stats
def BCH_model(p, steps, model_dict, gen_mat):
    ret = {}
    gen = datagen_creator(gen_mat)(200, p, params['DEFAULT_LLR_F'], zero_only=False)
    gen_list = itertools.tee(gen , len(model_dict))
    for i, (k, m) in enumerate(model_dict.items()):
        print(f'For {k} - {p}')
        ret[k] = m.evaluate(gen_list[i], steps=steps, return_dict=True)
    return ret


def multiple_stats(probs, key_list, try_cache = True, update_cache = True, rerun_listed=False, use_saved_biases=True):
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
            
            if rerun_listed:
                for k in key_list:
                    data.pop(k, None)
            else:
                key_list -= data.keys()
            ret_dict.update(data)
            if not key_list:
                # All already cached
                return extract_ret(ret_dict)
            print(f'Loaded from cache: {list(data.keys())}')
        except Exception as e:
            print(f'Cannot load cache: {e}')
            print(traceback.format_exc())
    
    if use_saved_biases:
        error_key_list = []
        for k, _ in key_list:
            if not os.path.exists(get_bias_path(key=k)):
                error_key_list.append(k)
        if error_key_list:        
            raise ValueError(f"No saved biases for {', '.join([str(x) for x in error_key_list])}")
    
    for k, step_weight in key_list:
        active_mat = gen_mat_dict[k]
        G, _ = get_tanner_graph(active_mat)
        gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))
        model, n_v = get_compiled_model(G, params['BF_ITERS'])
        if use_saved_biases:
            bias_arr = np.load(get_bias_path(key=k))
            set_bias_arr(model, bias_arr)
        else:
            print(f'Train {k}')
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
        if match := re.match(r'stats_(.*)\(([0-9]*)_([0-9]*)\)\.json', p.name):
            key = match.group(1)
            llr_w = int(match.group(2))
            dec_p_bit = int(match.group(3))
            with p.open('rb') as infile:
                c_stats = json.load(infile)
            ret_dict[(f'{key}_C_({llr_w}_{dec_p_bit})', -1)] = \
                {'m': [{'BER': x['ber'], 'FER': x['fer']} for x in c_stats],
                 'p': [x['p'] for x in c_stats]}
    return ret_dict

def extract(stats, key, what, ident=False):
    key_lst = [x for x in stats.keys() if ((x[0] == key) if isinstance(key, str) else (x == key))]
    key_lst.sort(key=lambda x: x[1], reverse=True)
    key = key_lst[0]
    x_lst = stats[key]['p']
    y_lst = [x[what] for x in stats[key]['i' if ident else 'm']]
    return x_lst, y_lst


# %%
multiple_stats(np.geomspace(1e-1, 5e-5, 7), [('H_4_7', 60)], rerun_listed=True)

# %%
all_stats = multiple_stats(np.geomspace(1e-1, 5e-5, 7), ['H_32_44', ('H_4_7', 60), ('BCH_11_15', 40), 'BCH_16_31', 'BCH_21_31'])
list(all_stats.keys())

# %%
fig, ax = plt.subplots(nrows=2,ncols = 1, figsize=(9,11))
fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3) 
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
ax[0].loglog(*extract(all_stats, 'BCH_16_31', 'BER'), '-k', label='BCH(16, 31) Decoder')
ax[0].loglog(*extract(all_stats, 'BCH_16_31', 'BER', ident=True), '--k', label='BCH(16, 31) Identity', alpha=0.5)
ax[0].loglog(*extract(all_stats, 'BCH_11_15', 'BER'), '-r', label='BCH(11, 15) Decoder')
ax[0].loglog(*extract(all_stats, 'BCH_11_15', 'BER', ident=True), '--r', label='BCH(11, 15) Identity', alpha=0.5)
ax[0].set_xlabel('$E_b/N_0(dB)$')
ax[0].set_ylabel('BER ($P_b$)')
ax[0].set_title('BER for BCH codes')
ax[0].grid(True)
ax[0].legend()
ax[0].invert_xaxis()
ax[1].loglog(*extract(all_stats, 'BCH_16_31', 'FER'), '-k', label='BCH(16, 31) Decoder')
ax[1].loglog(*extract(all_stats, 'BCH_16_31', 'FER', ident=True), '--k', label='BCH(16, 31) Identity', alpha=0.5)
ax[1].loglog(*extract(all_stats, 'BCH_11_15', 'FER'), '-r', label='BCH(11, 15) Decoder')
ax[1].loglog(*extract(all_stats, 'BCH_11_15', 'FER', ident=True), '--r', label='BCH(11, 15) Identity', alpha=0.5)
ax[1].set_xlabel('$E_b/N_0(dB)$')
ax[1].set_ylabel('FER ($P_b$)')
ax[1].set_title('FER for BCH codes')
ax[1].grid(True)
ax[1].legend()
ax[1].invert_xaxis()

plt.savefig('images/BCH_python.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
fig, ax = plt.subplots(nrows=2,ncols = 1, figsize=(9,11))
fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3) 
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
ax[0].loglog(*extract(all_stats, 'H_32_44', 'BER'), '-b', label='LRRO(32, 44) Decoder')
ax[0].loglog(*extract(all_stats, 'H_32_44', 'BER', ident=True), '--b', label='LRRO(32, 44) Identity', alpha=0.5)
ax[0].loglog(*extract(all_stats, 'H_4_7', 'BER'), '-g', label='LRRO(4, 7) Decoder')
ax[0].loglog(*extract(all_stats, 'H_4_7', 'BER', ident=True), '--g', label='LRRO(4, 7) Identity', alpha=0.5)
ax[0].set_xlabel('$E_b/N_0(dB)$')
ax[0].set_ylabel('BER ($P_b$)')
ax[0].set_title('BER for LRRO codes')
ax[0].grid(True)
ax[0].legend()
ax[0].invert_xaxis()
ax[1].loglog(*extract(all_stats, 'H_32_44', 'FER'), '-b', label='LRRO(32, 44) Decoder')
ax[1].loglog(*extract(all_stats, 'H_32_44', 'FER', ident=True), '--b', label='LRRO(32, 44) Identity', alpha=0.5)
ax[1].loglog(*extract(all_stats, 'H_4_7', 'FER'), '-g', label='LRRO(4, 7) Decoder')
ax[1].loglog(*extract(all_stats, 'H_4_7', 'FER', ident=True), '--g', label='LRRO(4, 7) Identity', alpha=0.5)
ax[1].set_xlabel('$E_b/N_0(dB)$')
ax[1].set_ylabel('FER ($P_b$)')
ax[1].set_title('FER for LRRO codes')
ax[1].grid(True)
ax[1].legend()
ax[1].invert_xaxis()

plt.savefig('images/LRRO_python.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3) 
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')
ax.loglog(*extract(all_stats, 'H_32_44', 'BER', ident=True), '--k', label='Identity', alpha=1)
ax.loglog(*extract(all_stats, 'H_32_44', 'BER'), '-b', label='LRRO(32, 44) Decoder')
ax.loglog(*extract(all_stats, 'H_4_7', 'BER'), '-g', label='LRRO(4, 7) Decoder')
ax.loglog(*extract(all_stats, 'BCH_16_31', 'BER'), '-k', label='BCH(16, 31) Decoder')
ax.loglog(*extract(all_stats, 'BCH_21_31', 'BER'), '-y', label='BCH(16, 31) Decoder')
ax.loglog(*extract(all_stats, 'BCH_11_15', 'BER'), '-r', label='BCH(11, 15) Decoder')
ax.set_xlabel('$E_b/N_0(dB)$')
ax.set_ylabel('BER ($P_b$)')
ax.grid(True)
ax.legend()
ax.invert_xaxis()

plt.savefig('images/all_BER_python.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
# all_stats_2 = multiple_stats(np.geomspace(1e-1, 5e-5, 7), [('H_4_7', 100), ('BCH_11_15', 40)] )

# %%
c_stats = get_c_stats()
c_stats


# %%
merge_stats = all_stats | get_c_stats()
KEY_FILL = 'BCH_16_31'
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.loglog(*extract(merge_stats, KEY_FILL, 'BER', ident=True), '--b', label='Identity')
ax.loglog(*extract(merge_stats, KEY_FILL, 'BER'), '-b', label='Decoder')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(12_6)', 'BER'), '-g', label='C Decoder 12, 6')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(8_4)', 'BER'), '-r', label='C Decoder 8,4')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(8_3)', 'BER'), '-r', label='C Decoder 8,3')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(7_2)', 'BER'), '-r', label='C Decoder 8,3')
ax.set_xlabel('$p$')
ax.set_ylabel('BER')
ax.grid(which='minor', linestyle='--')
ax.grid(which='major', linestyle='-', linewidth=1.5)
ax.legend()
ax.invert_xaxis()

# %%
merge_stats = all_stats | get_c_stats()

fig, ax = plt.subplots(nrows=2,ncols = 1, figsize=(9,11))
fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.3) 
#ax.semilogy(X_theory, compute_ber(X_theory),'-',label='BPSK Theory')
#ax.semilogy(X_sim, [x[1]['BER'] for x in stat_list], 'X-b', label='BPSK Theory')

ax[0].loglog(*extract(all_stats, 'BCH_16_31', 'BER'), '-k', label='BCH(16, 31) Decoder')
ax[0].loglog(*extract(all_stats, 'BCH_16_31', 'BER', ident=True), '--k', label='BCH(16, 31) Identity', alpha=0.5)
ax[0].loglog(*extract(merge_stats, 'BCH_16_31_C_(10_4)', 'BER'), 's--', color='gray', label='BCH(16, 31) C Decoder')
ax[0].loglog(*extract(all_stats, 'BCH_21_31', 'BER'), '-r', label='BCH(11, 15) Decoder')
ax[0].loglog(*extract(all_stats, 'BCH_21_31', 'BER', ident=True), '--r', label='BCH(11, 15) Identity', alpha=0.5)
ax[0].loglog(*extract(merge_stats, 'BCH_21_31_C_(10_4)', 'BER'), 's--', color='pink', label='BCH(11, 15) C Decoder')
ax[0].set_xlabel('$E_b/N_0(dB)$')
ax[0].set_ylabel('BER ($P_b$)')
ax[0].set_title('BER for LRRO codes')

ax[1].loglog(*extract(all_stats, 'BCH_16_31', 'FER'), '-k', label='BCH(16, 31) Decoder')
ax[1].loglog(*extract(all_stats, 'BCH_16_31', 'FER', ident=True), '--k', label='BCH(16, 31) Identity', alpha=0.5)
ax[1].loglog(*extract(merge_stats, 'BCH_16_31_C_(10_4)', 'FER'), 's--', color='gray', label='BCH(16, 31) C Decoder')
# ax[1].loglog(*extract(all_stats, 'BCH_11_15', 'FER'), '-r', label='BCH(11, 15) Decoder')
# ax[1].loglog(*extract(all_stats, 'BCH_11_15', 'FER', ident=True), '--r', label='BCH(11, 15) Identity', alpha=0.5)
# ax[1].loglog(*extract(merge_stats, 'BCH_11_15_C_(10_4)', 'FER'), 's--', color='pink', label='BCH(11, 15) C Decoder')
ax[1].set_xlabel('$E_b/N_0(dB)$')
ax[1].set_ylabel('FER ($P_b$)')
ax[1].set_title('FER for LRRO codes')


for a in ax:
    a.grid(which='minor', linestyle='--')
    a.grid(which='major', linestyle='-', linewidth=1.5)
    a.legend()
    a.invert_xaxis()

# plt.savefig('images/LRRO_python.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
import matplotlib.cm as cm

# Generate some random data
merge_stats = all_stats | get_c_stats()
KEY_FILL = 'BCH_16_31'
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))

ax.loglog(*extract(merge_stats, KEY_FILL, 'BER', ident=True), '--k', label='Identity')
ax.loglog(*extract(merge_stats, KEY_FILL, 'BER'), '-k', label='Decoder')

secondary_lines = [(f'{KEY_FILL}_C_(12_6)', 'C Decoder 12, 6'), 
                   (f'{KEY_FILL}_C_(8_4)', 'C Decoder 8, 4'), 
                   (f'{KEY_FILL}_C_(8_3)', 'C Decoder 8, 3'),
                   (f'{KEY_FILL}_C_(7_2)', 'C Decoder 7, 2'),
                   (f'{KEY_FILL}_C_(6_1)', 'C Decoder 6, 1'),
                   (f'{KEY_FILL}_C_(5_0)', 'C Decoder 5, 0')
                  ]

# Define the colormap and normalize the range
cmap = cm.get_cmap('plasma')
norm = plt.Normalize(0, len(secondary_lines))

# Plot the secondary lines with varying colors from the colormap
for i in range(len(secondary_lines)):
    color = cmap(norm(i))
    ax.plot(*extract(merge_stats, secondary_lines[i][0], 'BER'), 's:', 
            color=color, alpha=0.7, label=secondary_lines[i][1], linewidth=2)
    
ax.set_xlabel('$p$')
ax.set_ylabel('BER')
ax.grid(which='minor', linestyle='--')
ax.grid(which='major', linestyle='-', linewidth=1.5)
ax.legend()
ax.invert_xaxis()

plt.savefig('images/C_stats.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
import matplotlib.cm as cm

# Generate some random data
merge_stats = all_stats | get_c_stats()
KEY_FILL = 'BCH_16_31'
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))

ax.loglog(*extract(merge_stats, KEY_FILL, 'FER', ident=True), '--k', label='Identity')
ax.loglog(*extract(merge_stats, KEY_FILL, 'FER'), '-k', label='Decoder')

secondary_lines = [(f'{KEY_FILL}_C_(12_6)', 'C Decoder 12, 6'), 
                   (f'{KEY_FILL}_C_(8_4)', 'C Decoder 8, 4'), 
                   (f'{KEY_FILL}_C_(8_3)', 'C Decoder 8, 3'),
                   (f'{KEY_FILL}_C_(7_2)', 'C Decoder 7, 2'),
                   (f'{KEY_FILL}_C_(6_1)', 'C Decoder 6, 1'),
                   (f'{KEY_FILL}_C_(5_0)', 'C Decoder 5, 0')
                  ]

# Define the colormap and normalize the range
cmap = cm.get_cmap('plasma')
norm = plt.Normalize(0, len(secondary_lines))

# Plot the secondary lines with varying colors from the colormap
for i in range(len(secondary_lines)):
    color = cmap(norm(i))
    ax.plot(*extract(merge_stats, secondary_lines[i][0], 'FER'), 's:', 
            color=color, alpha=0.7, label=secondary_lines[i][1], linewidth=2)
    
ax.set_xlabel('$p$')
ax.set_ylabel('FER')
ax.grid(which='minor', linestyle='--')
ax.grid(which='major', linestyle='-', linewidth=1.5)
ax.legend()
ax.invert_xaxis()

plt.savefig('images/C_stats.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%
KEY_FILL = 'BCH_16_31'
fig, ax = plt.subplots(nrows=1,ncols = 1, figsize=(10,7))
ax.loglog(*extract(merge_stats, KEY_FILL, 'FER', ident=True), '--b', label='Identity')
ax.loglog(*extract(merge_stats, KEY_FILL, 'FER'), '-b', label='Decoder')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(12_6)', 'FER'), '-g', label='C Decoder 12, 6')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(8_4)', 'FER'), '-r', label='C Decoder 8,4')
ax.loglog(*extract(merge_stats, f'{KEY_FILL}_C_(8_3)', 'FER'), '-r', label='C Decoder 8,3')
ax.set_xlabel('$p$')
ax.set_ylabel('FER')
ax.grid(which='minor', linestyle='--')
ax.grid(which='major', linestyle='-', linewidth=2)
ax.legend()
ax.invert_xaxis()


# %%
def int_gen_mapper(gen, params):
    for x, y in gen:
        x = tf.where(x > 0, params['DEFAULT_LLR'], -params['DEFAULT_LLR'])
        y = tf.where(y > 0, params['DEFAULT_LLR'], -params['DEFAULT_LLR'])
        yield x, y  
        
def get_int_stats(orig_model, int_pars, my_gen):
    
    temp_params = get_params(int_pars)
    temp_model, _ = get_compiled_model(G, temp_params['BF_ITERS'])
    my_gen = int_gen_mapper(my_gen, temp_params)
    
    bias_arr = get_bias_arr(orig_model)
    bias_arr_casted = convert_to_int(bias_arr, temp_params)
    set_bias_arr(temp_model, bias_arr_casted.astype('float32'))
    print(f"LLR for {int_pars}: {temp_params['DEFAULT_LLR']}")
    stats = temp_model.evaluate(
        x=my_gen,
        steps=500
    )
    return stats
    


# %%
# _gen_orig = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], zero_only=False)

def get_gen_dup(gen_limit = 10000):
    gen_orig = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], zero_only=False)
    gen_list = itertools.tee(gen_orig, gen_limit)
    for g in gen_list:
        yield g
gen_dup = get_gen_dup()

# %%
model.evaluate(
    x=next(gen_dup),
    steps=500
)

# %%
get_int_stats(model, {'DECIMAL_POINT_BIT':8, 'LLR_WIDTH': 16}, next(gen_dup))


# %%
def int_stats_gen(attempt_load=True):
    PATH = '../data/stats/py_int_stats.npy'
    @np.vectorize
    def my_function(x, y):
        if x >= y:
            return np.nan
        res = get_int_stats(model, {'DECIMAL_POINT_BIT':x, 'LLR_WIDTH': y}, next(gen_dup))[1]
        return (np.nan if np.allclose(res, 0) else res)
    # create a 2D grid of integer values
    max_dim = 12
    x = np.arange(0, max_dim)
    y = np.arange(1, max_dim + 1)
    X, Y = np.meshgrid(x, y)
    
    int_data = None
    if attempt_load:
        try:
            with open(PATH, 'rb') as infile:
                int_data = np.load(infile, allow_pickle=True)
        except OSError as e:
            pass
    
    if int_data is not None:
        if int_data.size != X.size:
            int_data = None
    
    if int_data is None:
        int_data = my_function(X, Y)
        with open(PATH, 'wb') as outfile:
            int_data.dump(outfile)
    return (x, y), int_data


# %%
int_stats = int_stats_gen()
int_stats

# %%
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
import matplotlib.colors as mcolors
import matplotlib as mpl
import numpy as np

(x, y), Z = int_stats

cmap = mpl.colormaps['plasma']
cmap.set_bad(color='grey')

# create the color map
fig, ax = plt.subplots(figsize=[7,7])
im = ax.imshow(Z, cmap=cmap)

# add a color bar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('BER', rotation=270, labelpad=20)

# set the axis labels
ax.set_xticks(np.arange(len(x)))
ax.set_yticks(np.arange(len(y)))
ax.set_xticklabels(x)
ax.set_yticklabels(y)
ax.set_xlabel('Decimal Point Placement (D)')
ax.set_ylabel('LLR Width (N)')
ax.invert_yaxis()
plt.savefig('images/int_gridplot.pdf', bbox_inches="tight")
# show the plot
plt.show()

# %%

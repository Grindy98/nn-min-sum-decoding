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
gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)

# %%
history = model.fit(
    x=gen,
    epochs=15,
    verbose="auto",
    callbacks=None,
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

# %% [markdown]
# ## Model Stats

# %%
def model_stats(eval_fun):
    def wrapper(probs):
        stat_list = []
        for p in probs:
            steps = max(int(1/p), 101)
            print(f'For {p}')
            eval_res = eval_fun(p, steps)
            stat_list.append((p, eval_res))
        return stat_list
    return wrapper


# %%
@model_stats
def BCH_model(p, steps):
    return model.evaluate(datagen_creator(gen_mat)(120, p, params['DEFAULT_LLR_F'], zero_only=False),
                          steps=steps, return_dict=True)

BCH_model(compute_ber(X_sim))

# %%

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

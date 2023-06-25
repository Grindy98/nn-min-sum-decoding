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
#     display_name: Python [conda env:nn]
#     language: python
#     name: conda-env-nn-py
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
import yaml
import tensorflow as tf
import scipy.io
import os

import numpy as np
import galois
import networkx as nx
from matplotlib import pyplot as plt

# %% [markdown]
# ## Helper Functions Imports

# %%
from utils import prob_to_llr, llr_to_prob, get_bias_arr, get_params, set_bias_arr, \
    generate_adj_matrix_data, get_gen_mat_dict, get_tanner_graph, convert_to_int, get_bias_path

from model import get_compiled_model, datagen_creator

# %% [markdown]
# ## Configurations
#
# **RERUN FROM HERE FOR CHANGES IN PARAMETERS**

# %%
gen_mat_dict = get_gen_mat_dict()
print(gen_mat_dict['BCH_4_7'], '\n')

print(gen_mat_dict['H_4_7'])

# %%
# Generator matrix

params = get_params()
active_mat = gen_mat_dict[params['MODEL_KEY']]
params

# %% [markdown]
# # Model training and testing
#

# %% [markdown]
# ## Tanner Graph

# %%
G, pos = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))

fig, ax = plt.subplots(figsize=[14, 14])
nx.draw_networkx(G, pos, ax=ax, node_size=800, font_size=14)
plt.show()

# %% [markdown]
# ## Model Compile and Fit
#
# **RERUN FROM HERE FOR MODEL REFRESH**

# %%
model, n_v = get_compiled_model(G, params['BF_ITERS'])
model.summary()

# %%
gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)

# %%
history = model.fit(
    x=gen,
    epochs=20,
    verbose="auto",
    callbacks=None,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    class_weight=None,
    sample_weight=None,
    initial_epoch=0,
    steps_per_epoch=300,
    validation_steps=None,
    validation_batch_size=None,
    validation_freq=1,
    max_queue_size=10,
    workers=1,
    use_multiprocessing=False,
)

# %%
model.evaluate(
    x=datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], zero_only=False),
    steps=100
)

# %%
bias_arr = get_bias_arr(model)

# %% [markdown]
# ## Bias Import 
# **SKIP IF MODEL TRAINING**

# %%
params = get_params()
if not os.path.exists(get_bias_path(params)):
    raise ValueError('No saved bias')
active_mat = gen_mat_dict[params['MODEL_KEY']]

G, _ = get_tanner_graph(active_mat)
gen_mat = galois.parity_check_to_generator_matrix(galois.GF2(active_mat))
model, n_v = get_compiled_model(G, params['BF_ITERS'])

bias_arr = np.load(get_bias_path(params))
set_bias_arr(model, bias_arr)

# %% [markdown]
# ## Bias Extraction and Integer Cast Evaluation

# %%
# Extract biases
bias_arr_casted = convert_to_int(bias_arr, params)
bias_arr_casted.dtype

# %%
# Test biases
int_model, n_v = get_compiled_model(G, params['BF_ITERS'])
set_bias_arr(int_model, bias_arr_casted.astype('float64'))

# %%
int_model.evaluate(
    x=datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR'], zero_only=False),
    steps=100 
)

# %%
# Test biases
model_no_w, n_v = get_compiled_model(G, params['BF_ITERS'])
set_bias_arr(int_model, np.zeros(bias_arr_casted.shape))

# %%
model_no_w.evaluate(
    x=datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR'], zero_only=False),
    steps=100 
)

# %% [markdown]
# # EXPORTS

# %% [markdown]
# ### METAPARAMETER WRITE

# %%
# Force params reloading
params = get_params()
print(params)

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
}
par_dict.update(params)
with open('../data/params.json', 'w') as jout:
    json.dump(par_dict, jout, indent=2)

# %% [markdown]
# ### FULL BIAS WRITE

# %%
# Save biases
if os.path.exists(get_bias_path(params)):
    raise ValueError('Cannot override biases implicitly')
np.save('../data/biases.npy', bias_arr_casted)
np.save(get_bias_path(params), bias_arr)

# %% [markdown]
# ### INT BIAS REFRESH

# %%
# Int biases refresh
bias_arr = np.load(get_bias_path(params))
bias_arr_casted = convert_to_int(bias_arr, params)

np.save('../data/biases.npy', bias_arr_casted)

# %% [markdown]
# # DEBUG / IMPORTS
#
# **ONLY RUN WITHOUT RUNNING THE EXPORTS SECTION**

# %%
bias_arr_casted = np.load('../data/biases.npy')
set_bias_arr(int_model, bias_arr_casted.astype('float64'))
int_model.evaluate(
    x=datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR'], zero_only=False),
    steps=100 
)

# %%
str_x = '110001011001011'
x = np.array([int(x) for x in list(str_x)]).reshape(1, len(str_x))
x = np.where(x, params['DEFAULT_LLR'], -params['DEFAULT_LLR'])
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

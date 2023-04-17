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
import itertools

import numpy as np
import galois
import networkx as nx
from matplotlib import pyplot as plt

# %% [markdown]
# ## Helper Functions Imports

# %%
from utils import prob_to_llr, llr_to_prob, get_bias_arr, get_params, set_bias_arr, \
    generate_adj_matrix_data, get_gen_mat_dict, get_tanner_graph, convert_to_int, int_gen_mapper

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

fig, ax = plt.subplots(figsize=[8, 12])
nx.draw_networkx(G, pos, ax=ax, node_size=300, font_size=9)
plt.show()

# %% [markdown]
# ## Model Compile and Fit
#
# **RERUN FROM HERE FOR MODEL REFRESH**

# %%
model, n_v = get_compiled_model(G, params['BF_ITERS'])
model.summary()

# %%
# tf.keras.utils.plot_model(model, show_shapes=True)

# %%
gen = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], forced_flips=1)

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
    steps_per_epoch=200,
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
def model_predict(model, inp_out_t, params, is_int=False):
    inp_x = inp_out_t
    inp_y = None
    if isinstance(inp_out_t, tuple):
        inp_x = inp_out_t[0]
        inp_y = inp_out_t[1]
    if inp_x.ndim == 1:
        inp_x = inp_x.reshape(1, -1)
    if is_int:
        inp = np.where(inp_x == 1, params['DEFAULT_LLR'], -params['DEFAULT_LLR'])
    else:
        inp = np.where(inp_x == 1, params['DEFAULT_LLR_F'], -params['DEFAULT_LLR_F'])
    inp_t = tf.convert_to_tensor(inp)
    outp = model.predict(inp_t)
    outp = np.where(outp > 0, 1, 0)
    if inp_y is not None:
        xored = np.where(np.logical_xor(outp, inp_y), 1, 0)
        return np.sum(xored, axis=-1), xored, outp
    return outp


# %% [markdown]
# ## Bias Extraction and Integer Cast Evaluation

# %%
gen_template = datagen_creator(gen_mat)(120, params['CROSS_P'], params['DEFAULT_LLR_F'], zero_only=False)
test_data = None
while not test_data or len(test_data[0]) < 10_000:
    new_data = next(gen_template)
    if not test_data:
        test_data = new_data
    else:
        test_data = (np.concatenate((test_data[0], new_data[0])), np.concatenate((test_data[1], new_data[1])))


# %%
convert_to_int(test_data[0], params)

# %%
bias_arr = get_bias_arr(model)
zero_model, _ = get_compiled_model(G, params['BF_ITERS'])
set_bias_arr(zero_model, np.zeros(bias_arr.shape))

bias_arr_casted = convert_to_int(bias_arr, params)
int_model, _ = get_compiled_model(G, params['BF_ITERS'])
set_bias_arr(int_model, bias_arr_casted.astype('float32'))


# %%
def test_int_models():
    def group_list(l, group_size):
        n = l.shape[1] / group_size
        return np.array_split(l, n, axis=1)
    np_data = np.stack(test_data)
#     np_data = np.transpose(np_data, (1, 0, 2))
    for i, d in enumerate(group_list(np_data, 200)):
        print(f'Iter {i}')
        if i == 50:
            break
        x = d[0, :]
        y = d[1, :]
        x = np.where(x > 0, 1, 0)
        y = np.where(y > 0, 1, 0)
        no_errs_1, xor_1, pred_1 = model_predict(model, (x, y), params, is_int=False)
        no_errs_2, xor_2, pred_2 = model_predict(int_model, (x, y), params, is_int=True)
        no_errs_3, xor_3, pred_3 = model_predict(zero_model, (x, y), params, is_int=False)
        no_errs_4, xor_4, pred_4 = model_predict(zero_model, (x, y), params, is_int=True)
        masked = np.transpose(np.stack([x, y, xor_1, xor_3, pred_1, pred_3]), (1, 0, 2))[no_errs_1 > no_errs_3]
        for tup in masked: 
            print(f'float err \n\t{tup[0]}\n\t{tup[1]} -> \n({np.sum(tup[2])}){tup[4]};\n({np.sum(tup[3])}){tup[5]}')
        masked = np.transpose(np.stack([x, y, xor_2, xor_4, pred_2, pred_4]), (1, 0, 2))[no_errs_2 > no_errs_4]
        for tup in masked: 
            print(f'int err \n\t{tup[0]}\n\t{tup[1]} -> \n({np.sum(tup[2])}){tup[4]};\n({np.sum(tup[3])}){tup[5]}')
#             print(f'float err {x} - {y} -> {pred_1}, {pred_3}')
#         if no_errs_2 > no_errs_4:
#             print(f'int err {x} - {y} -> {pred_2}, {pred_4}')


# %%
test_int_models()


# %%
def print_res(pred_tup):
    print(f'{pred_tup[0][0]} - \n\t{pred_tup[1][0]} \n\t{pred_tup[2][0]}')
tup = (
    np.fromstring('0 0 0 1 1 1 1 1 0 1 0 1 1 0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 1 1', dtype=int, sep=' '),
    np.fromstring('0 0 0 1 1 0 1 1 0 1 0 1 1 0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 1 1', dtype=int, sep=' ')
)
print_res(model_predict(model, tup, params, is_int=False))
print_res(model_predict(zero_model, tup, params, is_int=False))

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
}
par_dict.update(params)
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
set_bias_arr(int_model, bias_arr_casted.astype('float32'))
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

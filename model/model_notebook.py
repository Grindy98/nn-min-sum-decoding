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


# %%
def swap_form(matrix):
    rows = matrix.shape[0]
    return np.concatenate((matrix[:, rows:], matrix[:, :rows]), axis=1)


# %%
const_dict = scipy.io.loadmat('constants.mat')
H_test = np.array(const_dict['BCH_test'])
H_32_44 = np.array(const_dict['H_32_44'])
H_4_7 = np.array(const_dict['H_4_7'])

# %%
from utils import get_tanner_graph

G, pos = get_tanner_graph(H_32_44)

nx.draw_networkx(G, pos)

# %%
from keras.layers import Input
from keras.models import Model

from layers import OutputLayer

# %%
inp = Input(shape=(44,))
inp2 = Input(shape=(147,))
out = OutputLayer(G, 'i1')([inp, inp2])
model = Model([inp, inp2], out)

# %%
g = tf.random.Generator.from_seed(123)

model.predict([g.normal((1,44)), g.normal((1,147))])

# %%

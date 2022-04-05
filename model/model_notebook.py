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

G, pos = get_tanner_graph(H_4_7)

nx.draw_networkx(G, pos)

# %%
from keras.layers import Input
from keras.models import Model

from layers import OutputLayer

# %%
inp = Input(shape=(7,))
inp2 = Input(shape=(12,))
out = OutputLayer(G, 'i1')([inp, inp2])
model = Model([inp, inp2], out)

# %%
g = tf.random.Generator.from_seed(123)

model.predict([g.normal((1,7)), g.normal((1,12))])

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
model, n_v = create_model(G, 2)
model.summary()

# %%
tf.keras.utils.plot_model(model, show_shapes=True)

# %%
from utils import prob_to_llr, llr_to_prob
def loss_wrapper(n_v):
    def inner(y_true, y_pred):
        # Fix for None, None shape
        y_true = tf.reshape(y_true, [-1, n_v])
        y_pred = tf.reshape(y_pred, [-1, n_v])
        
        y_true = tf.where(y_true <= 0, 0.0, 1.0)
        y_pred = llr_to_prob(y_pred)
        N = y_true.shape[1]
        out = y_true * tf.math.log(y_pred)
        out += (1 - y_true) * tf.math.log(1 - y_pred)
        out = tf.math.reduce_sum(out, axis=1)
        out = -1/N * out
        return out
    return inner


# %%
from tensorflow.keras.optimizers import Adam
adam = Adam(learning_rate=0.001)


model.compile(
    optimizer=adam,
    loss=loss_wrapper(n_v)
)

# %%
import keras.backend as K 

def datagen(shape, p, data_limit=1000000, zero_only=True):
    neg_llr = prob_to_llr(p)
    pos_llr = -neg_llr
    for _ in range(data_limit):
        if zero_only:
            y = np.zeros(shape, dtype=bool)
        else:
            y = np.random.choice([False, True], size=shape)
        # This is the binary symmetric channel mask
        mask = np.random.choice([False, True], size=shape, p=[1-p, p])
        x = np.logical_xor(y, mask)
        x = np.where(x, pos_llr, neg_llr)
        y = np.where(y, pos_llr, neg_llr)
        x = x.astype('float32')
        y = y.astype('float32')
        yield x, y
        
        

# %%
gen = datagen([120, n_v], 0.05)
print(n_v)

model.fit(
    x=gen,
    epochs=5,
    verbose="auto",
    callbacks=None,
    validation_split=0.0,
    validation_data=None,
    shuffle=True,
    class_weight=None,
    sample_weight=None,
    initial_epoch=0,
    steps_per_epoch=1000,
    validation_steps=None,
    validation_batch_size=None,
    validation_freq=1,
    max_queue_size=10,
    workers=1,
    use_multiprocessing=False,
)

# %%
model.evaluate(
    x=datagen([120, n_v], 0.05, zero_only=True),
    steps=100 
)

# %%

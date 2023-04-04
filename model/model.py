import numpy as np
import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
import tensorflow.keras.backend as K 
import galois

from layers import OddLayerFirst, OddLayer, EvenLayer, OutputLayer
from metrics import BER, FER
import utils

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

def loss_wrapper(n_v, e_clip=1e-10):
    def inner(y_true, y_pred):
        # Fix for None, None shape
        y_true = tf.reshape(y_true, [-1, n_v])
        y_pred = tf.reshape(y_pred, [-1, n_v])
        
        y_true = tf.where(y_true <= 0, 0.0, 1.0)
        y_pred = utils.llr_to_prob(y_pred)
        N = y_true.shape[1]
        out = y_true * tf.math.log(tf.clip_by_value(y_pred, e_clip, 1.0))
        out += (1 - y_true) * tf.math.log(tf.clip_by_value(1 - y_pred, e_clip, 1.0))
        out = tf.math.reduce_sum(out, axis=1)
        out = -1/N * out
        return out
    return inner

def get_compiled_model(tanner_graph, iters = 1, other_options = {}):
    model, n_v = create_model(tanner_graph, iters)
    adam = Adam(learning_rate=0.1)
    comp_options = {
        'optimizer':adam,
        'loss':loss_wrapper(n_v),
        'metrics':[BER(), FER()]
    }
    comp_options.update(other_options)
    model.compile(**comp_options)
    return model, n_v

# Generator matrix for shape and creation of codewords
def datagen_creator(gen_matrix, data_limit=1000000):
    def datagen(batch_size, p, default_llr=None, zero_only=True, forced_flips=0):
        if default_llr is None:
            default_llr = -utils.prob_to_llr(p)
        
        for _ in range(data_limit):
            input_shape = (batch_size, gen_matrix.shape[0])
            if zero_only:
                y = galois.GF2(np.zeros(input_shape, dtype=int))
            else:
                y = galois.GF2(np.random.choice([0, 1], size=input_shape))

            # Transform dataword to codeword
            y = y @ gen_matrix

            # This is the binary symmetric channel mask
            mask = np.append(np.random.choice([0, 1], size=(y.shape[1]-forced_flips), p=[1-p, p]),
                                        np.ones(forced_flips, dtype=int))
            np.random.shuffle(mask)
            mask = galois.GF2(mask)
            x = y + mask

            # Transform from bool to llr
            x = np.where(x, default_llr, -default_llr).astype('float64')
            y = np.where(y, default_llr, -default_llr).astype('float64')

            yield x, y
    return datagen;

from keras.layers import Layer
import networkx as nx
import numpy as np
import tensorflow as tf

def _stdize(edge):
    # Make sure c nodes are always first
    if edge[0].startswith('v'):
        edge = edge[::-1]
    return edge

def _edge_sort(graph):
    # Sort edges (for consistency only)
    edge_lst = [_stdize(e) for e in graph.edges]
    edge_lst.sort(key= lambda x: (int(x[1][1:]), int(x[0][1:])))
    return {_stdize(e): i for i, e in enumerate(edge_lst)}

def _create_prev_layer_mask(graph, common_node):
    edge_idx = _edge_sort(graph)
    edge_n = len(graph.edges)
    
    # Build layer mask
    A = np.zeros((edge_n,edge_n))
    for edge, idx in edge_idx.items():
        # Common node edges
        other_edges = [edge_idx[_stdize(e)] for e 
                       in graph.edges(edge[1 if common_node == 'v' else 0])]
        other_edges.remove(idx)
        
        A[idx, other_edges] = 1
        
    return tf.convert_to_tensor(A, dtype='float32')

def _create_input_layer_mask(graph):
    edge_idx = _edge_sort(graph)
    edge_n = len(graph.edges)
    
    v_node_n = len([n for n in graph.nodes if n.startswith('v')])
    
    # Build layer mask
    B = np.zeros((v_node_n,edge_n))
    for edge, idx in edge_idx.items():
        # Get index of v node
        v_idx = int(edge[1][1:])
        # Mark it as 1
        B[v_idx, idx] = 1
        
    return tf.convert_to_tensor(B, dtype='float32')
        
def _create_final_layer_mask(graph):
    edge_idx = _edge_sort(graph)
    edge_n = len(graph.edges)
    v_n = len([n for n in graph.nodes if n.startswith('v')])
    
    # Build layer mask
    A = np.zeros((edge_n, v_n))
    for idx in range(v_n):
        node = f'v{idx}'
        # Common node edges
        selected_edges = [edge_idx[_stdize(e)] for e 
                       in graph.edges(node)]
        
        A[selected_edges, idx] = 1
        
    return tf.convert_to_tensor(A, dtype='float32')


class OddLayer(Layer):

    def __init__(self, tanner_graph: nx.Graph, name):
        super().__init__(name=name)
        
        self.prev_layer_mask = _create_prev_layer_mask(tanner_graph, 'v')
        self.input_layer_mask = _create_input_layer_mask(tanner_graph)
    
    def call(self, inputs):
        
        from_input = inputs[0] @ self.input_layer_mask
        from_prev = inputs[1] @ self.prev_layer_mask
        
        return from_input + from_prev


class OddLayerFirst(Layer):

    def __init__(self, tanner_graph: nx.Graph, name):
        super().__init__(name=name)
        
        self.input_layer_mask = _create_input_layer_mask(tanner_graph)
    
    def call(self, inputs):
        
        from_input = inputs @ self.input_layer_mask
        
        return from_input


class EvenLayer(Layer):

    def __init__(self, tanner_graph: nx.Graph, name):
        super().__init__(name=name)
        
        prev_mask = _create_prev_layer_mask(tanner_graph, 'c')
        self.inf_mask = tf.where(prev_mask == 0, np.inf, 0)
        neuron_n = len(prev_mask)
        self.bias = self.add_weight(
            shape=(1, neuron_n),
            
        )
    
    def call(self, inputs):
        
        # Repeat rows for each input neuron to form an array of square matrices
        expanded_in = tf.tile(tf.expand_dims(inputs, -2), 
                              [1, self.inf_mask.shape[0], 1])
        masked_prod = expanded_in + self.inf_mask
        # Multiply masked input row-wise to get sign
        signs = tf.sign(tf.math.reduce_prod(masked_prod, -1))

        abs_in = tf.abs(expanded_in)
        # Compute min row-wise with infinite mask
        mins = tf.reduce_min(abs_in + self.inf_mask, -1)

        # Add beta weight
        biased_mins = tf.maximum(mins - self.bias, 0)
        
        return signs * biased_mins


class OutputLayer(Layer):

    def __init__(self, tanner_graph: nx.Graph, name):
        super().__init__(name=name)
        
        self.final_layer_mask = _create_final_layer_mask(tanner_graph)
    
    def call(self, inputs):
        # Inputs from input layer are just passed through
        from_input = inputs[0]
        from_prev = inputs[1] @ self.final_layer_mask
        
        return from_input + from_prev
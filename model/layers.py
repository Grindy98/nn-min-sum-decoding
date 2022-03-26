
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
        
    

class OddLayer(Layer):

    def __init__(self, tanner_graph: nx.Graph, name):
        super().__init__(name=name)

        # Initialize constant structure of layer
        neuron_n = len(tanner_graph.edges)
        
        self.prev_layer_mask = _create_prev_layer_mask(tanner_graph, 'v')
        self.input_layer_mask = _create_input_layer_mask(tanner_graph)
    
    def call(self, inputs):
        
        from_input = inputs[0] @ self.input_layer_mask
        from_prev = inputs[1] @ self.prev_layer_mask
        
        return from_input + from_prev
    

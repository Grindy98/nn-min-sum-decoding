#ifndef LAYER
#define LAYER

#include "matrix.h"

typedef struct oddlayer_t{
    matrix_t* prev_layer_mask;
    matrix_t* input_mask;
} oddlayer_t;

typedef struct evenlayer_t{
    matrix_t* prev_layer_mask;
    matrix_t* biases;
} evenlayer_t;

typedef struct outputlayer_t{
    matrix_t* output_mask;
} outputlayer_t;

typedef struct model_t{
    matrix_t* input_mask;
    matrix_t* prev_odd_layer_mask;
    matrix_t* prev_even_layer_mask;
    matrix_t* biases;
    matrix_t* output_mask;
} model_t;

matrix_t* process_oddlayer(oddlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer);
matrix_t* process_evenlayer(evenlayer_t layer, matrix_t* from_prev_layer);
matrix_t* process_output(outputlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer);

matrix_t* process_model(model_t whole_model, matrix_t* inp_mat);

#endif
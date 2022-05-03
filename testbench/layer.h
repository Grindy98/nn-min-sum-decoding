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

matrix_t* process_oddlayer(oddlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer);

matrix_t* process_evenlayer(evenlayer_t layer, matrix_t* from_prev_layer);

#endif
#ifndef LAYER
#define LAYER

#include "matrix.h"

typedef struct oddlayer{
    matrix* prev_layer_mask;
    matrix* input_mask;
} oddlayer;

typedef struct evenlayer{
    matrix* prev_layer_mask;
    matrix* biases;
} evenlayer;

matrix* process_oddlayer(oddlayer layer, matrix* from_input, matrix* from_prev_layer);

matrix* process_evenlayer(evenlayer layer, matrix* from_prev_layer);

#endif
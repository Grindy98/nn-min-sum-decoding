#ifndef IMPORT_MATRIX_WRAPPER
#define IMPORT_MATRIX_WRAPPER
#include "matrix.h"

extern matrix_t* odd_prev_layer_mask_mat;
extern matrix_t* odd_inp_layer_mask_mat;
extern matrix_t* even_prev_layer_mask_mat;
extern matrix_t* output_mask_mat;
extern matrix_t* biases_mat;
extern matrix_t* generator_mat;
void init_adj_mats();
void free_adj_mats();
#endif

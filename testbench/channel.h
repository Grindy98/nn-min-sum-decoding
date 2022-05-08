#ifndef CHANNEL
#define CHANNEL

#include "matrix.h"

#define DEFAULT_LLR 3

matrix_t* generate_random_codeword(matrix_t* gen_mat);
matrix_t* channel_out_llr(matrix_t* codeword, float crossover_p);

#endif
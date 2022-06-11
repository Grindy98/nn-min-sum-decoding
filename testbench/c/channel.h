#ifndef CHANNEL
#define CHANNEL

#include "matrix.h"

#define DEFAULT_LLR 74

matrix_t* generate_random_codeword(matrix_t* gen_mat);
matrix_t* apply_channel(matrix_t* codeword, float crossover_p);
matrix_t* cast_to_llr(matrix_t* codeword);
matrix_t* cast_from_llr(matrix_t* codeword);
matrix_t* channel_out_llr(matrix_t* codeword, float crossover_p);

#endif
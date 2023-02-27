#ifndef CHANNEL
#define CHANNEL

#include "matrix.h"

extern const int DEFAULT_LLR;

matrix_t* generate_random_codeword(matrix_t* gen_mat);
matrix_t* apply_channel(matrix_t* codeword, float crossover_p);
matrix_t* apply_fixed_error(matrix_t* codeword, int n_errs);
matrix_t* cast_to_llr(matrix_t* codeword);
matrix_t* cast_from_llr(matrix_t* codeword);
matrix_t* channel_out_llr(matrix_t* codeword, float crossover_p);
matrix_t* fixed_error_out_llr(matrix_t* codeword, int n_errs);

#endif
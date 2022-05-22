#include "channel.h"
#include <stdio.h>
#include <stdlib.h>

matrix_t* generate_random_codeword(matrix_t* gen_mat){
    if(!gen_mat->is_mod_two){
        printf("Generator matrix has to be mod 2\n");
        exit(1);
    }
    // Generate exactly as many bits as expected by the input
    int64_t random_arr[gen_mat->row_size];
    for (int i = 0; i < gen_mat->row_size; i++)
    {
        random_arr[i] = rand() % 2;
    }
    matrix_t* new_inp = create_mat(random_arr, 1, gen_mat->row_size, 1);
    matrix_t* ret = mat_mul(new_inp, gen_mat);
    free_mat(&new_inp);
    return ret;
}

matrix_t* apply_channel(matrix_t* codeword, float crossover_p){
    if(!codeword->is_mod_two){
        printf("Codeword has to be mod 2\n");
        exit(1);
    }
    matrix_t* out = duplicate_mat(codeword, 1);
    for (int i = 0; i < out->col_size; i++)
    {
        float r = (float)rand() / ((float)RAND_MAX);
        if(r < crossover_p){
            // Invert bit
            int64_t elem = get_elem(out, 0, i);
            elem = 1 - elem;
            put_elem(out, 0, i, elem);
        }
    }
    return out;
}

matrix_t* cast_to_llr(matrix_t* codeword){
    if(!codeword->is_mod_two){
        printf("Codeword has to be mod 2\n");
        exit(1);
    }
    matrix_t* out = duplicate_mat(codeword, 0);
    for (int i = 0; i < out->col_size; i++)
    {
        int64_t elem = get_elem(out, 0, i);
        elem = elem ? DEFAULT_LLR : (-DEFAULT_LLR);
        put_elem(out, 0, i, elem);
    }
    return out;
}

matrix_t* cast_from_llr(matrix_t* llr){
    matrix_t* out = duplicate_mat(llr, 1);
    for (int i = 0; i < out->col_size; i++)
    {
        int64_t elem = get_elem(llr, 0, i);
        put_elem(out, 0, i, elem > 0 ? 1 : 0);
    }
    return out;
}

matrix_t* channel_out_llr(matrix_t* codeword, float crossover_p){
    matrix_t* output_cw = apply_channel(codeword, crossover_p);
    matrix_t* out = cast_to_llr(output_cw);
    free_mat(&output_cw);
    return out;
}
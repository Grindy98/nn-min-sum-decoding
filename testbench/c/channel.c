#include "channel.h"
#include "print.h"
#include <stdlib.h>

matrix_t* generate_random_codeword(matrix_t* gen_mat){
    if(!gen_mat->is_mod_two){
        custom_print('+', "Generator matrix has to be mod 2\n");
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
        custom_print('+', "Codeword has to be mod 2\n");
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

void shuffle(int *array, int n, int num_shuffles) {
    for (int j = 0; j < num_shuffles; j++) {
        for (int i = 0; i < n - 1; i++) {
            size_t j = i + rand() / (RAND_MAX / (n - i) + 1);
            int t = array[j];
            array[j] = array[i];
            array[i] = t;
        }
    }
}

matrix_t* apply_fixed_error(matrix_t* codeword, int n_errs){
    if(!codeword->is_mod_two){
        custom_print('+', "Codeword has to be mod 2\n");
        exit(1);
    }
    if(codeword->col_size < n_errs){
        custom_print('+', "Number of errors has to be smaller than size of cw\n");
        exit(1);
    }
    int ind_arr[codeword->col_size];
    for(int i = 0; i < codeword->col_size; i++){
        ind_arr[i] = i;
    }
    shuffle(ind_arr, codeword->col_size, 20);
    matrix_t* out = duplicate_mat(codeword, 1);
    for (int i = 0; i < n_errs; i++)
    {
        // Invert bit
        int64_t elem = get_elem(out, 0, ind_arr[i]);
        elem = 1 - elem;
        put_elem(out, 0, ind_arr[i], elem);
    }
    return out;
}

matrix_t* cast_to_llr(matrix_t* codeword){
    if(!codeword->is_mod_two){
        custom_print('+', "Codeword has to be mod 2\n");
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

matrix_t* fixed_error_out_llr(matrix_t* codeword, int n_errs){
    matrix_t* output_cw = apply_fixed_error(codeword, n_errs);
    matrix_t* out = cast_to_llr(output_cw);
    free_mat(&output_cw);
    return out;
}

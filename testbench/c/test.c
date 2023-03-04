#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>

#include "print.h"
#include "matrix.h"
#include "layer.h"
#include "channel.h"
#include "import_matrix_wrapper.h"

int custom_print ( const char * fmt, ... ){
    int ret;
    va_list args;
    va_start(args, fmt);
    ret = vprintf(fmt, args);
    va_end(args);
    return ret;
}

void test_full_layer(){
    matrix_t* inp_mat, *llr_mat, *out_mat;
    
    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;

    printf("\nMODEL TEST\n");

    int64_t inp_arr[] = {1,0,0,0,1,1,1};
    inp_mat = create_mat(inp_arr, 1, 7, 1);

    llr_mat = cast_to_llr(inp_mat);
    out_mat = process_model(model, llr_mat);

    display_mat(inp_mat);
    display_mat(llr_mat);
    display_mat(out_mat);

    free_mat(&inp_mat);
    free_mat(&llr_mat);
    free_mat(&out_mat);
}

int main(){
    // Seed for rng
    srand(time(0));

    init_adj_mats();
    
    matrix_t* inp_mat;
    matrix_t* prev_mat;
    matrix_t* inp_mat_mask;
    matrix_t* prev_mat_mask;
    matrix_t* bias_mat;
    {
        int64_t inp_arr[] = {1, 2, 3};
        int64_t prev_arr[] = {1, 2, 3, 4, 5};
        int64_t inp_arr_mask[] = {1 , 0, 0, 0, 0,
                                  1 , 1, 0, 0, 0,
                                  0 , 1, 1, 1, 1};

        int64_t prev_arr_mask[] = {1, 0, 0, 0, 0,
                                   1, 1, 0, 0, 0,
                                   0, 1, 1, 0, 1,
                                   0, 1, 0, 0, 1,
                                   0, 1, 0, 1, 0};
        int64_t bias_arr[] = {0, 1, -1, 0, 1};
        inp_mat = create_mat(inp_arr, 1, 3, 0);
        prev_mat = create_mat(prev_arr, 1, 5, 0);
        inp_mat_mask = create_mat(inp_arr_mask, 3, 5, 1);
        prev_mat_mask = create_mat(prev_arr_mask, 5, 5, 1);
        bias_mat = create_mat(bias_arr, 1, 5, 0);
    }


    printf("Channel tests\n");
    matrix_t* cw = generate_random_codeword(generator_mat);
    display_mat(cw);
    matrix_t* llr_cw = channel_out_llr(cw, 0.01);
    display_mat(llr_cw);
    matrix_t* llr_cw_fixed = fixed_error_out_llr(cw, 1);
    display_mat(llr_cw_fixed);

    printf("Layer test\n");
    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;

    int64_t in_arr[] = {5, 5, 5, 5, 5, 
                        5, 5, 5, 5, 5, 
                        5, 5, 5, 5, 5};
    matrix_t* in = create_mat(in_arr, 1, 15, 0); 

    matrix_t* out = process_model(model, llr_cw);
    display_mat(out);
    matrix_t* out_llr = cast_from_llr(out);
    display_mat(out_llr);

    test_full_layer();

    free_mat(&in);
    free_mat(&llr_cw);
    free_mat(&llr_cw_fixed);
    free_mat(&cw);
    free_mat(&out);
    free_mat(&out_llr);
    free_mat(&inp_mat);
    free_mat(&prev_mat);
    free_mat(&inp_mat_mask);
    free_mat(&prev_mat_mask);
    free_mat(&bias_mat);
    free_adj_mats();
    return 0;
}

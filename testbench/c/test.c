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

extern const double CROSS_P;
char def_print_type = 'c';

int custom_print (const char flag, const char * fmt, ... ){
    if(flag != def_print_type && flag != '+'){
        return 0;
    } 
    int ret;
    va_list args;
    va_start(args, fmt);
    ret = vprintf(fmt, args);
    va_end(args);
    return ret;
}

void test_full_layer(char inp_str[]){
    matrix_t* inp_mat, *llr_mat, *out_mat_llr, *out_mat;
    
    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;

    printf("\nMODEL TEST\n");
    int len = strlen(inp_str);
    int64_t inp_arr[len];
    for(int i = 0; i < len; i++){
        inp_arr[i] = inp_str[i] == '1' ? 1 : 0;
    }

    inp_mat = create_mat(inp_arr, 1, len, 1);

    llr_mat = cast_to_llr(inp_mat);
    out_mat_llr = process_model(model, llr_mat);
    out_mat = cast_from_llr(out_mat_llr);

    display_mat('=', inp_mat);
    display_mat('=', llr_mat);
    display_mat('=', out_mat);

    free_mat(&inp_mat);
    free_mat(&llr_mat);
    free_mat(&out_mat_llr);
    free_mat(&out_mat);
}

void misc_tests(){
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
    display_mat('+', cw);
    matrix_t* llr_cw = channel_out_llr(cw, 0.01);
    display_mat('+', llr_cw);
    matrix_t* llr_cw_fixed = fixed_error_out_llr(cw, 1);
    display_mat('+', llr_cw_fixed);

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
    display_mat('+', out);
    matrix_t* out_llr = cast_from_llr(out);
    display_mat('+', out_llr);

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
}

void get_stats(int n){
    def_print_type = '+';

    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;
    
    int total_bits = 0;
    int bit_errors = 0;
    int frame_errors = 0;
    for (int i = 0; i < n; i++){
        matrix_t* cw = generate_random_codeword(generator_mat);
        matrix_t* cw_noisy = channel_out_llr(cw, CROSS_P);
        matrix_t* res_llr = process_model(model, cw_noisy);
        matrix_t* res = cast_from_llr(res_llr);

        int frame_flag = 0;
        for(int j = 0; j < res->col_size; j++){
            // Iterate over all bits, if one is wrong then frame has error
            if(get_elem(res, 0, j) != get_elem(cw, 0, j)){
                frame_flag = 1;
                bit_errors++;
            }
        }
        if(frame_flag){
            frame_errors++;
        }
        total_bits += res->col_size;

        // display_mat('+', res);
        // display_mat('+', cw_noisy);
        // display_mat('+', cw);

        free_mat(&res);
        free_mat(&res_llr);
        free_mat(&cw_noisy);
        free_mat(&cw);
    }
    double ber = bit_errors;
    double fer = frame_errors;
    ber /= total_bits;
    fer /= n;

    printf("BER: %e\n", ber);
    printf("FER: %e\n", fer);
    
}

int main(int argc, char* argv[]){
    // Seed for rng
    srand(time(0));
    init_adj_mats();
    if(argc == 1){
        misc_tests();
    } else if(argc == 3 && strcmp(argv[1], "-d") == 0){
        // test_full_layer("110001011001011");
        test_full_layer(argv[2]);
    } else if(argc == 3 && strcmp(argv[1], "-m") == 0){
        int n = 0;
        sscanf(argv[2], "%d", &n);
        get_stats(n);
    }else{
        printf("Invalid arguments!\n");
        return 1;
    }

    free_adj_mats();
    return 0;
}

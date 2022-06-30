#include <svdpi.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>

#include "channel.h"
#include "layer.h"
#include "import_matrix_wrapper.h"


void before_start(){
    // Seed for rng
    srand(time(0));
    init_adj_mats();
}

void before_end(){
    free_adj_mats();
}

void c_print_wrapper(const char* str);

void logger(const char *fmt, ...) {
    char outstr[100];
    va_list args;
    va_start(args, fmt);
    vsnprintf(outstr, 100, fmt, args);
    va_end(args);
    c_print_wrapper(outstr);
}

int generate_noisy_cw(svOpenArrayHandle arrHandle, double crossover, int n_errors){
    matrix_t* initial = generate_random_codeword(generator_mat);
    if(initial->col_size != svSize(arrHandle, 1)){
        free_mat(&initial);
        return 1;
    }
    matrix_t* noisy;
    if(n_errors <= 0){
        noisy = apply_channel(initial, crossover);
    }else{
        noisy = apply_fixed_error(initial, n_errors);
    }
    matrix_t* casted_noisy = cast_to_llr(noisy);
    for(int i = svRight(arrHandle, 1); i <= svLeft(arrHandle, 1) ; i++){
        int* arrElem = (int*)svGetArrElemPtr1(arrHandle, i);
        *arrElem = (int)get_elem(casted_noisy, 0, i);
    }
    free_mat(&casted_noisy);
    free_mat(&noisy);
    free_mat(&initial);
    return 0;
}

void pass_through_model(svOpenArrayHandle inpArrHandle, svOpenArrayHandle outpArrHandle){
    int64_t store_input[generator_mat->col_size];
    for(int i = svRight(inpArrHandle, 1); i <= svLeft(inpArrHandle, 1) ; i++){
        int* arrElem = (int*)svGetArrElemPtr1(inpArrHandle, i);
        store_input[i] = *arrElem;
    }
    matrix_t* inp_mat = create_mat(store_input, 1, generator_mat->col_size, 0);

    // Create model
    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;

    matrix_t* out_mat = process_model(model, inp_mat);
    for(int i = svRight(outpArrHandle, 1); i <= svLeft(outpArrHandle, 1) ; i++){
        int64_t out_val = get_elem(out_mat, 0, i);
        svLogic* arrElem = (svLogic*)svGetArrElemPtr1(outpArrHandle, i);
        *arrElem = (out_val >= 0 ? 1 : 0); 
    }
    free_mat(&inp_mat);
    free_mat(&out_mat);
}
/*     
    for(int i = svRight(arrHandle, 1); i <= svLeft(arrHandle, 1) ; i++){
        //int* arrElem = (int*)svGetArrElemPtr1(arrHandle, i);
        int64_t arrElem = get_elem(noisy, 0, i); 
        svLogic val = (arrElem == 1 ? 1 : 0); 
        svPutLogicArrElem(arrHandle, val, i);
    }
*/
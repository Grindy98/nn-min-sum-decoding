#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>

#include "dpiheader.h"

#include "print.h"
#include "channel.h"
#include "layer.h"
#include "import_matrix_wrapper.h"


void before_start(){
    // Seed for rng
    srand(2132);
    init_adj_mats();
}

void before_end(){
    free_adj_mats();
}

int custom_print (const char flag, const char * fmt, ... ){
    if(flag != 'v' && flag != '+'){
        return 0;
    } 
    char outstr[100];
    int ret;
    va_list args;
    va_start(args, fmt);
    ret = vsnprintf(outstr, 100, fmt, args);
    va_end(args);
    //c_print_wrapper(outstr);
    printf("%s", outstr);
    return ret;
}

int generate_cw_init(svOpenArrayHandle arrHandle){
    matrix_t* initial = generate_random_codeword(generator_mat);
    
    if(initial->col_size != svSize(arrHandle, 1)){
        free_mat(&initial);
        custom_print('+', "ERROR: size not matched");
        return 1;
    }

    for(int i = svRight(arrHandle, 1); i <= svLeft(arrHandle, 1) ; i++){
        svLogic* arrElem = (svLogic*)svGetArrElemPtr1(arrHandle, i);
        *arrElem = get_elem(initial, 0, i);
    }

    free_mat(&initial);
    return 0;
}

int generate_cw_noisy_from_init(svOpenArrayHandle arrHandleOut, svOpenArrayHandle arrHandleIn, double crossover, int n_errors){
    if(svSize(arrHandleIn, 1) != svSize(arrHandleOut, 1)){
        custom_print('+', "ERROR: size not matched");
        return 1;
    }

    matrix_t* initial = create_mat(NULL, 1, svSize(arrHandleIn, 1), 1);
    for(int i = svRight(arrHandleIn, 1); i <= svLeft(arrHandleIn, 1) ; i++){
        svLogic* arrElem = (svLogic*)svGetArrElemPtr1(arrHandleIn, i);
        put_elem(initial, 0, i, (int)*arrElem);
    }
    
    matrix_t* noisy;
    if(n_errors <= 0){
        noisy = apply_channel(initial, crossover);
    }else{
        noisy = apply_fixed_error(initial, n_errors);
    }

    for(int i = svRight(arrHandleOut, 1); i <= svLeft(arrHandleOut, 1) ; i++){
        svLogic* arrElem = (svLogic*)svGetArrElemPtr1(arrHandleOut, i);
        *arrElem = get_elem(noisy, 0, i);
    }

    free_mat(&noisy);
    free_mat(&initial);
    return 0;
}

int cast_cw_to_llr(svOpenArrayHandle intArrHandleOut, svOpenArrayHandle arrHandleIn){
    if(svSize(arrHandleIn, 1) != svSize(intArrHandleOut, 1)){
        custom_print('+', "ERROR: size not matched");
        return 1;
    }

    matrix_t* initial = create_mat(NULL, 1, svSize(arrHandleIn, 1), 1);
    for(int i = svRight(arrHandleIn, 1); i <= svLeft(arrHandleIn, 1) ; i++){
        svLogic* arrElem = (svLogic*)svGetArrElemPtr1(arrHandleIn, i);
        put_elem(initial, 0, i, (int)*arrElem);
    }
    
    matrix_t* casted;
    casted = cast_to_llr(initial);

    for(int i = svRight(intArrHandleOut, 1); i <= svLeft(intArrHandleOut, 1) ; i++){
        int* arrElem = (int*)svGetArrElemPtr1(intArrHandleOut, i);
        *arrElem = (int)get_elem(casted, 0, i);
    }

    free_mat(&casted);
    free_mat(&initial);
    return 0;
}

int generate_noisy_llr_cw(svOpenArrayHandle arrHandle, double crossover, int n_errors){
    matrix_t* initial = generate_random_codeword(generator_mat);
    
    custom_print('+', "Initial CW:\t");
    
    display_mat('+', initial);
    
    if(initial->col_size != svSize(arrHandle, 1)){
        free_mat(&initial);
        custom_print('+', "ERROR: size not matched");
        return 1;
    }
    matrix_t* noisy;
    if(n_errors <= 0){
        noisy = apply_channel(initial, crossover);
    }else{
        noisy = apply_fixed_error(initial, n_errors);
    }

    custom_print('+', "Error CW:\t");
    display_mat('+', noisy);

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

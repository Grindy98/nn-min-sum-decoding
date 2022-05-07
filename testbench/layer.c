#include "layer.h"
#include <stdlib.h>
#include <stdio.h>

matrix_t* process_oddlayer(oddlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer){
    // Make sure inputs are row vectors
    if(from_input->row_size != 1 || from_prev_layer->row_size != 1){
        printf("Inputs have to be row vectors\n");
        exit(1);
    }
    matrix_t* masked_input = mat_mul(from_input, layer.input_mask);
    matrix_t* masked_prev = mat_mul(from_prev_layer, layer.prev_layer_mask);
    matrix_t* sum = mat_sum(masked_input, masked_prev);

    free_mat(&masked_input);
    free_mat(&masked_prev);
    return sum;
}

matrix_t* process_evenlayer(evenlayer_t layer, matrix_t* from_prev_layer){
    // Make sure input is a row vector
    if(from_prev_layer->row_size != 1){
        printf("Inputs have to be row vectors\n");
        exit(1);
    }
    
    // Generate sign vector
    matrix_t* signs = create_mat(NULL, 1, layer.prev_layer_mask->row_size, 0);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        cint_t curr_sign = {1};
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            if(mul(get_elem(layer.prev_layer_mask, i, j),
                get_elem(from_prev_layer, 0, j)).x < 0){
                curr_sign.x *= -1;
            }
        }
        put_elem(signs, 0, i, curr_sign);
    }

    // Generate minimum vector
    matrix_t* minimum = create_mat(NULL, 1, layer.prev_layer_mask->row_size, 0);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        cint_t curr_min = {CINT_MAX};
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            // Skip if not connected
            if(get_elem(layer.prev_layer_mask, i, j).x == 0){
                continue;
            }
            // Check abs value against minimum
            int x = abs(get_elem(from_prev_layer, 0, j).x);
            if(curr_min.x > x){
                curr_min.x = x;
            }

        }
        put_elem(minimum, 0, i, curr_min);
    }

    // Final matrix
    matrix_t* post_processing = mat_pointwise_mul(signs, minimum);
    matrix_t* final = mat_sum(post_processing, layer.biases);
    
    free_mat(&signs);
    free_mat(&minimum);
    free_mat(&post_processing);
    return final;
}
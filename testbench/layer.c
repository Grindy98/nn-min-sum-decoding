#include "layer.h"
#include <stdlib.h>
#include <stdio.h>
#include <limits.h>

matrix* process_oddlayer(oddlayer layer, matrix* from_input, matrix* from_prev_layer){
    // Make sure inputs are row vectors
    if(from_input->row_size != 1 || from_prev_layer->row_size != 1){
        printf("Inputs have to be row vectors\n");
        exit(1);
    }
    matrix* masked_input = mat_mul(from_input, layer.input_mask);
    matrix* masked_prev = mat_mul(from_prev_layer, layer.prev_layer_mask);
    matrix* sum = mat_sum(masked_input, masked_prev);

    free_mat(&masked_input);
    free_mat(&masked_prev);
    return sum;
}

matrix* process_evenlayer(evenlayer layer, matrix* from_prev_layer){
    // Make sure input is a row vector
    if(from_prev_layer->row_size != 1){
        printf("Inputs have to be row vectors\n");
        exit(1);
    }
    
    // Generate sign vector
    matrix* signs = create_mat(NULL, 1, layer.prev_layer_mask->row_size);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        int curr_sign = 1;
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            if(get_elem(layer.prev_layer_mask, i, j) 
                * get_elem(from_prev_layer, 0, j) < 0){
                curr_sign *= -1;
            }
        }
        put_elem(signs, 0, i, curr_sign);
    }

    // Generate minimum vector
    matrix* minimum = create_mat(NULL, 1, layer.prev_layer_mask->row_size);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        int curr_min = INT_MAX;
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            // Skip if not connected
            if(get_elem(layer.prev_layer_mask, i, j) == 0){
                continue;
            }
            // Check abs value against minimum
            int x = abs(get_elem(from_prev_layer, 0, j));
            if(curr_min > x){
                curr_min = x;
            }

        }
        put_elem(minimum, 0, i, curr_min);
    }

    // Final matrix
    matrix* post_processing = mat_pointwise_mul(signs, minimum);
    matrix* final = mat_sum(post_processing, layer.biases);
    
    free_mat(&signs);
    free_mat(&minimum);
    free_mat(&post_processing);
    return final;
}
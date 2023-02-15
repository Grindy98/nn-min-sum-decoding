#include "layer.h"
#include <stdlib.h>
#include "print.h"

matrix_t* process_oddlayer(oddlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer){
    // Make sure inputs are row vectors
    if(from_input->row_size != 1 || from_prev_layer->row_size != 1){
        custom_print("Inputs have to be row vectors\n");
        exit(1);
    }
    matrix_t* masked_input = mat_mul(from_input, layer.input_mask);
    matrix_t* masked_prev = mat_mul(from_prev_layer, layer.prev_layer_mask);
    matrix_t* sum = mat_sum(masked_input, masked_prev);
    mat_apply_saturation(sum);

    free_mat(&masked_input);
    free_mat(&masked_prev);
    return sum;
}

matrix_t* process_evenlayer(evenlayer_t layer, matrix_t* from_prev_layer){
    // Make sure input is a row vector
    if(from_prev_layer->row_size != 1){
        custom_print("Inputs have to be row vectors\n");
        exit(1);
    }
    
    // Generate sign vector
    matrix_t* signs = create_mat(NULL, 1, layer.prev_layer_mask->row_size, 0);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        int64_t curr_sign = 1;
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            if(get_elem(layer.prev_layer_mask, i, j) * 
                get_elem(from_prev_layer, 0, j) < 0){
                curr_sign *= -1;
            }
        }
        put_elem(signs, 0, i, curr_sign);
    }

    // Generate minimum vector
    matrix_t* minimum = create_mat(NULL, 1, layer.prev_layer_mask->row_size, 0);
    for (int i = 0; i < layer.prev_layer_mask->row_size; i++)
    {
        int64_t curr_min = INT64_MAX;
        
        for (int j = 0; j < layer.prev_layer_mask->col_size; j++)
        {
            // Skip if not connected
            if(get_elem(layer.prev_layer_mask, i, j) == 0){
                continue;
            }
            // Check abs value against minimum
            int64_t x = abs(get_elem(from_prev_layer, 0, j));
            if(curr_min > x){
                curr_min = x;
            }

        }
        put_elem(minimum, 0, i, curr_min);
    }

    // Final matrix
    matrix_t* post_processing = mat_pointwise_mul(signs, minimum);
    matrix_t* final = mat_sum(post_processing, layer.biases);
    mat_apply_saturation(final);
    
    free_mat(&signs);
    free_mat(&minimum);
    free_mat(&post_processing);
    return final;
}

matrix_t* process_output(outputlayer_t layer, matrix_t* from_input, matrix_t* from_prev_layer){
    // Make sure inputs are row vectors
    if(from_input->row_size != 1 || from_prev_layer->row_size != 1){
        custom_print("Inputs have to be row vectors\n");
        exit(1);
    }
    matrix_t* masked_prev = mat_mul(from_prev_layer, layer.output_mask);
    matrix_t* sum = mat_sum(from_input, masked_prev);
    mat_apply_saturation(sum);

    free_mat(&masked_prev);
    return sum;
}

matrix_t* process_model(model_t whole_model, matrix_t* inp_mat){
    // Deduce number of iters from size of biases
    int iters = whole_model.biases->row_size;

    // Create odd and output layers, since they are static
    oddlayer_t o_l = {whole_model.prev_odd_layer_mask, whole_model.input_mask};
    outputlayer_t op_l = {whole_model.output_mask};

    // Handle first odd layer separately
    matrix_t* dummy_mat = create_mat(NULL, 1, o_l.prev_layer_mask->row_size, 0);
    matrix_t* out_mat = process_oddlayer(o_l, inp_mat, dummy_mat);
    free_mat(&dummy_mat);

    for (int i = 0; i <= iters - 1; i++)
    {
        matrix_t* curr_bias = mat_extract(whole_model.biases, i, -1);
        evenlayer_t e_l = {whole_model.prev_even_layer_mask, curr_bias};
        matrix_t* interm_mat = process_evenlayer(e_l, out_mat);
        free_mat(&out_mat);

        if(i == iters - 1){
            // Handle last output layer
            out_mat = process_output(op_l, inp_mat, interm_mat);
        }else{
            // Pass thrugh another odd layer
            out_mat = process_oddlayer(o_l, inp_mat, interm_mat);
        }
        free_mat(&interm_mat);
        free_mat(&curr_bias);
    }
    
    return out_mat;
}
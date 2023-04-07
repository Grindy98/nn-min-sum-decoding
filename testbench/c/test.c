#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <pthread.h>
#include <errno.h>

#include "print.h"
#include "matrix.h"
#include "layer.h"
#include "channel.h"
#include "import_matrix_wrapper.h"

extern const double CROSS_P;
extern const char MODEL_KEY[];
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
struct thread_inp{
    int min_iters;
    int min_errors;
    double p;
    int t_bits;
    int t_frames;
    int e_bits;
    int e_frames;
};
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
void * threaded_prob(void* inputs){
    struct thread_inp* inp = (struct thread_inp*) inputs;

    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;
    
    pthread_mutex_lock(&mutex);
    double p = inp->p;
    int min_iters = inp->min_iters;
    int min_errors = inp->min_errors;
    pthread_mutex_unlock(&mutex);

    while (1){
        pthread_mutex_lock(&mutex);
        if(!(inp->e_bits < min_errors || inp->t_frames < min_iters)){
            pthread_mutex_unlock(&mutex);
            break;
        }
        pthread_mutex_unlock(&mutex);

        matrix_t* cw = generate_random_codeword(generator_mat);
        matrix_t* cw_noisy = channel_out_llr(cw, p);
        matrix_t* res_llr = process_model(model, cw_noisy);
        matrix_t* res = cast_from_llr(res_llr);

        int bit_errors = 0;
        for(int j = 0; j < res->col_size; j++){
            // Iterate over all bits, if one is wrong then frame has error
            if(get_elem(res, 0, j) != get_elem(cw, 0, j)){
                bit_errors++;
            }
        }
        pthread_mutex_lock(&mutex);
        if(bit_errors > 0){
            inp->e_frames++;
        }
        inp->e_bits += bit_errors;
        inp->t_bits += res->col_size;
        inp->t_frames++;
        if(inp->t_frames % 10000 == 0){
            printf("Frames - errs: %8d - %2d\n", inp->t_frames, inp->e_bits);
        }
        pthread_mutex_unlock(&mutex);

        free_mat(&res);
        free_mat(&res_llr);
        free_mat(&cw_noisy);
        free_mat(&cw);
    }
    return NULL;
}

void get_stats_prob(int n_errors, int min_iters, double p, double stats[2]){
    model_t model;
    model.biases = biases_mat;
    model.input_mask = odd_inp_layer_mask_mat;
    model.output_mask = output_mask_mat;
    model.prev_even_layer_mask = even_prev_layer_mask_mat;
    model.prev_odd_layer_mask = odd_prev_layer_mask_mat;
    
    int total_bits = 0;
    int total_frames = 0;
    int bit_errors = 0;
    int frame_errors = 0;
    while (bit_errors < n_errors || total_frames < min_iters){
        if(total_frames % 10000 == 0 && total_frames != 0){
            printf("Frames processed: %7d\n", total_frames);
        }
        matrix_t* cw = generate_random_codeword(generator_mat);
        matrix_t* cw_noisy = channel_out_llr(cw, p);
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
        total_frames++;

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
    fer /= total_frames;

    // printf("BER: %e\n", ber);
    // printf("FER: %e\n", fer);
    
    stats[0] = ber;
    stats[1] = fer;
}

void export_model_stats(){
    def_print_type = '+';

    double upper = 0.1, lower = 5e-5;
    int n = 8;
    double factor = pow(lower / upper, 1.0 / (n - 1));

    for(int i = 0; i < n; i++){
        double p = upper * pow(factor, (double)i);
        double stats[2];
        get_stats_prob(11, 101, p, stats);

        printf("For %.2e: BER: %e, ", p, stats[0]);
        printf("FER: %e\n", stats[1]);
    }

}

void export_model_stats_threaded(const char* dir_path){
    def_print_type = '+';

    double upper = 0.1, lower = 5e-5;
    int n = 8;
    int n_thr = 4;
    double factor = pow(lower / upper, 1.0 / (n - 1));


    const int MAX_BUF = 10000;
    char* whole_text = malloc(sizeof(char) * MAX_BUF);
    if(whole_text == NULL){
        printf("Error allocating space");
        exit(1);
    }
    int length = 0;
    length += snprintf(whole_text+length, MAX_BUF-length, "[\n");

    for(int i = 0; i < n; i++){
        double p = upper * pow(factor, (double)i);
        struct thread_inp inp;
        inp.e_bits = 0;
        inp.e_frames = 0;
        inp.t_bits = 0;
        inp.t_frames = 0;
        inp.p = p;
        inp.min_errors = 11;
        inp.min_iters = 101;

        pthread_t thr_arr[n_thr];
        for(int i_thr = 0; i_thr < n_thr; i_thr++){
            pthread_create(&thr_arr[i_thr], NULL, threaded_prob, &inp);
        }
        for(int i_thr = 0; i_thr < n_thr; i_thr++){
            pthread_join(thr_arr[i_thr], NULL);
        }
        double ber = ((double)inp.e_bits) / inp.t_bits;
        double fer = ((double)inp.e_frames) / inp.t_frames;

        printf("For %.2e: BER: %e, ", p, ber);
        printf("FER: %e\n", fer);

        // Write in JSON list format
        char comma = (i == n - 1 ? ' ' : ','); 
        length += snprintf(whole_text+length, MAX_BUF-length, 
            "\t{\"p\":%.10lf, \"ber\":%.10lf, \"fer\":%.10lf}%c\n", p, ber, fer, comma);
    }
    
    length += snprintf(whole_text+length, MAX_BUF-length, "]\n");

    // Open file in data dir and dump the data
    char line_buf[100];
    snprintf(line_buf, 100, "%s/stats_%s.json", dir_path, MODEL_KEY);
    FILE* fout = fopen(line_buf, "w");

    if(fout == NULL){
        printf("File open error: %s\n", strerror(errno));
        exit(1);
    }

    fprintf(fout, "%s", whole_text);
    fclose(fout);
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
    } else if(argc >= 2 && strcmp(argv[1], "-m") == 0){
        if(argc == 2){
            export_model_stats();
        }else{
            export_model_stats_threaded(argv[2]);
        }
    }else{
        printf("Invalid arguments!\n");
        return 1;
    }

    free_adj_mats();
    return 0;
}

#include "tanner_graph.h"
#include <stdlib.h>


tgraph_t* create_tgraph(){
    
}

matrix_t* gen_prev_layer_mask_mat(tgraph_t* graph){

    matrix_t* mask = create_mat(NULL, graph->edge_n, graph->edge_n);
    
}

void free_tgraph(tgraph_t** t_ptr){
    free((*t_ptr)->edge_arr);
    *t_ptr = NULL;
}
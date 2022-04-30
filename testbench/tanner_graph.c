#include "tanner_graph.h"
#include <stdlib.h>


tgraph* create_tgraph(){
    
}

matrix* gen_prev_layer_mask_mat(tgraph* graph){

    matrix* mask = create_mat(NULL, graph->edge_n, graph->edge_n);
    
}

void free_tgraph(tgraph** t_ptr){
    free((*t_ptr)->edge_arr);
    *t_ptr = NULL;
}
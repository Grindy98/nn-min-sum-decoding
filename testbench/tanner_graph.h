#ifndef TANNER_GRAPH
#define TANNER_GRAPH
#include "matrix.h"

typedef struct edge_t{
    int v_index;
    int c_index;
} edge_t;

typedef struct tgraph_t{
    int edge_n;
    int n_v;
    int n_c;
    edge_t* edge_arr;
} tgraph_t;

tgraph_t* create_tanner_graph(int* h_matrix, int cols, int rows);

void free_tanner_graph(tgraph_t** t_ptr);

#endif

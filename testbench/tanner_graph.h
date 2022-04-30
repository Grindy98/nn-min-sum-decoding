#ifndef TANNER_GRAPH
#define TANNER_GRAPH
#include "matrix.h"

typedef struct edge{
    int v_index;
    int c_index;
} edge;

typedef struct tgraph{
    int edge_n;
    int n_v;
    int n_c;
    edge* edge_arr;
} tgraph;

tgraph* create_tanner_graph(int* h_matrix, int cols, int rows);

void free_tanner_graph(tgraph** t_ptr);

#endif

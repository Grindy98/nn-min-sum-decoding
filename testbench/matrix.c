#include "matrix.h"
#include <stdlib.h>
#include <stdio.h>

// Initialize with arr or with 0 if no arr
matrix* create_mat(int* arr, int rows, int cols){
    int* new_arr = malloc(rows * cols * sizeof(int));
    if(new_arr == NULL){
        exit(1);
    }
    matrix* ret = malloc(sizeof(matrix));
    if(ret == NULL){
        exit(1);
    }
    if (arr){
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                new_arr[i * cols + j] = arr[i * cols + j];
            }
            
        }
    }else{
        for (int i = 0; i < rows; i++)
        {
            for (int j = 0; j < cols; j++)
            {
                new_arr[i * cols + j] = 0;
            }
            
        }
    }
    ret->mat = new_arr;
    ret->col_size = cols;
    ret->row_size = rows;
    return ret;
}

matrix* duplicate_mat(matrix* mat){
    return create_mat(mat->mat, mat->row_size, mat->row_size);
}

int check_range(matrix* mat, int row, int col){
    return row >= 0 && row < mat->row_size &&
        col >= 0 && col < mat->col_size;
}

int get_elem(matrix* mat, int row, int col){
    if(!check_range(mat, row, col)){
        printf("Invalid range for elem\n");
        exit(1);
    } 
    return mat->mat[row * mat->col_size + col];
}

void put_elem(matrix* mat, int row, int col, int elem){
    if(!check_range(mat, row, col)){
        printf("Invalid range for elem\n");
        exit(1);
    } 
    mat->mat[row * mat->col_size + col] = elem;
}

matrix* mat_mul(matrix* A, matrix* B){
    if(A->col_size != B->row_size){
        printf("Matrices must have same inner rank\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = B->col_size;
    matrix* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            int sum = 0;
            for (int k = 0; k < A->col_size; k++)
            {
                sum += get_elem(A, i, k) * get_elem(B, k, j);
            }
            
            put_elem(new_mat, i, j, sum); 
        }
        
    }
    return new_mat;
    
}

matrix* mat_sum(matrix* A, matrix* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        printf("Matrices must have same ranks\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            put_elem(new_mat, i, j, get_elem(A, i, j) + get_elem(B, i, j));
        }
        
    }
    return new_mat;
    
}

matrix* mat_pointwise_mul(matrix* A, matrix* B){
    if(A->row_size != B->row_size || A->col_size != B->col_size){
        printf("Matrices must have same ranks\n");
        exit(1);
    }
    int new_row = A->row_size;
    int new_col = A->col_size;
    matrix* new_mat = create_mat(NULL, new_row, new_col);
    for (int i = 0; i < new_row; i++)
    {
        for (int j = 0; j < new_col; j++)
        {
            put_elem(new_mat, i, j, get_elem(A, i, j) * get_elem(B, i, j));
        }
        
    }
    return new_mat;
    
}

void display_mat(matrix* mat){
    for (int i = 0; i < mat->row_size; i++)
    {
        printf(" ");
        for (int j = 0; j < mat->col_size; j++)
        {
            printf("%d ", get_elem(mat, i, j));
        }
        printf("\n");
    }
}

void free_mat(matrix** m_ptr){
    free((*m_ptr)->mat);
    free(*m_ptr);
    *m_ptr = 0;
}
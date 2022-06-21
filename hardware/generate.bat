@echo off
setlocal
cd /d %~dp0

call conda activate py_new
call python verilog_gen.py -i ..\data\adj_matrices.npz -var_o variable_nodes -check_o check_nodes
call conda deactivate

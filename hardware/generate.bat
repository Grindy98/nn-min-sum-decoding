@echo off
setlocal
cd /d %~dp0

call python verilog_gen.py -i ..\data\adj_matrices.npz -var_o variable_nodes -check_o check_nodes -out_o out_layer

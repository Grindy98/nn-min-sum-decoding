set decoder_dir "D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding/hardware"
set testbench_dir "D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding/testbench/sv"
set all_files [concat [glob -d $decoder_dir *.v *.vh] [glob -d $testbench_dir *.v *.sv] ]


# Recompile dpi lib
source ccompile.tcl

# Generate v files
#exec start "" "${decoder_dir}/generate.bat"

exec ${decoder_dir}/generate.bat

remove_files [get_files]
add_files {*}$all_files
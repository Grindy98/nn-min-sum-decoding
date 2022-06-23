set decoder_dir "D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding/hardware"
set testbench_dir "D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding/testbench/sv"
set all_files [concat [glob -d $decoder_dir *.v *.vh] [glob -d $testbench_dir *.v *.sv] ]
set proj_path [get_property DIRECTORY [current_project]]

# Set current project properties
set_property INCREMENTAL false [get_filesets sim_1]
set prop_value_list [list -sv_root ${proj_path}/xsim.dir/work/xsc -sv_lib dpi]
set_property -name {xsim.elaborate.xelab.more_options} -value $prop_value_list -objects [get_filesets sim_1]
set_property -name {xsim.elaborate.load_glbl} -value {false} -objects [get_filesets sim_1]
set_property -name {xsim.simulate.runtime} -value {0ns} -objects [get_filesets sim_1]
set_property top tb [get_filesets sim_1]

# Recompile dpi lib
source ${proj_path}/ccompile.tcl

# Generate v files
#exec start "" "${decoder_dir}/generate.bat"

exec ${decoder_dir}/generate.bat

remove_files [get_files]
add_files {*}$all_files
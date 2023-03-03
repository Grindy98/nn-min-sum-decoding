# CONSTANT
set GIT_REPO_PATH D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding

proc ref {} {
	global GIT_REPO_PATH
	
	# Generate c import_matrix file
	puts [exec ${GIT_REPO_PATH}/testbench/sim/globalgen.bat]

}

proc comp {} {
	global GIT_REPO_PATH
	puts "---------------COMPILE-------------------"
	vlog -sv -ccflags \"-std=c99\" -f ${GIT_REPO_PATH}/testbench/sim/simfiles.f
}

proc simulate {} {
	set orig_dir [pwd]
		
	set proj_name [get_property NAME [current_project]]
	set proj_path [get_property DIRECTORY [current_project]]
	try {
		set xvlog_args [list [get_files -compile_order sources -used_in simulation -filter {FILE_TYPE == VERILOG}] -svlog [get_files -compile_order sources -used_in simulation -filter {FILE_TYPE == SYSTEMVERILOG}]]
		if { [current_sim -quiet] != "" } {
			close_sim
		}
		cd ${proj_path}/build
		puts [exec xvlog {*}${xvlog_args}] 
		puts [exec xelab work.tb -sv_lib dpi -sv_root ./xsim.dir/work/xsc -debug typical]
		#puts [exec xsim work.tb]
	} finally {
		cd ${orig_dir}
	}
}

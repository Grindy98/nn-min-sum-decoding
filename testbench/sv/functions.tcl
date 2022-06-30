# CONSTANT
set GIT_REPO_PATH D:/Projects/Matlab/NN_BP_BCH/nn-min-sum-decoding




proc try {script args} {
    upvar 1 try___msg msg try___opts opts
    if {[llength $args]!=0 && [llength $args]!=2} {
       return -code error "wrong \# args: should be \"try script ?finally script?\""
    }
    if {[llength $args] == 2} {
       if {[lindex $args 0] ne "finally"} {
          return -code error "mis-spelt \"finally\" keyword"
       }
    }
    set code [uplevel 1 [list catch $script try___msg try___opts]]
    if {[llength $args] == 2} {
       uplevel 1 [lindex $args 1]
    }
    if {$code} {
       dict incr opts -level 1
       return -options $opts $msg
    }
    return $msg
 }
proc refresh {} {
	set orig_dir [pwd]
	global GIT_REPO_PATH
	set src_dir ${GIT_REPO_PATH}/testbench/c
	set decoder_dir ${GIT_REPO_PATH}/hardware
	set testbench_dir ${GIT_REPO_PATH}/testbench/sv 
	
	set proj_name [get_property NAME [current_project]]
	set proj_path [get_property DIRECTORY [current_project]]
	try {
		# Generate c import_matrix file
		exec ${src_dir}/generate.bat
		
		cd ${proj_path}

		puts "--------------------C COMPILE---------------------"
		if {[glob -nocomplain -d $src_dir *.c] != ""} {
			puts "Compiling C files"
			if {[catch {exec xsc {*}[glob -d $src_dir *.c] } errmsg]} {
			   puts "ErrorMsg: $errmsg"
			}
		}
		puts "-------------------------DONE------------------------"
		


		exec ${decoder_dir}/generate.bat
		
		set all_files [concat [glob -d $decoder_dir *.v *.vh] [glob -d $testbench_dir *.v *.sv] ]

		remove_files [get_files]
		puts [add_files {*}$all_files]
		move_files -fileset [current_fileset -simset] [get_files tb.sv]
		
		# Set current project properties
		set prop_value_list [list -sv_root ${proj_path}/xsim.dir/work/xsc -sv_lib dpi]
		set_property -name {xsim.elaborate.xelab.more_options} -value $prop_value_list -objects [get_filesets sim_1]
		set_property -name {xsim.simulate.runtime} -value {0ns} -objects [get_filesets sim_1]
		set_property top decoder_top [current_fileset]
		set_property top tb [get_filesets sim_1]
	
	} finally {
		cd ${orig_dir}
	}
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

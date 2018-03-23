#!/usr/bin/env python
"""Run Roux sampling workflow represented by Jennifer's scripts and tpr files"""

import os
import sys
sys.path.append('/home/mei2n/sample_restraint/build/src/pythonmodule')

import gmx

import logging
logging.getLogger().setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logging.getLogger().addHandler(ch)
logger = logging.getLogger()

import myplugin

logger.info("myplugin is {}".format(myplugin.__file__))

if len(sys.argv) > 1:
    size = int(sys.argv[1])
else:
    size = 20
input_dir_list = ['aa_{:02d}'.format(i) for i in range(size)]
print("Input directory list: {}".format(input_dir_list))

tpr_list = [os.path.abspath(os.path.join(directory, 'mRMR.tpr')) for directory in input_dir_list]

# dt = 0.002
# First restratint applied between atoms 387 and 2569
# Second restraint applied between atom 1330 and 2520
# Restraint site coordinates relative to atom 1735
# Relevant MDP parameters
# k = 100
# pull-nstxout = pull-nstfout = 1000
# window size = 5000
# total number of windows gathered: 23. 

# positional parameters
#    site1
#    site2
#    /// Width of bins (distance) in histogram
#    size_t nbins{0};
#    /// Histogram boundaries.
#    double min_dist{0};
#    double max_dist{0};
#    PairHist experimental{};
#
#    /// Number of samples to store during each window.
#    unsigned int nsamples{0};
#    double sample_period{0};
#
#    /// Number of windows to use for smoothing histogram updates.
#    unsigned int nwindows{0};
#    double window_update_period{0};
#
#    /// Harmonic force coefficient
#    double K{0};
#    /// Smoothing factor: width of Gaussian interpolation for histogram
#    double sigma{0};

params = {
	'sites': [387, 1735, 2569],
	'k': 100.,
	'sigma': 0.2,
	'nbins': 70,
	'binwidth': 0.1,
	'max_dist': 7.0,
	'min_dist': 0.0,
	'experimental': [1.799741371805743e-21, 1.394386099050501e-19, 8.502972718446353e-18, 4.085581973134053e-16, 1.548764419813057e-14, 4.638792711370235e-13, 1.0996581066864261e-11, 2.0673577567003664e-10, 3.0896196375481035e-09, 3.680765701683053e-08, 3.5071251461730994e-07, 2.683161946307409e-06, 1.6559233749685584e-05, 8.289071953350906e-05, 0.00033870482482321125, 0.0011381605345541928, 0.0031720369601255603, 0.007403098031042665, 0.014627984136430199, 0.024781412546281113, 0.036538520471987135, 0.04776926450937005, 0.056703917249967935, 0.06290983130284482, 0.06723680313442071, 0.07080726976949929, 0.07402160052652465, 0.0765402296381977, 0.07828089499810763, 0.08047585508402359, 0.08570745927698609, 0.09674399700081715, 0.11510583738691207, 0.14051216332953817, 0.17140325711911122, 0.20554101371952832, 0.23970384865306096, 0.2690817283268939, 0.2883208679737597, 0.2947929622276882, 0.2912919631495654, 0.28445334990710786, 0.27916526960634136, 0.2740440567694397, 0.2627885645671059, 0.24084583312911054, 0.2119920710658402, 0.18961266641719554, 0.19160148241368294, 0.23183520488057596, 0.31258390292452404, 0.4212625964074282, 0.5329315503397933, 0.6177862653849041, 0.6510130306580447, 0.621354685844679, 0.5350130330039692, 0.4131558700737114, 0.28383821525616004, 0.17174126508493523, 0.0904869618596048, 0.04102083542122555, 0.0158113507543527, 0.00512381828028717, 0.0013817258262933331, 0.00030725601604590235, 5.5898129564429734e-05, 8.270145724798172e-06, 1.066958972950409e-06, 8.525674649177577e-07],
	'nsamples': 50,
	#'sample_period': 1000*0.002,
	'sample_period': 100*0.002,
	'nwindows': 20,
	'window_update_period': 5000*0.002 
	}

potential = gmx.workflow.WorkElement(
	namespace="myplugin",
	operation="ensemble_restraint",
	depends=[],
	params=params
	)
potential.name = "ensemble_restraint_1"

md = gmx.workflow.from_tpr(tpr_list, tmpi=20, grid=[3, 3, 2], ntomp_pme=1, npme=2, ntomp=1)
#md = gmx.workflow.from_tpr(tpr_list, tmpi=2, grid=[3, 3, 2], ntomp_pme=1, npme=1, ntomp=1)
md.add_dependency(potential)

context = gmx.context.ParallelArrayContext(md)

with context as session:
	session.run()


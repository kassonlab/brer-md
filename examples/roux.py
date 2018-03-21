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
	'sites': [387, 2569],
	'k': 100.,
	'sigma': 0.2,
	'nbins': 70,
	'binwidth': 0.1,
	'max_dist': 7.0,
	'min_dist': 0.0,
	'experimental': [0.05]*70,
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


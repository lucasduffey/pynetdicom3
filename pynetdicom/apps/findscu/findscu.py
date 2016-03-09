#!/usr/bin/env python

"""
    A dcmtk style findscu application. 
    
    Used for 
"""

import argparse
import logging
import os
import socket
import sys
import time

from pydicom.dataset import Dataset

from pynetdicom.ae import AE
from pynetdicom.SOPclass import PatientRootFindSOPClass
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian, \
    ExplicitVRBigEndian

logger = logging.Logger('findscu')
stream_logger = logging.StreamHandler()
formatter = logging.Formatter('%(levelname).1s: %(message)s')
stream_logger.setFormatter(formatter)
logger.addHandler(stream_logger)
logger.setLevel(logging.ERROR)

def _setup_argparser():
    # Description
    parser = argparse.ArgumentParser(
        description="The findscu application implements a Service Class User "
                    "(SCU) for the Query/Retrieve (QR) Service Class and the "
                    "Basic Worklist Management (BWM) Service Class. findscu "
                    "only supports query functionality using the C-FIND "
                    "message. It sends query keys to an SCP and waits for a "
                    "response. The application can be used to test SCPs of the "
                    "QR and BWM Service Classes.",
        usage="findscu [options] peer port")
        
    # Parameters
    req_opts = parser.add_argument_group('Parameters')
    req_opts.add_argument("peer", help="hostname of DICOM peer", type=str)
    req_opts.add_argument("port", help="TCP/IP port number of peer", type=int)
    req_opts.add_argument("dcmfile_in", 
                          metavar="dcmfile-in",
                          help="DICOM query file(s)", 
                          type=str)

    # General Options
    gen_opts = parser.add_argument_group('General Options')
    gen_opts.add_argument("--version", 
                          help="print version information and exit", 
                          action="store_true")
    gen_opts.add_argument("--arguments", 
                          help="print expanded command line arguments", 
                          action="store_true")
    gen_opts.add_argument("-q", "--quiet", 
                          help="quiet mode, print no warnings and errors", 
                          action="store_true")
    gen_opts.add_argument("-v", "--verbose", 
                          help="verbose mode, print processing details", 
                          action="store_true")
    gen_opts.add_argument("-d", "--debug", 
                          help="debug mode, print debug information", 
                          action="store_true")
    gen_opts.add_argument("-ll", "--log-level", metavar='[l]', 
                          help="use level l for the logger (fatal, error, warn, "
                               "info, debug, trace)", 
                          type=str, 
                          choices=['fatal', 'error', 'warn', 
                                   'info', 'debug', 'trace'])
    gen_opts.add_argument("-lc", "--log-config", metavar='[f]', 
                          help="use config file f for the logger", 
                          type=str)
    
    # Network Options
    net_opts = parser.add_argument_group('Network Options')
    net_opts.add_argument("-aet", "--calling-aet", metavar='[a]etitle', 
                          help="set my calling AE title (default: FINDSCU)", 
                          type=str, 
                          default='FINDSCU')
    net_opts.add_argument("-aec", "--called-aet", metavar='[a]etitle', 
                          help="set called AE title of peer (default: ANY-SCP)", 
                          type=str, 
                          default='ANY-SCP')
    
    # Query information model choices
    qr_group = parser.add_argument_group('Query Information Model Options')
    qr_model = qr_group.add_mutually_exclusive_group()
    qr_model.add_argument("-W", "--worklist",
                          help="use modality worklist information model",
                          action="store_true")
    qr_model.add_argument("-P", "--patient",
                          help="use patient root information model",
                          action="store_true")
    qr_model.add_argument("-S", "--study",
                          help="use study root information model",
                          action="store_true")
    qr_model.add_argument("-O", "--psonly",
                          help="use patient/study only information model",
                          action="store_true")

    return parser.parse_args()

args = _setup_argparser()

if args.verbose:
    logger.setLevel(logging.INFO)
    pynetdicom_logger = logging.getLogger('pynetdicom')
    pynetdicom_logger.setLevel(logging.INFO)
    
if args.debug:
    logger.setLevel(logging.DEBUG)
    pynetdicom_logger = logging.getLogger('pynetdicom')
    pynetdicom_logger.setLevel(logging.DEBUG)

logger.debug('$findscu.py v%s %s $' %('0.1.0', '2016-02-15'))
logger.debug('')


# Create application entity
# Binding to port 0 lets the OS pick an available port
ae = AE(ae_title=args.calling_aet, 
        port=0, 
        scu_sop_class=[PatientRootFindSOPClass], 
        scp_sop_class=[], 
        transfer_syntax=[ExplicitVRLittleEndian])

# Request association with remote
assoc = ae.associate(args.peer, args.port, args.called_aet)

# Create query dataset
d = Dataset()
d.PatientsName = '*'
d.QueryRetrieveLevel = "PATIENT"

if args.worklist:
    query_model = 'W'
elif args.patient:
    query_model = 'P'
elif args.study:
    query_model = 'S'
elif args.psonly:
    query_model = 'O'
else:
    query_model = 'W'

# Send query
if assoc.Established:
    response = assoc.send_c_find(d, query_model)
    
    time.sleep(1)
    for value in response:
        pass
    
    assoc.Release()

ae.quit()

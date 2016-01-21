"""
This software is Copyright by the
 Board of Trustees of Michigan
 State University (c) Copyright 2015.
"""
from __future__ import print_function
import google.protobuf as protobuf
from carchive.backend import EPICSEvent_pb2 as pbt
from carchive.backend.pb import escape as pb_escape
from carchive.backend.pb import dtypes as pb_dtypes
import os, errno

DELIMITER = '\x1B'

class EmptyFileError(Exception):
    pass

class VerificationError(Exception):
    pass

def verify_stream(stream, pb_type=None, pv_name=None, year=None, upper_ts_bound=None):
    # Prepare line iterator.
    line_iterator = pb_escape.iter_lines(stream)
    
    # Check if we have a header.
    try:
        header_data = line_iterator.next()
    except pb_escape.IterationError as e:
        raise VerificationError('Reading header: {0}'.format(e))
    except StopIteration:
        raise EmptyFileError()
    
    # Parse header.
    header_pb = pbt.PayloadInfo()
    try:
        header_pb.ParseFromString(header_data)
    except protobuf.message.DecodeError as e:
        raise VerificationError('Failed to decode header: {0}'.format(e))
    
    # Sanity checks.
    if pb_type != None and header_pb.type != pb_type:
        raise VerificationError('Type mismatch in header.')
    if pv_name != None and header_pb.pvname != pv_name:
        raise VerificationError('PV name mismatch in header. Probably two PVs are bound to the same destination file. Check the used delimiters.')
    if year != None and header_pb.year != year:
        raise VerificationError('Year mismatch in header.')
    
    # Find PB class for this data type.
    pb_class = pb_dtypes.get_pb_class_for_type(header_pb.type)
    
    # Will be returning the last timestamp (if any).
    last_timestamp = None
    
    pos = find_position(stream)
            
    stream.seek(pos,os.SEEK_SET)
    line_iterator = pb_escape.iter_lines(stream)
    
    try:
        for sample_data in line_iterator:
            # Parse sample.
            sample_pb = pb_class()
            try:
                sample_pb.ParseFromString(sample_data)
            except protobuf.message.DecodeError as e:
                raise VerificationError('Failed to decode sample: {0}'.format(e))
            
            # Sanity check timestamp.
            sample_timestamp = (sample_pb.secondsintoyear, sample_pb.nano)
            if upper_ts_bound is not None:
                if sample_timestamp > upper_ts_bound:
                    raise VerificationError('Found newer sample')
            
            last_timestamp = sample_timestamp
        
    except pb_escape.IterationError as e:
        raise VerificationError('Reading samples: {0}'.format(e))
    
    return {
        'last_timestamp': last_timestamp,
        'year': header_pb.year,
    }

# Find the position which is the beginning of nearly the last sample in the file
def find_position(stream):
    stream.seek(0, os.SEEK_END)
    linecount = 0
    n = 3
    bsize = 2048
    
    while linecount <= n + 1:
        # read at least n lines + 1 more; we need to skip a partial line later on
        try:
            stream.seek(-bsize, os.SEEK_CUR)           # go backwards
            linecount += stream.read(bsize).count(DELIMITER) # count newlines
            stream.seek(-bsize, os.SEEK_CUR)           # go back again
        except IOError, e:
            if e.errno == errno.EINVAL:
                # Attempted to seek past the start, can't go further
                bsize = stream.tell()
                stream.seek(0, os.SEEK_SET)
                linecount += stream.read(bsize).count(DELIMITER)
                break
            raise  # Some other I/O exception, re-raise
    stream.readline() # move to the beginning of a line 
    pos = stream.tell()  
    return pos;
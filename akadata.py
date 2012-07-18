#!/usr/bin/env python

"""
akadata.py implements EdgeScape support in Python
Created from AkaData.pm by Ken Reeves ( joodahr@gmail.com )

Requires Python 2.6

Sample Usage:
    
Command Line: 
$ ./akadata.py -e facilitator.myhost.net -p 2001 123.123.123.123
city=BEIJING
domain=baidu.com
region_code=BJ
network=chinaunicom
company=China_Unicom_Beijing_province_network
long=116.41
bw=1
throughput=low
country_code=CN
lat=39.90
timezone=GMT+8
continent=AS
asnum=4808

Module:
from akadata import AkaData

edge_host = AkaData( host = facilitator.myhost.net, port = 2001 )

result = edge_host.ipLookup( '123.123.123.123' )
    
The result is a dictionary of all returned fields.

"""

import struct, socket, select, re

AKAMAI_OK            	 = 0
AKAMAI_DEFAULT       	 = 1
AKAMAI_GENERIC_ERROR 	 = 2
AKAMAI_SMALL_BUFFER  	 = 3
AKAMAI_TRY_AGAIN     	 = 4
AKAMAI_PERMISSION_DENIED = 5
AKAMAI_NOT_FOUND     	 = 6
AKAMAI_GO_AWAY       	 = 7
AKAMAI_LATEST        	 = 8

# default response packet when Edgescape server is unreachable
DEFAULT_ANSWER = { 'default_answer': 'T', 'country_code': 'US', 'default_source': 'client', }

RESPONSE_BUFFER_SIZE = 1024
RESPONSE_HEADER_OFFSET = 12

class AkaData( object ):

    def __init__( self, host = '127.0.0.1', port = 2001 ):

        self.host = host
        self.port = port
        self.result = tuple()

    def ipLookup( self, ip_address, timeout = 10 ):

        self.result = tuple()

        conn = socket.socket( socket.AF_INET, socket.SOCK_DGRAM, )

        if not conn:
            raise Exception( 1, 'Socket creation failed.' )

        conn.setblocking(0)

        ip_address_long = struct.unpack( '!L', socket.inet_aton( ip_address ) )[0]

        packet = struct.pack( '>BBHHBBL', 1, 0, 0, RESPONSE_BUFFER_SIZE, 0, 0, ip_address_long )

        send_result = conn.sendto( packet, 0, ( self.host, self.port, ) )

        if not send_result:
            raise Exception( 2, 'Data transmission failed.' )

        select_result = select.select( [ conn, ], tuple(), tuple(), float( timeout ) )

        if not conn in select_result[0]:
            raise Exception( 3, 'Data retrieval failed.' )

        recv_data, recv_address = conn.recvfrom( RESPONSE_BUFFER_SIZE, 0 )

        if not recv_data:
            raise Exception( 4, 'No data returned.' )

        try:
            ( header_version, header_flags, header_q, header_size, header_error, header_reserved, header_ip_address ) = struct.unpack( '>BBHHBBL', recv_data[:RESPONSE_HEADER_OFFSET] )
        except:
            raise Exception( 5, 'Could not unpack result header.' )
        
        if not header_version == 1:
            raise Exception( 6, 'Response was of an unexpected version.' )

        if not header_flags == 0:
            raise Exception( 7, 'Response contained unexpected flags.' )

        if not header_size == len( recv_data ):
            raise Exception( 8, 'Response was an unexpected length.' )

        if not header_error == AKAMAI_OK and not header_error == AKAMAI_DEFAULT:
            raise Exception( 9, 'Response retruned an error.', header_error )

        if socket.inet_ntoa( struct.pack( '!L', header_ip_address ) ) != ip_address:
            raise Exception( 10, 'Could not verify data.' )

        data = re.split( '\x00', recv_data[RESPONSE_HEADER_OFFSET:] )

        if not len( data ):
            raise Exception( 11, 'Retruned dataset was empty.' )

        values = {}

        for item in data:
            if len( item ):
                key, value = item.split( '=', 1 )
                values[ key ] = value

        return values

if __name__ == '__main__':
    import sys
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option( "-t", "--timeout", type = 'int', dest='requested_timeout', metavar = 'TIMEOUT', default = 10 )
    parser.add_option( "-e", "--edgescape-host", dest='requested_host', metavar = 'HOST', default = '127.0.0.1' )
    parser.add_option( "-p", "--port", dest='requested_port', metavar = 'PORT', default = 2001 )
    ( options, args ) = parser.parse_args()

    if len( args ) < 1:
        print 'Missing required ip address argument.'
        sys.exit(1)

    ip_address = args[0]

    edge_host = AkaData( host = options.requested_host, port = options.requested_port )

    result = edge_host.ipLookup( ip_address )
    
    for key, value in result.items():
        print '{}={}'.format( key, value )

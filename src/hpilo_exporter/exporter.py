#!/usr/bin/python3

"""
Pulls data from specified iLO and presents as Prometheus metrics
"""

from __future__ import absolute_import # Must be at the beginning of this file!
from __future__ import print_function  # Must be at the beginning of this file!

from os import getenv # for ilo_password

from _socket import gaierror

import sys
import hpilo

import time
import hpilo_exporter.prometheus_metrics as prometheus_metrics # Python3
# prometeus_metrics is a file with the metrics definitions

#from BaseHTTPServer import BaseHTTPRequestHandler
#from BaseHTTPServer import HTTPServer
from  http.server import BaseHTTPRequestHandler # Python3
from  http.server import HTTPServer             # Python3

# from SocketServer import ForkingMixIn
from socketserver import ForkingMixIn           # Python 3
from prometheus_client import generate_latest, Summary

# from urlparse import parse_qs
# from urlparse import urlparse
from urllib.parse import parse_qs               # Python3
from urllib.parse import urlparse               # Python3




def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary(
    'request_processing_seconds', 'Time spent processing request')


class ForkingHTTPServer(ForkingMixIn, HTTPServer):

    max_children = 30
    timeout = 30


class RequestHandler(BaseHTTPRequestHandler):
    """
    Endpoint handler
    """
    def return_error(self):
        self.send_response(500)
        self.end_headers()

    def do_GET(self):
        """
        Process GET request

        :return: Response with Prometheus metrics
        """
        # this will be used to return the total amount of time the request took
        start_time = time.time()
        # get parameters from the URL
        url = urlparse(self.path)
        # following boolean will be passed to True if an error is detected during the argument parsing
        error_detected = False
        query_components = parse_qs(urlparse(self.path).query)

        ilo_host = None
        ilo_port = None
        ilo_user = None
        ilo_password = None
        try:
            ilo_host = query_components['ilo_host'][0]
            ilo_port = int(query_components['ilo_port'][0])
            ilo_user = query_components['ilo_user'][0]
            # ilo_password = query_components['ilo_password'][0]
            ilo_password = getenv('ILO', 'ILO environment variable missing')
        # except KeyError, e:   valid only in Python2
        except KeyError as e:   # Python3
            print_err("missing parameter %s" % e)
            self.return_error()
            error_detected = True

        if url.path == self.server.endpoint and ilo_host and ilo_user and ilo_password and ilo_port:

            ilo = None
            try:
                ilo = hpilo.Ilo(hostname=ilo_host,
                                login=ilo_user,
                                password=ilo_password,
                                port=ilo_port, timeout=10)
            except hpilo.IloLoginFailed:
                print("ILO login failed")
                self.return_error()
            except gaierror:
                print("ILO invalid address or port")
                self.return_error()
            # except hpilo.IloCommunicationError, e:  # Python2
            except hpilo.IloCommunicationError as e:  # Python3

                print(e)

            # get product and server name
            try:
                product_name = ilo.get_product_name()
            except:
                product_name = "Unknown HP Server"

            try:
                server_name = ilo.get_server_name()
                if server_name == "":
                    server_name = ilo_host
            except:
                server_name = ilo_host

            # get iLO health information 
            embedded_health = ilo.get_embedded_health()
            # print_err('STRUCTURE: {}'.format(embedded_health))
            
            health_at_glance = embedded_health['health_at_a_glance'] 
            if health_at_glance is not None:
                for key, value in health_at_glance.items():
                    for status in value.items():
                        if status[0] == 'status':
                            gauge = 'hpilo_{}_gauge'.format(key)
                            if status[1].upper() == 'OK':
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,
                                                                        server_name=server_name).set(0)
                            elif status[1].upper() == 'DEGRADED':
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,
                                                                        server_name=server_name).set(1)
                            else:
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,
                                                                        server_name=server_name).set(2)
            #for iLO3 patch network
            if ilo.get_fw_version()["management_processor"] == 'iLO3':
                print_err('Unknown iLO nic status')
            else:
                # get nic information
                for nic_name,nic in embedded_health['nic_information'].items():
                   # print_err('nic: {}'.format(nic))
                   try:
                       value = ['OK','Disabled','Unknown','Link Down'].index(nic['status']) # returns the index of 'status' like 0 or 1     0 means OK
                       # print_err( "nic status: {}".format(nic['status']) )  # returns OK and Unknown
 
                   except ValueError:
                       value = 4
                       print_err('unrecognised nic status: {}'.format(nic['status']))

                   # print_err('ip_address of %s: {}'.format(nic['ip_address']) % nic_name ) 
                   prometheus_metrics.hpilo_nic_status_gauge.labels(product_name=product_name,
                                                                    server_name=server_name,
                                                                    nic_name=nic_name,
                                                                    mac_address=nic['mac_address'],
                                                                    ip_address=nic['ip_address'],
                                                                    network_port=nic['network_port']).set(value)

            # get firmware version
            fw_version = ilo.get_fw_version()["firmware_version"]
            management_processor = ilo.get_fw_version()["management_processor"]
            license_type = ilo.get_fw_version()["license_type"]
            # prometheus_metrics.hpilo_firmware_version.set(fw_version)
            prometheus_metrics.hpilo_firmware_version.labels(product_name=product_name,
                                                             server_name=server_name,
                                                             management_processor=management_processor,
                                                             license_type=license_type).set(fw_version)
            # ip = ilo.get_network_settings()['ip_address']
            # print_err( "ip: {}".format(ip) ) 


            # get the amount of time the request took
            REQUEST_TIME.observe(time.time() - start_time)

            # generate and publish metrics
            metrics = generate_latest(prometheus_metrics.registry)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics)

        elif url.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write("""<html>
            <head><title>HP iLO Exporter</title></head>
            <body>
            <h1>HP iLO Exporter</h1>
            <p>Visit <a href="/metrics">Metrics</a> to use.</p>
            </body>
            </html>""")

        else:
            if not error_detected:
                self.send_response(404)
                self.end_headers()


class ILOExporterServer(object):
    """
    Basic server implementation that exposes metrics to Prometheus
    """

    def __init__(self, address='0.0.0.0', port=8080, endpoint="/metrics"):
        self._address = address
        self._port = port
        self.endpoint = endpoint

    def print_info(self):
        print_err("Starting exporter on: http://{}:{}{}".format(self._address, self._port, self.endpoint))
        print_err("Press Ctrl+C to quit")

    def run(self):
        self.print_info()

        server = ForkingHTTPServer((self._address, self._port), RequestHandler)
        server.endpoint = self.endpoint

        try:
            while True:
                server.handle_request()
        except KeyboardInterrupt:
            print_err("Killing exporter")
            server.server_close()

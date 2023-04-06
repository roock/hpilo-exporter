#!/usr/bin/python3

"""
Pulls data from specified iLO and presents as Prometheus metrics
"""

from __future__ import absolute_import # Must be at the beginning of this file!
from __future__ import print_function  # Must be at the beginning of this file!

import os      # for ilo_password
import psutil  # process handling, zombies

from _socket import gaierror

import sys
import traceback
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
            ilo_password = os.getenv('ILO', 'ILO environment variable missing')
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
                                port=ilo_port, timeout=60)
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

            # --------------------------------------------------
            # get iLO health information 
            embedded_health = ilo.get_embedded_health()
            # print_err('STRUCTURE: {}'.format(embedded_health))
            # --------------------------------------------------
            
            # battery
            try:
                battery1_b = embedded_health['power_supplies']['Battery 1']
                label_b = embedded_health['power_supplies']['Battery 1']['label']
                present_b = embedded_health['power_supplies']['Battery 1']['present']
                status_b = embedded_health['power_supplies']['Battery 1']['status']
                model_b = embedded_health['power_supplies']['Battery 1']['model']
                spare_b = embedded_health['power_supplies']['Battery 1']['spare']
                serial_number_b = embedded_health['power_supplies']['Battery 1']['serial_number']
                capacity_b = embedded_health['power_supplies']['Battery 1']['capacity']
                firmware_version_b = embedded_health['power_supplies']['Battery 1']['firmware_version']
                # print_err('%s LABEL_B: {}'.format(label_b) % server_name )

            except BaseException as ex: # Python 3

                battery1_b = None

                # Get current system exception
                ex_type, ex_value, ex_traceback = sys.exc_info()

                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)

                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                   stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

                print("Exception type : %s " % ex_type.__name__)
                print("Exception message : %s" %ex_value)
                print("Stack trace : %s" %stack_trace)
                # print_err('%s BATTERY1-EXCEPT: {}'.format(str(ex)) % server_name )

            # # For HP server Gen 9 or higher
            # if 'memory_components' in embedded_health['memory']:
            #     memory_components = embedded_health['memory']['memory_components']
            #     for cpu_idx in range(0, len(memory_components)):
            #         cpu = memory_components[cpu_idx]
            #         total_memory_size = 0 if (cpu[1][1]['value'] == 'Not Installed') else int(cpu[1][1]['value'].split(' ')[0]) / 1024
            #         operating_frequency = cpu[2][1]['value']
            #         # Not expose operating_voltage
            #         prometheus_metrics.gauges["hpilo_memory_detail_gauge"].labels(product_name=product_name, server_name=server_name, cpu_id=cpu_idx, operating_frequency=operating_frequency, operating_voltage='').set(total_memory_size)

            for cpu_idx, cpu in embedded_health['memory']['memory_details_summary'].items():
                total_memory_size = 0 if (cpu['total_memory_size'] == 'N/A') else int(cpu['total_memory_size'].split()[0])
                prometheus_metrics.gauges["hpilo_memory_detail_gauge"].labels(product_name=product_name, server_name=server_name, cpu_id=cpu_idx.split("_")[1], operating_frequency=cpu['operating_frequency'], operating_voltage=cpu['operating_voltage']).set(total_memory_size)


            for cpu in embedded_health['processors'].values():
                prometheus_metrics.gauges["hpilo_processor_detail_gauge"].labels(product_name=product_name, server_name=server_name, cpu_id=cpu['label'].split()[1], name=cpu['name'].strip(), status=cpu['status'], speed=cpu['speed']).set(1 if "OK" in cpu["status"] else 0)

            for psu in embedded_health['power_supplies'].values():
                capacity_w = 0 if psu["capacity"] == "N/A" else int(psu["capacity"].split()[0])
                prometheus_metrics.gauges["hpilo_power_supplies_detail_gauge"].labels(product_name=product_name, server_name=server_name, psu_id=psu['label'].split()[-1], label=psu['label'], status=psu['status'], capacity_w=capacity_w, present=psu["present"]).set(1 if "Good" in psu["status"] else 0)

            if battery1_b is not None:
                if status_b.upper() == 'OK':
                    # (*1) The other battery metric "hpilo_battery_gauge" with other labels is below row 200 in this code  
                    # The "_gauge" is not a component of the created metric name. Metric name is: "hpilo_battery" 
                    # All labels here have to be defined in this file too: prometheus_metrics.py
                    prometheus_metrics.hpilo_battery1_gauge.labels(label=label_b,present=present_b,status=status_b,model=model_b,spare=spare_b,serial_number=serial_number_b,capacity=capacity_b,firmware_version=firmware_version_b,product_name=product_name,server_name=server_name).set(0)
                else:
                    prometheus_metrics.hpilo_battery1_gauge.labels(label=label_b,present=present_b,status=status_b,model=model_b,spare=spare_b,serial_number=serial_number_b,capacity=capacity_b,firmware_version=firmware_version_b,product_name=product_name,server_name=server_name).set(1)
            
            # battery-end
            
            # controller
            # Parse Controller Info
            try:
              # storage = embedded_health['storage']
              controller_on_system_board = embedded_health['storage']['Controller on System Board'] 
              label             = embedded_health['storage']['Controller on System Board']['label']
              status            = embedded_health['storage']['Controller on System Board']['status']
              controller_status = embedded_health['storage']['Controller on System Board']['controller_status']
              model             = embedded_health['storage']['Controller on System Board']['model']
              serial_number     = embedded_health['storage']['Controller on System Board']['serial_number']
              fw_version        = embedded_health['storage']['Controller on System Board']['fw_version']
            except:
                controller_on_system_board = None
            
            # There are controller in slot 1 and in slot 3 in one server
            try:
              controller_in_slot_1 = embedded_health['storage']['Controller in Slot 1']  
              label_1              = embedded_health['storage']['Controller in Slot 1']['label']
              status_1             = embedded_health['storage']['Controller in Slot 1']['status']
              controller_status_1  = embedded_health['storage']['Controller in Slot 1']['controller_status']
              model_1              = embedded_health['storage']['Controller in Slot 1']['model']
              serial_number_1      = embedded_health['storage']['Controller in Slot 1']['serial_number']
              fw_version_1         = embedded_health['storage']['Controller in Slot 1']['fw_version']
            except:
              controller_in_slot_1 = None
           
            try:
              controller_in_slot_3 = embedded_health['storage']['Controller in Slot 3']  
              label_3              = embedded_health['storage']['Controller in Slot 3']['label']
              status_3             = embedded_health['storage']['Controller in Slot 3']['status']
              controller_status_3  = embedded_health['storage']['Controller in Slot 3']['controller_status']
              model_3              = embedded_health['storage']['Controller in Slot 3']['model']
              serial_number_3      = embedded_health['storage']['Controller in Slot 3']['serial_number']
              fw_version_3         = embedded_health['storage']['Controller in Slot 3']['fw_version']
            except:
              controller_in_slot_3 = None

            
            if controller_on_system_board is not None:
                # print_err( "MH %s controller: {}".format(label) % server_name )
                if status.upper() == 'OK' and controller_status.upper() == 'OK':
                    prometheus_metrics.hpilo_controller_status_gauge.labels(label=label,status=status,controller_status=controller_status,serial_number=serial_number,model=model,fw_version=fw_version,product_name=product_name,server_name=server_name).set(0)
                else:
                    prometheus_metrics.hpilo_controller_status_gauge.labels(label=label,status=status,controller_status=controller_status,serial_number=serial_number,model=model,fw_version=fw_version,product_name=product_name,server_name=server_name).set(1)


            if controller_in_slot_1 is not None:
                # print_err( "MH %s controller: {}".format(label_1) % server_name )
                if status_1.upper() == 'OK' and controller_status_1.upper() == 'OK':
                    prometheus_metrics.hpilo_controller_status_1_gauge.labels(label=label_1,status=status_1,controller_status=controller_status_1,serial_number=serial_number_1,model=model_1,fw_version=fw_version_1,product_name=product_name,server_name=server_name).set(0)
                else:
                    prometheus_metrics.hpilo_controller_status_1_gauge.labels(label=label_1,status=status_1,controller_status=controller_status_1,serial_number=serial_number_1,model=model_1,fw_version=fw_version_1,product_name=product_name,server_name=server_name).set(1)


            if controller_in_slot_3 is not None: 
                # print_err( "MH %s controller: {}".format(label_3) % server_name )
                if status_3.upper() == 'OK' and controller_status_3.upper() == 'OK':
                    prometheus_metrics.hpilo_controller_status_3_gauge.labels(label=label_3,status=status_3,controller_status=controller_status_3,serial_number=serial_number_3,model=model_3,fw_version=fw_version_3,product_name=product_name,server_name=server_name).set(0)
                else:
                    prometheus_metrics.hpilo_controller_status_3_gauge.labels(label=label_3,status=status_3,controller_status=controller_status_3,serial_number=serial_number_3,model=model_3,fw_version=fw_version_3,product_name=product_name,server_name=server_name).set(1)
            # controller-end
            
            health_at_glance = embedded_health['health_at_a_glance'] 
            if health_at_glance is not None:
                for key, value in health_at_glance.items():
                    for status in value.items():
                        if status[0] == 'status':
                            gauge = 'hpilo_{}_gauge'.format(key)
                            if status[1].upper() == 'OK':
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,server_name=server_name).set(0)
                            elif status[1].upper() == 'DEGRADED':
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,server_name=server_name).set(1)
                            else:
                                prometheus_metrics.gauges[gauge].labels(product_name=product_name,server_name=server_name).set(2)

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
        
        pid = None
        try:
            while True:
                server.handle_request()
                
                # new block waiting for zombies
                for proc in psutil.process_iter():   
                    if 'hpilo-exporter' in proc.name():
                        pid = proc.pid
                        p = psutil.Process(pid)
                        if p.status() == psutil.STATUS_ZOMBIE:
                            # print("wait for pid: " + str(pid) + " p.status: " + str(  p.status()  )  ) # running, sleeping, zombie
                            if (pid != 0):
                                os.waitid(os.P_PID, pid, os.WEXITED) # terminate zombie
                        pid = None
                
        except KeyboardInterrupt:
            print_err("Killing exporter")
            server.server_close()

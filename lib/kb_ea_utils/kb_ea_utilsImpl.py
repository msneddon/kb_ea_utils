# -*- coding: utf-8 -*-
#BEGIN_HEADER
import sys
import traceback
from biokbase.workspace.client import Workspace as workspaceService
import requests
requests.packages.urllib3.disable_warnings()
import subprocess
import os
import re
from pprint import pprint, pformat
import uuid
from ReadsUtils.ReadsUtilsClient import ReadsUtils as ReadsUtils

#END_HEADER


class kb_ea_utils:
    '''
    Module Name:
    kb_ea_utils

    Module Description:
    Utilities for converting KBaseAssembly types to KBaseFile types
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "1.0.0"
    GIT_URL = "git@github.com:msneddon/kb_ea_utils"
    GIT_COMMIT_HASH = "e642d722169c442856846ecf813ccd0565d761a3"

    #BEGIN_CLASS_HEADER
    def log(self, target, message):
        if target is not None:
            target.append(message)
        print(message)
        sys.stdout.flush()

    def get_reads_ref_from_params(self, params):
        if 'read_library_ref' in params:
            return params['read_library_ref']

        if 'workspace_name' not in params and 'read_library_name' not in params:
            raise ValueError('Either "read_library_ref" or "workspace_name" with ' +
                             '"read_library_name" fields are required.')

        return str(params['workspace_name']) + '/' + str(params['read_library_name'])


    def get_report_string (self, fastq_file):
      cmd_string = " ".join (("fastq-stats", fastq_file));
      try:
          cmd_process = subprocess.Popen(cmd_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
          outputlines = []
          console = []
          while True:
             line = cmd_process.stdout.readline()
             outputlines.append(line)
             if not line: break
             #self.log(console, line.replace('\n', ''))

          report = '====' + fastq_file + '====' + "\n"
          report += "".join(outputlines)
      except:
          report = "Error in processing " +  fastq_file
      return report


    def get_ea_utils_result (self,refid, input_params):
      ref = [refid] 
      DownloadReadsParams={'read_libraries':ref}
      dfUtil = ReadsUtils(self.callbackURL)
      x=dfUtil.download_reads(DownloadReadsParams)
      report = ''
      fwd_file = None 
      rev_file = None 

      fwd_file    =  x['files'][ref[0]]['files']['fwd']
      otype =  x['files'][ref[0]]['files']['otype']

      #case of interleaved
      if (otype == 'interleaved'):
          report += self.get_report_string (fwd_file)
          
      #case of separate pair 
      if (otype == 'paired'):
         report += self.get_report_string (fwd_file)

         rev_file    =  x['files'][ref[0]]['files']['rev']
         report += self.get_report_string (rev_file)

      #case of single end 
      if (otype == 'single'):
         report += self.get_report_string (fwd_file)
      #print report
      return report

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.shockURL = config['shock-url']
        self.scratch = os.path.abspath(config['scratch'])
        self.handleURL = config['handle-service-url']

        self.callbackURL = os.environ.get('SDK_CALLBACK_URL')
        if self.callbackURL == None:
            raise ValueError ("SDK_CALLBACK_URL not set in environment")

        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)
        #END_CONSTRUCTOR
        pass


    def get_fastq_ea_utils_stats(self, ctx, input_params):
        """
        This function should be used for getting statistics on read library object types 
        The results are returned as a string.
        :param input_params: instance of type
           "get_fastq_ea_utils_stats_params" (if read_library_ref is set,
           then workspace_name and read_library_name are ignored) ->
           structure: parameter "workspace_name" of String, parameter
           "read_library_name" of String, parameter "read_library_ref" of
           String
        :returns: instance of String
        """
        # ctx is the context object
        # return variables are: ea_utils_stats
        #BEGIN get_fastq_ea_utils_stats
        token = ctx['token']
        wsClient = workspaceService(self.workspaceURL)
        # add additional info to provenance here, in this case the input data object reference
        input_reads_ref = self.get_reads_ref_from_params(input_params)

        info = None
        readLibrary = None
        try:
            readLibrary = wsClient.get_objects2({'objects':[{'ref': input_reads_ref}]})['data'][0]
            info = readLibrary['info']
            readLibrary = readLibrary['data']
        except Exception as e:
            raise ValueError('Unable to get read library object from workspace: (' + input_reads_ref + ')' + str(e))

        ea_utils_stats = ''
        ea_utils_stats = self.get_ea_utils_result(input_reads_ref, input_params)

        #END get_fastq_ea_utils_stats

        # At some point might do deeper type checking...
        if not isinstance(ea_utils_stats, basestring):
            raise ValueError('Method get_fastq_ea_utils_stats return value ' +
                             'ea_utils_stats is not type basestring as required.')
        # return the results
        return [ea_utils_stats]

    def run_app_fastq_ea_utils_stats(self, ctx, input_params):
        """
        This function should be used for getting statistics on read library object type.
        The results are returned as a report type object.
        :param input_params: instance of type
           "run_app_fastq_ea_utils_stats_params" (if read_library_ref is set,
           then workspace_name and read_library_name are ignored) ->
           structure: parameter "workspace_name" of String, parameter
           "read_library_name" of String, parameter "read_library_ref" of
           String
        :returns: instance of type "Report" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: report
        #BEGIN run_app_fastq_ea_utils_stats
        print (input_params)

        wsClient = workspaceService(self.workspaceURL)
        provenance = [{}]
        if 'provenance' in ctx:
            provenance = ctx['provenance']
        # add additional info to provenance here, in this case the input data object reference
        input_reads_ref = self.get_reads_ref_from_params(input_params)
        if 'workspace_name' not in input_params:
            raise ValueError('"workspace_name" field is required to run this App"')
        workspace_name = input_params['workspace_name']
        provenance[0]['input_ws_objects'] = [input_reads_ref]

        info = None
        readLibrary = None
        try:
            readLibrary = wsClient.get_objects([{'ref': input_reads_ref}])[0]
            info = readLibrary['info']
            readLibrary = readLibrary['data']
        except Exception as e:
            raise ValueError('Unable to get read library object from workspace: (' + input_reads_ref + ')' + str(e))
#        ref=['11665/5/2', '11665/10/7', '11665/11/1' ]
        #ref=['11802/9/1']
        report = self.get_ea_utils_result(input_reads_ref, input_params)
        reportObj = {
            'objects_created':[],
            'text_message':report
        }

        reportName = 'run_fastq_stats_'+str(uuid.uuid4())
        report_info = wsClient.save_objects({
            'workspace':workspace_name,
            'objects':[
                 {
                  'type':'KBaseReport.Report',
                  'data':reportObj,
                  'name':reportName,
                  'meta':{},
                  'hidden':1, # important!  make sure the report is hidden
                  'provenance':provenance
                 }
            ] })[0]  
        print('saved Report: '+pformat(report_info))
        
        report = { "report_name" : reportName,"report_ref" : str(report_info[6]) + '/' + str(report_info[0]) + '/' + str(report_info[4]) }

        #print (report)
        #END run_app_fastq_ea_utils_stats

        # At some point might do deeper type checking...
        if not isinstance(report, dict):
            raise ValueError('Method run_app_fastq_ea_utils_stats return value ' +
                             'report is not type dict as required.')
        # return the results
        return [report]

    def get_ea_utils_stats(self, ctx, input_params):
        """
        This function should be used for getting statistics on fastq files. Input is string of file path.
        Output is a report string.
        :param input_params: instance of type "ea_utils_params"
           (read_library_path : absolute path of fastq files) -> structure:
           parameter "read_library_path" of String
        :returns: instance of String
        """
        # ctx is the context object
        # return variables are: report
        #BEGIN get_ea_utils_stats
        read_library_path = input_params['read_library_path']
        report = self.get_report_string (read_library_path)
        #END get_ea_utils_stats

        # At some point might do deeper type checking...
        if not isinstance(report, basestring):
            raise ValueError('Method get_ea_utils_stats return value ' +
                             'report is not type basestring as required.')
        # return the results
        return [report]

    def calculate_fastq_stats(self, ctx, input_params):
        """
        This function should be used for getting statistics on fastq files. Input is string of file path.
        Output is a data structure with different fields.
        :param input_params: instance of type "ea_utils_params"
           (read_library_path : absolute path of fastq files) -> structure:
           parameter "read_library_path" of String
        :returns: instance of type "ea_report" (read_count - the number of
           reads in the this dataset total_bases - the total number of bases
           for all the the reads in this library. gc_content - the GC content
           of the reads. read_length_mean - The average read length size
           read_length_stdev - The standard deviation read lengths phred_type
           - The scale of phred scores number_of_duplicates - The number of
           reads that are duplicates qual_min - min quality scores qual_max -
           max quality scores qual_mean - mean quality scores qual_stdev -
           stdev of quality scores base_percentages - The per base percentage
           breakdown) -> structure: parameter "read_count" of Long, parameter
           "total_bases" of Long, parameter "gc_content" of Double, parameter
           "read_length_mean" of Double, parameter "read_length_stdev" of
           Double, parameter "phred_type" of String, parameter
           "number_of_duplicates" of Long, parameter "qual_min" of Double,
           parameter "qual_max" of Double, parameter "qual_mean" of Double,
           parameter "qual_stdev" of Double, parameter "base_percentages" of
           mapping from String to Double
        """
        # ctx is the context object
        # return variables are: ea_stats
        #BEGIN calculate_fastq_stats
        read_library_path = input_params['read_library_path']
        ea_report = self.get_report_string (read_library_path)
        ea_stats = {}
        report_lines = ea_report.splitlines()
        report_to_object_mappings = {'reads': 'read_count',
                                     'total bases': 'total_bases',
                                     'len mean': 'read_length_mean',
                                     'len stdev': 'read_length_stdev',
                                     'phred': 'phred_type',
                                     'dups': 'number_of_duplicates',
                                     'qual min': 'qual_min',
                                     'qual max': 'qual_max',
                                     'qual mean': 'qual_mean',
                                     'qual stdev': 'qual_stdev'}
        integer_fields = ['read_count', 'total_bases', 'number_of_duplicates']
        for line in report_lines:
            line_elements = line.split()
            line_value = line_elements.pop()
            line_key = " ".join(line_elements)
            line_key = line_key.strip()
            if line_key in report_to_object_mappings:
                # print ":{}: = :{}:".format(report_to_object_mappings[line_key],line_value)
                value_to_use = None
                if line_key == 'phred':
                    value_to_use = line_value.strip()
                elif report_to_object_mappings[line_key] in integer_fields:
                    value_to_use = int(line_value.strip())
                else:
                    value_to_use = float(line_value.strip())
                ea_stats[report_to_object_mappings[line_key]] = value_to_use
            elif line_key.startswith("%") and not line_key.startswith("%dup"):
                if 'base_percentages' not in ea_stats:
                    ea_stats['base_percentages'] = dict()
                dict_key = line_key.strip("%")
                ea_stats['base_percentages'][dict_key] = float(line_value.strip())
        # populate the GC content (as a value betwwen 0 and 1)
        if 'base_percentages' in ea_stats:
            gc_content = 0
            if "G" in ea_stats['base_percentages']:
                gc_content += ea_stats['base_percentages']["G"]
            if "C" in ea_stats['base_percentages']:
                gc_content += ea_stats['base_percentages']["C"]
            ea_stats["gc_content"] = gc_content / 100
        # set number of dups if no dups, but read_count
        if 'read_count' in ea_stats and 'number_of_duplicates' not in ea_stats:
            ea_stats["number_of_duplicates"] = 0
        #END calculate_fastq_stats

        # At some point might do deeper type checking...
        if not isinstance(ea_stats, dict):
            raise ValueError('Method calculate_fastq_stats return value ' +
                             'ea_stats is not type dict as required.')
        # return the results
        return [ea_stats]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK", 'message': "", 'version': self.VERSION, 
                     'git_url': self.GIT_URL, 'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]

'''
Created on Aug 11, 2018

@author: n.amafu
@desc: Reusable Library to parse BitTorrent Files. 
       BTParser.py exposes the following pieces of information about BitTorrent files ( when available in the file )
       - Creation date
       - Client that created the file
       - The tracker URL
       - The name, length and checksum of each file described in the torrent 
       
@usage: It Can be imported and used like a library file or extended.
        For test, Place lib file(BTParser) in same directory as torrent files and run the lib file from commandline eg. python BTParser. 
'''

import os, cStringIO, re, hashlib
from datetime import datetime

class BTParser(object):
    # TODO: Replace delimiters with constant attributes...
    # Make program accessible by passing params from commandline or terminal
    
    def __init__(self, torrent_file):
        '''
        STEP 1.
            At constructor level, prepare(validate) torrent file, foremost.
            1. Filename should be instance of a string
            2. Torrent file path should be valid(exist) 
        '''
        
        # checking for errors..
        if not isinstance(torrent_file, basestring):
            raise ValueError("String was expected for file torrent path")
        
        if not os.path.exists(torrent_file):
            raise IOError('The torrent file path "{}" does not exist.'.format(torrent_file))
        
        # read torrent file..
        with open(torrent_file, 'rb') as tfile:
            tfile_obj = tfile.read()
            
        self._file_buffer_creator(tfile_obj)
        
        self.parsed_torrent_content = self._torrent_parser()
    
    
    
    
    def _file_buffer_creator(self, torrent_file):
        '''
        STEP 2. 
            Convert to text stream...
            Options available StringIO / cStringIO (Faster version of StringIO)
        
        '''
        self.torrent_buff_str = cStringIO.StringIO(torrent_file)
        self.curr_torrent_str = None
        
        
    def next_torr_char(self):
        self.curr_torrent_str = self.torrent_buff_str.read(1)
        return self.curr_torrent_str
    
    def seek_char_back(self, pos=-1, offset=1):
        return self.torrent_buff_str.seek(pos, offset)
    
    def number_paser(self, delim):
        
        num_result = ''
        while True:
            par_int_char = self.next_torr_char()
            if re.match('\d', par_int_char):
                num_result +=par_int_char
            else:
                if par_int_char == delim:
                    break
                else:
                    raise Exception("Number parser Error!")
                
        return int(num_result)
    
    def parse_torr_string(self):
        ''' Read from current position to the length '''
        
        self.seek_char_back() # Stepback once to get the number
       
        str_len = self.number_paser(':')
        
        if not str_len:
            raise Exception("String Parsing Error! Invalid character at position %d" % self.torrent_buff_str.tell() )
        
        return self.torrent_buff_str.read(str_len)
    
    def parse_torr_integers(self):
        
        # Double check if integer parsing format is correct.
        if self.curr_torrent_str != 'i':
            raise Exception("Integer Parsing Error! Invalid character at position %d" % self.torrent_buff_str.tell() )
        
        return int(self.number_paser('e'))
                
                
    
    
    def _torrent_parser(self):
        
        # The whole bytes string is a dict. which should start with a d.
        valid_char = self.next_torr_char()
        
        if not valid_char: return;
        
        if valid_char == 'e': return; # End of dictionary
        
        elif valid_char == 'i': # INTEGER BEGINS : i<integer>e: 
            return self.parse_torr_integers()
        
        elif re.match('\d', valid_char): # digits in string.
            return self.parse_torr_string()
        
        elif valid_char == 'l':# LIST START 'l' END 'e' => l[value 1][value2][value3][...]e
            list_res = []
            while True:
                litem = self._torrent_parser()
                if not litem:
                    break
                list_res.append(litem)
                
            return list_res
                
        elif valid_char == 'd':# DICT : START 'd' END 'e'.
            dict_res = {}
            while True:
                dkey = self._torrent_parser()
                if not dkey:
                    break
                dval = self._torrent_parser()
                
                dict_res[dkey] = dval
                
            return dict_res  
            

    def get_creation_date(self):
        ''' Returns the UTC date and time the torrent file was created '''
        
        readable_date_time = None
        parsed_time_stamp = self.parsed_torrent_content.get('creation date', None)
        
        if parsed_time_stamp:
            readable_date_time = datetime.utcfromtimestamp(parsed_time_stamp).strftime('%Y-%m-%dT%H:%M:%SZ')
            
        return readable_date_time
    
    def get_client_name(self):
        '''  Returns then name of the torrent file creator '''
        return self.parsed_torrent_content.get('created by', None)
    
    def get_tracker_URL(self):
        ''' Returns the Tracker URL '''
        return self.parsed_torrent_content.get('announce', None)
    
    def get_file_details(self):
        ''' Returns dict of file info (name, length checksum) of physical files on disc as described in torrent file. '''
        
        parsed_info_dict = []
        file_info = self.parsed_torrent_content.get('info', None) # dict of file details
        mult_files = file_info.get('files') # list of dicts
        
        if file_info:
            if mult_files: # multiple files
                for sfile in mult_files:
                    parsed_info_dict.append((file_info.get('name', None), 
                                             sfile.get('length', None), 
                                             self._get_checksum(file_info.get('name', None)), )) 
            else: # single file
                parsed_info_dict.append((file_info.get('name', None), 
                                         file_info.get('length', None), 
                                         self._get_checksum(file_info.get('name', None)), ))
            
        
        return parsed_info_dict
    
    def _get_checksum(self, file_name):
        '''
        :param filename 
        :return checksum of file if it exists
        :notes assumption is that lib file exist in same folder as torrent files.
               and physical torrent files are named the same as described in metafile
        '''
        hash_md5 = hashlib.md5()
        try:
            with open(file_name, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except IOError:
            raise Exception("Checksum Error! Encountered Problems opening %s." % file_name)
        
        return hash_md5.hexdigest()
  


def main():
    # Library file is to be placed within folder which contains other torrent files..    
    
    # If Torrent files are parsed...else run default
    # Read all files from current directory...For tet.    
    
    fcount = 0
    files = [fl for fl in os.listdir('.') if os.path.isfile(fl)]
    for sfile in files:
        file_name, file_ext = os.path.splitext(sfile)
        if file_ext == '.torrent':
            fcount +=1
            
            # For each file object...
            btp = BTParser(sfile)
      
            print 'Parsing %s' % sfile
            print (btp.get_creation_date(), btp.get_client_name(), btp.get_tracker_URL(), btp.get_file_details())
            print '-'*100
            print ''
          
    
    if fcount == 0:
        print 'No torrent files available...'
    

if __name__ == "__main__" : main()
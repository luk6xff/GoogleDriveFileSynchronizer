import httplib2
import os
import sys
import re
import io

import oauth2client
from oauth2client import client
from oauth2client import tools
import apiclient
from apiclient import discovery
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload


import logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) 
logger.setLevel(logging.NOTSET)
logging.disable(logging.CRITICAL) #disables all logs

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'GoogleDriveManager'
FOLDER_TO_BE_SYNCED_PATH=r'C:\Users\igbt6\Desktop\CurrentProjects\GoogleDriveFileSynchronizer\test\GOOGLE_DRIVE_SYNCER_TEST_FOLDER'
FILE_TYPE=frozenset(["FILE","FOLDER"])

class GoogleDriveSynchronizer():
    
    def __init__(self,root_folder_name):
        self._root_folder= GoogleDriveFile(root_folder_name)
        self._credentials = self.get_credentials()
        self._http_auth = self._credentials.authorize(httplib2.Http())
        self._service = discovery.build('drive', 'v3', http=self._http_auth)
        self._root_folder.id=self.check_if_file_exist_create_new_one(self._root_folder.name)
        
    def get_credentials(self):
        '''Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        Returns:
            Credentials, the obtained credential.
        '''
        home_dir = os.getcwd()
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,'google_drive_manager.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            logger.debug('Storing credentials to ' + credential_path)
        return credentials
       
    def find_folder_or_file_by_name(self,file_name,parent_id=None):
        if(file_name ==None or len(file_name)==0):
            return False
        page_token = None
        if parent_id is not None:
            query=("name = '%s' and '%s' in parents"%(file_name,parent_id))
        else:
            query=("name = '%s'"%file_name)
        while True:
            response = self._service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name, parents)',pageToken=page_token).execute()
            for file in response.get('files', []):
                logger.debug('Found file: %s (%s) %s' % (file.get('name'), file.get('id'),file.get('parents')))
                return file.get('id')
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                return False;
        
    def check_if_file_exist_create_new_one(self,file_name,file_type="FOLDER",parent_id=None):
        if file_type not in FILE_TYPE:
            raise ValueError("Incorrect file_type arg. Allowed types are: %s"%(', '.join(list(FILE_TYPE))))
        id = self.find_folder_or_file_by_name(file_name,parent_id)
        if id:
            logger.debug(file_name + " exists")
        else:
            logger.debug(file_name + " does not exist")
            if file_type is "FILE":
                pass #TODO
            else:
                id=self.create_new_folder(file_name,parent_id)
        return id
        
    
    def list_all_files_in_main_folder(self):
        results = self._service.files().list().execute()
        items = results.get('files', [])
        if not items:
            logger.debug('No files found.')
        else:
            logger.debug('Files:')
            for item in items:
                logger.debug('{0} ({1})'.format(item['name'], item['id']))
        
    def create_new_folder(self,folder_name,parent_folders_id =None):
        parent_id= parent_folders_id if parent_folders_id is None else [parent_folders_id]
        file_metadata = {
            'name' : folder_name,
            'mimeType' : 'application/vnd.google-apps.folder',
            'parents': parent_id
        }
        file = self._service.files().create(body=file_metadata, fields='id').execute()
        logger.debug('Created Folder ID: %s' % file.get('id'))
        return file.get('id')
    
    def insert_file_in_folder(self,file_name,path,parent_folder_id,file_mime_type=None):
        parent_id= parent_folders_id if parent_folder_id is None else [parent_folder_id]
        file_metadata = {
          'name' : file_name,
          'parents': parent_id
        }
        media = MediaFileUpload(path,mimetype=file_mime_type,  # if None, it will be guessed 
                                resumable=True)
        file = self._service.files().create(body=file_metadata,media_body=media,fields='id').execute()
        logger.debug('File ID: %s' % file.get('id'))
        return file.get('id') 
    
    def _get_name_and_parent_from_path(self,path):
        splitted_path= os.path.split(path)
        file_name=splitted_path[1]
        parent_folder_name=os.path.split(splitted_path[0])[1]
        return file_name, parent_folder_name
    
    def create_folders_tree(self,folders):
        if folders is None or len(folders)==0:
            raise ValueError("Incorrect folders format")
        self._folders_tree=[self._root_folder]
        #creates folders in root folder
        for name, data in folders.items():
            for path in data["FOLDERS"]:
                folder_name,parent_folder_name=self._get_name_and_parent_from_path(path)
                logger.debug(parent_folder_name+" -> "+folder_name)
                for folder in self._folders_tree:
                    if folder.name==parent_folder_name:
                        temp_folder=GoogleDriveFile(folder_name)
                        temp_folder.parent_id=folder.id
                        id=self.check_if_file_exist_create_new_one(folder_name,parent_id=temp_folder.parent_id)
                        temp_folder.id=id 
                        self._folders_tree.append(temp_folder)                        
    
    def synchronize_files(self,files_data):
        if files_data is None or len(files_data)==0:
            raise ValueError("Incorrect files format")
        self.create_folders_tree(files_data)
        for main_folder_name, data in files_data.items():
            for path in data["FILES"]:
                file_name,parent_folder_name=self._get_name_and_parent_from_path(path)
                logger.debug("PATH: "+path+" "+parent_folder_name+" -> "+file_name)
                for folder in self._folders_tree:
                    if folder.name==parent_folder_name:
                        logger.debug("$$$ "+file_name+" "+path+" "+folder.id+" ")
                        try:
                            if not self.find_folder_or_file_by_name(file_name,folder.id):
                                self.insert_file_in_folder(file_name,path,folder.id)
                        except:
                            pass #just skip fail
                        break
                        
            
        
    def download_file(self,file_name,file_id):
        request = self._service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.debug("Download %d%%." % int(status.progress() * 100))

            
            
            
class FilesFolder():

    def __init__(self, main_folder_path):
        if not os.path.exists(main_folder_path):
            raise IOError("incorrect path of your main folder!")       
        self._root_path=main_folder_path 
        self._files={}
        self._list_all_filepaths()
        
    def _list_all_filepaths(self):
        #logger.debug(os.listdir(self._root_path))
        folders_set=set([])
        files_set= set([])
        for file_path in os.listdir(self._root_path):
            if os.path.isfile(os.path.join(self._root_path,file_path)):
                files_set.add(os.path.join(self._root_path,file_path))
            else:
                self._files[file_path]={"PATH":os.path.join(self._root_path,file_path)}
        for name,dataDict in self._files.items():
            for root_dir, subdirs, files in os.walk(dataDict["PATH"]):
                folders_set.add(root_dir)
                for file in files:
                        files_set.add(os.path.join(root_dir,file))
                for subdir in subdirs:
                    folders_set.add(os.path.join(root_dir,subdir))
                    for file in files:
                        files_set.add(os.path.join(root_dir,file))

            with open("result.txt","a") as f:
                f.write("\n--------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write("----------------------NAME---------------------------\n")
                f.write(name)
                f.write('\n')
                
                f.write("\n--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                f.write("--------------------FOLDERS---------------------------\n")
                for i in sorted(folders_set, key=len):
                    f.write(i)
                    f.write('\n')
                f.write("\n--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                f.write("--------------------FILES---------------------------\n")
                for i in files_set:
                    f.write(i)
                    f.write('\n')
            self._files[name]["FOLDERS"]=sorted(folders_set, key=len)
            self._files[name]["FILES"]=list(files_set)
            # logger.debug("\n--------------------PATH---------------------------\n")
            # logger.debug(self._files[name]["PATH"])
            # logger.debug("\n--------------------FOLDERS---------------------------\n")
            # logger.debug(self._files[name]["FOLDERS"])
            # logger.debug("\n--------------------FILES---------------------------\n")
            # logger.debug(self._files[name]["FILES"])
            #break
      
    def extract_folder_name_from_path(self,folder_path):
        m =re.search(r'\\(\w*)$',folder_path)
        if m:
            return m.group(1)
        else:
            raise ValueError("Incorrect folder_path %s"%folder_path)
            
    @property
    def files(self):
        return self._files
    
    @property
    def root_folder_path(self):
        return self._root_path
        
               
class GoogleDriveFile():
    """ Helper class that describes File or Folder on GoogleDrive server"""
    def __init__(self,file_name):
        self.name= file_name
        self.id =None
        self.parent_id=''
    
        
if __name__ == '__main__':
    file_folder = FilesFolder(os.path.join(FOLDER_TO_BE_SYNCED_PATH))
    google_drive_syncer= GoogleDriveSynchronizer(file_folder.extract_folder_name_from_path(file_folder.root_folder_path))  
    #google_drive_syncer.list_all_files_in_main_folder()
    #for name, data in file_folder.files.items():
        #google_drive_syncer.check_if_file_exist_create_new_one(name)
    # TEST1
    # id=google_drive_syncer.check_if_file_exist_create_new_one("TEST_FOLDER")
    # google_drive_syncer.insert_file_in_folder("TestFolderFile.txt",os.path.join(FOLDER_TO_BE_SYNCED_PATH,"cowsay.txt"),id)
    # id=google_drive_syncer.check_if_file_exist_create_new_one("TEST_SUB_FOLDER",id)
    # google_drive_syncer.insert_file_in_folder("TestSubFolderFile.txt",os.path.join(FOLDER_TO_BE_SYNCED_PATH,"cowsay.txt"),id)
    
    #TEST2
    #google_drive_syncer.create_folders_tree(file_folder.files)
    
    #TEST3
    google_drive_syncer.synchronize_files(file_folder.files)
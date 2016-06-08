import unittest
import sys
sys.path.insert(0,r'C:\Users\igbt6\Desktop\CurrentProjects\GoogleDriveFileSynchronizer')
from app.GoogleDriveSync import FilesFolder
from app.GoogleDriveSync import GoogleDriveSynchronizer
import os

FOLDER_TO_BE_SYNCED_PATH= r'C:\Users\igbt6\Desktop\CurrentProjects\GoogleDriveFileSynchronizer\test\GOOGLE_DRIVE_SYNCER_TEST_FOLDER'
class FolderToBeSynchronizedTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):     
        cls.file_folder = FilesFolder(os.path.join(FOLDER_TO_BE_SYNCED_PATH))
        
    def test_is_instance_created(self):         
        self.assertIsNotNone(self.file_folder)
    
    def test_parse_folders_paths(self):
        self.assertEquals(''.join(self.file_folder.get_folder_paths_list()[0]),os.path.join(FOLDER_TO_BE_SYNCED_PATH))
        
    def test_parse_files_paths(self):
        self.assertEquals(len(self.file_folder.get_files_paths_list()),37)

class GoogleDriveSynchronizerTests(unittest.TestCase):

    def setUp(self):
        self.file_folder = FilesFolder(os.path.join(FOLDER_TO_BE_SYNCED_PATH))
        self.google_drive_syncer= GoogleDriveSynchronizer(self.file_folder.extract_folder_name_from_path(self.file_folder.root_folder_path))  
    
    def test_is_instance_created(self):         
        self.assertIsNotNone(self.google_drive_syncer)
    
    def test_create_folders_on_gd(self):
        id=self.google_drive_syncer.check_if_file_exist_create_new_one("TEST_FOLDER")
        self.assertTrue(id)
        self.assertTrue(self.google_drive_syncer.insert_file_in_folder("TestFolderFile.txt",os.path.join(FOLDER_TO_BE_SYNCED_PATH,"cowsay.txt"),id))
        id=self.google_drive_syncer.check_if_file_exist_create_new_one("TEST_SUB_FOLDER",parent_id=id)
        self.assertTrue(id)
        id= self.google_drive_syncer.insert_file_in_folder("TestSubFolderFile.txt",os.path.join(FOLDER_TO_BE_SYNCED_PATH,"cowsay.txt"),id)
        self.assertTrue(id)
    
    def test_create_folders_tree_on_server(self):
        self.google_drive_syncer.create_folders_tree(self.file_folder.get_folder_paths_list())
    
    def test_folders_synchronization(self):
        self.google_drive_syncer.synchronize_files(self.file_folder.get_folder_paths_list(),self.file_folder.get_files_paths_list())    
    
    def tearDown(self):
        self.file_folder=None
        self.google_drive_syncer= None
    

        
    
def test_suite():
    """builds the test suite."""
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(FolderToBeSynchronizedTests))
    suite.addTests(unittest.makeSuite(GoogleDriveSynchronizerTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

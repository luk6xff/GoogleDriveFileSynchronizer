import unittest
from GoogleDriveSync import FilesFolder
from GoogleDriveSync import GoogleDriveSynchronizer
import os

class FolderToBeSynchronizedTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        FOLDER_TO_BE_SYNCED_PATH= 'L:\EBOOKS'
        cls.file_folder = FilesFolder(os.path.join(FOLDER_TO_BE_SYNCED_PATH))
        
    def test_is_instance_created(self):         
        self.assertIsNotNone(self.file_folder)
        



class GoogleDriveSynchronizer(unittest.TestCase):

    def setUp(self):
        FOLDER_TO_BE_SYNCED_PATH= 'L:\EBOOKS'
        file_folder = FilesFolder(os.path.join(FOLDER_TO_BE_SYNCED_PATH))
        google_drive_syncer= GoogleDriveSynchronizer(file_folder.extract_folder_name_from_path(file_folder.root_folder_path))  
    
    def test_is_instance_created(self):         
        self.assertIsNotNone(self.google_drive_syncer)
    
    
def test_suite():
    """builds the test suite."""
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(FolderToBeSynchronizedTests))
    suite.addTests(unittest.makeSuite(GoogleDriveSynchronizer))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

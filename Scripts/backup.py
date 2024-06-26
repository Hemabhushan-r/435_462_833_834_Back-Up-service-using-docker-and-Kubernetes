import json
import pickle
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
import io
import os
from mimetypes import MimeTypes
import logging

logging.basicConfig(filename='./back.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Define the Google Drive API scopes and service account file path
SCOPES = ['https://www.googleapis.com/auth/drive']
# SERVICE_ACCOUNT_FILE = "./flutterchatapp-60a2a-53b5f344f20c.json"

# Create credentials using the service account file
# credentials = service_account.Credentials.from_service_account_file(
#    SERVICE_ACCOUNT_FILE, scopes=SCOPES)


def init_drive():
    global drive_service
    with open("./Credentials/google-token.pkl", "rb") as f:
        credentials = pickle.load(f)
    credentials = json.loads(credentials)
    credentials = service_account.Credentials.from_service_account_info(
        credentials)
    # Build the Google Drive service
    drive_service = build('drive', 'v3', credentials=credentials)


def upload_basic(file_name, file_directory, upload_directory_id):
    """Insert new file.
    Returns : Id's of the file uploaded

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    # creds, _ = google.auth.default()

    try:
        # create drive api client
        # service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": file_name, "parents": [upload_directory_id]}
        mime_type = MimeTypes().guess_type(file_name)[0]
        media = MediaFileUpload(
            file_directory, mimetype=mime_type, resumable=True)
        # pylint: disable=maybe-no-member
        logging.info(
            f"Checking if file '{file_name}' already exists in Google Drive")
        response = drive_service.files().list(
            q=f"name='{file_name}' and parents='{upload_directory_id}' and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=None).execute()

        if not response['files']:
            logging.info(f"File '{file_name}' not found.Uploading new file...")
            file = (
                drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            logging.info(f"File '{file_name}' uploaded successfully")
            # print(f'File ID: {file.get("id")}')
        else:
            for file in response.get('files', []):
                logging.info(
                    f"File '{file_name}' found. Updating existing file...")
                update_file = drive_service.files().update(
                    fileId=file.get('id'),
                    media_body=media,
                ).execute()
                logging.info(f"File '{file_name}' Updated.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    return file.get("id")


def create_folder(folder_name, parent_folder_id=None):
    """Create a folder in Google Drive and return its ID."""
    folder_metadata = {
        'name': folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        'parents': [parent_folder_id] if parent_folder_id else []
    }
    results = drive_service.files().list(q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and parents='{parent_folder_id}'",
                                         spaces='drive',
                                         fields='files(id, name)').execute()

    folders = results.get('files', [])
    if folders:
        logging.info(f"A folder with name '{folder_name}' already exists.")
        for folder in folders:
            return folder['id']
            # print(f"Folder ID: {folder['id']}")
    else:
        logging.info(
            f"A folder with name '{folder_name}' does not exist.Creating folder")
        created_folder = drive_service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()

    # print(f'Created Folder ID: {created_folder["id"]}')
    return created_folder["id"]


def list_folder(parent_folder_id=None, delete=False):
    """List folders and files in Google Drive."""
    results = drive_service.files().list(
        q=f"'{parent_folder_id}' in parents and trashed=false" if parent_folder_id else None,
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print("No folders or files found in Google Drive.")
    else:
        print("Folders and files in Google Drive:")
        for item in items:
            print(
                f"Name: {item['name']}, ID: {item['id']}, Type: {item['mimeType']}")
            if delete:
                delete_files(item['id'])


def delete_files(file_or_folder_id):
    """Delete a file or folder in Google Drive by ID."""
    try:
        drive_service.files().delete(fileId=file_or_folder_id).execute()
        print(f"Successfully deleted file/folder with ID: {file_or_folder_id}")
    except Exception as e:
        print(f"Error deleting file/folder with ID: {file_or_folder_id}")
        print(f"Error details: {str(e)}")


def download_file(file_id, destination_path):
    """Download a file from Google Drive by its ID."""
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, mode='wb')

    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")


def upload_directory(directory_path, upload_directory_id):
    """Uploads a directory and its children to Google Drive while maintaining the same structure."""
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # print("file", file_path)
            logging.info(f"Processing File : '{file_name}'")
            upload_basic(file_name, file_path, upload_directory_id)

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            # print("dir", dir_path)
            # dir_metadata = {"name": dir_name, "parents": [upload_directory_id]}
            logging.info(f"Processing Directory '{dir_name}'")
            new_folder_id = create_folder(dir_name, upload_directory_id)
            upload_directory(dir_path, new_folder_id)
            logging.info(f"Completed Processing Directory '{dir_name}'")
        break


if __name__ == '__main__':
    for dir, folders, files in os.walk("./TargetDirectory"):
        pass
        # print(dir, folders, files)
    init_drive()
    upload_directory("./TargetDirectory", "1kAXUCXfxjLNLDm-OV6DNuZd8A5wcDRkr")
    logging.info(f"Completed Backup Process")
    # Example usage:

    # Create a new folder
    # create_folder("MyNewFolder")

    # List folders and files
    # list_folder()

    # Delete a file or folder by ID
    # delete_files("your_file_or_folder_id")
    # upload_basic("text.txt", "text/plain", "/kaggle/working/test.txt",
    #              "1kAXUCXfxjLNLDm-OV6DNuZd8A5wcDRkr")
    # Download a file by its ID
    # download_file("1IGjYbm6NCBOF60sTr5uHntYl1RlLHBCn", "/kaggle/working/")

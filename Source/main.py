
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
import os
from tqdm import tqdm
from tkinter import Tk
from tkinter import filedialog
import random as rnd
import subprocess

user_dir = os.path.expanduser("~")  # This gives the path to the user's home directory.
data_dir = os.path.join(user_dir, "Fernet/")  # Creating a folder in the user's home directory.

def generate_key(token=''): 
    key = Fernet.generate_key()
    with open(f"{data_dir}history_secret_{token}.key", 'ab') as save:
        save.write(key + b'\n')

    return key

def encrypt_file(path: str, key, new_path) -> bool:
    # Encrypts the file at the given path using the provided key and saves it to a new location.
    fernet_inst = Fernet(key)

    def retry():
        """Attempt to encrypt the file."""
        with open(path, 'rb') as target_file:
            content = target_file.read()
        encrypted = fernet_inst.encrypt(content)
        with open(new_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted)

    try:
        retry()
    except FileNotFoundError:
        print(f'Invalid file path: {path}')
        return False
    
    except PermissionError:
        # Remove hidden and read-only attributes using subprocess
        try:
            # Use subprocess to execute the attrib command safely for non-ASCII filenames
            subprocess.run(['attrib', '-h', '-r', path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            retry()
        except subprocess.CalledProcessError as e:
            print(f'[Skipped] Access denied: {path}\n{e.stderr.decode()}')
            return False
    
    except IsADirectoryError:
        print(f'[Skipped] Folder: {path}')
        return False
    
    return True

    
def decrypt_file(path:str, key, new_path) -> bool: #Enhance Logging
    try:
        fernet_inst = Fernet(key)
        with open(path, 'rb') as encrypted_file: 
            content = encrypted_file.read()
            decrypted_content = fernet_inst.decrypt(content)
    
    except FileNotFoundError:
        print(f'File not found: {path}')
        return False
    
    except ValueError:
        print(f'{key} is not a valid key format')
        return False
    
    except InvalidToken:
        print(f'Wrong key for decryption:{key}')
        return False

    try:
        with open(new_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_content)
    
    except FileNotFoundError:
        print(f'Invalid encrypted file destination: {new_path}')
        return False
    
    return True
    
    
class CryptoFile:
    key_dir = ''
    def __init__(self, key_dir):
        self.key_dir = key_dir
    
    def encrypt(self, target:str, new_dest=None, tag=''):
        if not target.endswith('/'):
            target+='/'
        target_files = os.listdir(target)
        files = []
        key = generate_key()
        rnd_flag = rnd.randint(100000,999999)
        
        with open(f'{self.key_dir}/secret_{tag}_{rnd_flag}.key', 'wb') as key_file:
            key_file.write(key)
            
        for f in tqdm(target_files, 'Encrypting files'):
            if encrypt_file(target+f, key, target+f): # Fix: Dont list access denied
                files.append(target+f+'\n')
        
        with open(f'{self.key_dir}/encrypted_{tag}_{rnd_flag}.txt', 'w', encoding='utf-8') as file_list:
            for f in files:
                file_list.write(f)
        
    def decrypt(self):
        preproccesed_files = os.listdir(self.key_dir)
        if len(preproccesed_files) == 0:
            print('No encryption history found')
            return None
        preproccesed_files = [f for f in preproccesed_files if f.endswith('.txt')]
        # list(filter(lambda x: x.endswith('.txt'), preproccesed_files)) also work
        
        for f,k in enumerate(preproccesed_files, start=1):
            print(f'{f}. {k}')
        
        choose = -1
        while not (len(preproccesed_files) >= choose > 0):
            choose = int(input('Select one of the above: '))
    
        tag = preproccesed_files[choose-1].split('_')[1]
        flag = preproccesed_files[choose-1].split('_')[2].split('.')[0]
        key_file_name = f'secret_{tag}_{flag}.key'
        key = None
        tg_files = []
        
        with open(self.key_dir+preproccesed_files[choose-1], 'r', encoding='utf-8') as rfile:
            tg_files = rfile.read().split('\n')
        
        del tg_files[len(tg_files)-1]
            
        with open(self.key_dir+key_file_name, 'rb') as rfile:
            key = rfile.read()
        
        for f in tqdm(tg_files,'Decrypting files'):
            decrypt_file(f,key,f)
        
        os.remove(self.key_dir+preproccesed_files[choose-1])
        os.remove(self.key_dir+key_file_name)


if __name__ == '__main__':
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    def openFolder():
        TkWindow = Tk()
        TkWindow.withdraw()
        dest = filedialog.askdirectory()
        TkWindow.destroy()
        return dest

    def openFile():
        TkWindow = Tk()
        TkWindow.withdraw()
        dest = filedialog.askopenfilename()
        TkWindow.destroy()
        return dest

    while True:
        obj = CryptoFile(data_dir)
        print('1. Encrypt a folder.\n2. Decrypt a folder.\n3. Decrypt single file.')
        n = int(input('Select: '))
        
        if n == 1:
            print('Opening filechooser...')
            dest = openFolder()
            print('Selected path: ', dest)
            tag = dest[dest.rfind('/')+1 if dest.rfind('/')!=-1 else 0:]
            obj.encrypt(dest, tag = tag)

        if n == 2:
            obj.decrypt()
        
        if n==3:
            filep = openFile()
            print(f'Selected path: {filep}')
            key_f = openFile()
            print(key_f)
            key = None
            with open(key_f, 'rb') as rfile:
                key = rfile.read()
            decrypt_file(filep, key, filep)
        print('Complete')


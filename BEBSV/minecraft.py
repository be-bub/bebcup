import os
import requests
import pyzipper
import subprocess
import psutil

class Updater:
    def __init__(self):
        self.base_url = "https://github.com/be-bub/bebcup/raw/main/BEBLS/"
        self.zip_filename = "launch.zip"
        self.executable_name = "launcher.exe"
        self.lsvers_url = "https://raw.githubusercontent.com/be-bub/bebcup/main/lsvers.txt"
        self.lsvers_local_path = "launcher/conservation/lsvers.txt"

    def run(self):
        try:
            if not self.check_lsvers_values():
                self.download_and_extract()
                self.update_text_files(self.lsvers_local_path, self.lsvers_url)
                self.close_existing_processes(self.executable_name)
                self.run_executable()
            else:
                self.close_existing_processes(self.executable_name)
                self.run_executable()
        except Exception as e:
            print(f"An error occurred: {e}")

    def check_lsvers_values(self):
        local_version = self.read_from_file(self.lsvers_local_path)
        remote_version = self.read_from_github(self.lsvers_url)

        if local_version != remote_version:
            self.update_text_files(self.lsvers_local_path, self.lsvers_url)
            return False

        return True

    def read_from_file(self, filename):
        try:
            with open(filename, "r") as file:
                content = file.read()
            return content
        except Exception as e:
            print(f"Error reading file {filename}: {str(e)}")
            return None

    def read_from_github(self, url):
        try:
            response = requests.get(url)
            return response.text.strip()
        except Exception as e:
            print(f"Error reading from GitHub: {str(e)}")
            return None

    def update_text_files(self, filename, url):
        try:
            github_text = self.read_from_github(url)
            with open(filename, "w") as file:
                file.write(github_text)
        except Exception as e:
            print(f"Error updating text file {filename}: {str(e)}")

    def download_and_extract(self):
        try:
            response = requests.get(self.base_url + self.zip_filename)
            with open(self.zip_filename, "wb") as file:
                file.write(response.content)
            self.extract_with_password()
            os.remove(self.zip_filename)
        except Exception as e:
            print(f"An error occurred during download and extraction: {e}")

    def extract_with_password(self):
        try:
            with pyzipper.AESZipFile(self.zip_filename, 'r', compression=pyzipper.ZIP_LZMA) as zfile:
                password = "!(@&F^G8127g1".encode('utf-8')
                zfile.pwd = password
                zfile.extractall()
        except Exception as e:
            print(f"An error occurred during extraction: {e}")

    def run_executable(self):
        try:
            subprocess.Popen([self.executable_name], shell=True)
        except Exception as e:
            print(f"An error occurred during executable run: {e}")

    def close_existing_processes(self, process_name):
        try:
            current_process = psutil.Process(os.getpid())
            for process in psutil.process_iter(attrs=['pid', 'name']):
                if process.info['name'] == process_name and process.info['pid'] != current_process.pid:
                    psutil.Process(process.info['pid']).terminate()
        except Exception as e:
            print(f"An error occurred during process termination: {e}")

if __name__ == "__main__":
    updater = Updater()
    updater.run()

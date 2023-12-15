from    p3lib.uio import UIO
from    p3lib.bokeh_auth import CredentialsManager 

def main():
    hashFile = "/tmp/ws_credentials.json"
    uio = UIO()
    credentialsManager = CredentialsManager(uio, hashFile)
    credentialsManager.manage()

if __name__ == '__main__':
    main()
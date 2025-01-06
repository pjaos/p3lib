import json
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode

class CryptFile(object):
    """@brief Responsible for encrypting and decrypting data to/from files using a password."""

    def __init__(self,
                 filename: str,
                 password: str,
                 add_enc_extension: bool = True,
                 dict_data: bool = True):
        """@brief Constructor
           @param filename The filename to save the data into.
           @param password The password to used encrypt data to and load encrypted data from file.
           @param add_enc_extension If True then the .enc extension is added to the filename
                                    supplied.
           @param dict_data If True the data is a python dictionary."""
        self._filename = filename
        self._password = password
        self._add_enc_extension = add_enc_extension
        self._dict_data = dict_data

        if not self._filename:
            raise Exception("No filename defined to save data to.")

        if len(self._filename) < 1:
            raise Exception("No filename defined. String length = 0.")

        if not self._password:
            raise Exception("No password defined to encrypt/decrypt data.")

        if len(self._password) < 1:
            raise Exception("No password defined. String length = 0.")

        self._add_extension()

    def save(self,
             data):
        """@brief Save the data to an encrypted file.
           @param data The data to be encrypted.
        """
        encrypted_data = self._encrypt_data(data)
        with open(self._filename, "wb") as file:
            file.write(encrypted_data)

    def load(self):
        """@brief Load data from an encrypted file.
           @return The decrypted data.
        """
        with open(self._filename, "rb") as file:
            data_bytes = file.read()
        return self._decrypt_data(data_bytes)

    def _decrypt_data(self, encrypted_data):
        # Extract the salt (first 16 bytes) from the encrypted data
        salt = encrypted_data[:16]
        encrypted_content = encrypted_data[16:]
        key = self._derive_key_from_password(salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_content)
        if self._dict_data:
             # Convert bytes back to a dict
            data = json.loads(decrypted_data.decode())

        else:
            data = decrypted_data

        return  data

    def get_file(self):
        """@return Get the name of the encrypted file."""
        return self._filename

    def _add_extension(self):
        """@brief Add the enc extension to the filename if required."""
        if self._add_enc_extension and self._filename and not self._filename.endswith('.enc') :
            self._filename = self._filename + ".enc"

    def _derive_key_from_password(self,
                                  salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend(),
        )
        return urlsafe_b64encode(kdf.derive(self._password.encode()))

    def _encrypt_data(self,
                      data):
        # Generate a random salt for key derivation
        salt = os.urandom(16)
        key = self._derive_key_from_password(salt)
        fernet = Fernet(key)
        # If we expect a dict
        if self._dict_data:
            data_bytes = json.dumps(data).encode()  # Convert JSON to bytes

        # else check we have bytes
        elif isinstance(data, bytes):
            data_bytes = data

        else:
            raise Exception("data to be stored is not a bytes instance.")

        encrypted_data = fernet.encrypt(data_bytes)
        return salt + encrypted_data  # Store the salt with the encrypted data

# Example usage
if __name__ == "__main__":

    password = input("Enter a password for encryption: ")

    # JSON data to encrypt
    json_data = {
        "name": "Alice",
        "age": 30,
        "is_admin": True,
        "preferences": {
            "theme": "dark",
            "language": "English"
        }
    }

    filename = "afile.txt"

    # Save and load a python dict
    cjf = CryptFile(filename=filename,
                password=password)
    cjf.save(json_data)
    print(f"Saved {cjf.get_file()}")

    decrypted_data = cjf.load()
    print(f"Decrypted data: {decrypted_data}")


    # Save and load data bytes
    data_bytes = "123".encode()
    cjf = CryptFile(filename=filename,
                    password=password,
                    dict_data=False)
    cjf.save(data_bytes)
    print(f"Saved {cjf.get_file()}")

    decrypted_data = cjf.load()
    print("Decrypted data:")
    for _byte in decrypted_data:
        print(f"_byte={_byte}")
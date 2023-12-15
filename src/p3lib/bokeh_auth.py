'''

This file is a modified version of the Bokeh authorisation example code.
Many thanks to bokeh for this.

'''
import os
import json
import tornado
from   tornado.web import RequestHandler
from   argon2 import PasswordHasher
from   argon2.exceptions import VerificationError

# could define get_user_async instead
def get_user(request_handler):
    user = request_handler.get_cookie("user")
    return user

# could also define get_login_url function (but must give up LoginHandler)
login_url = "/login"

# optional login page for login_url
class LoginHandler(RequestHandler):

    def get(self):
        try:
            errormessage = self.get_argument("error")
        except Exception:
            errormessage = ""
        self.render("login.html", errormessage=errormessage)
        
    def set_credentials(self, credHasher):
        """@brief Set the object that has details of the valid usernames and passwords."""
        self._credHasher = credHasher

    def check_permission(self, username, password):
        """@brief Check if we the username and password are valid
           @return True if the username and password are valid."""
        valid = False
        # If we have details of the valid usernames and passwords.
        if hasattr(self, '_credHasher'):
            if self._credHasher.valid(username, password):
                valid = True
        return valid

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth = self.check_permission(username, password)
        if auth:
            self.set_current_user(username)
            self.redirect("/")
        else:
            error_msg = "?error=" + tornado.escape.url_escape("Login incorrect")
            self.redirect(login_url + error_msg)

    def set_current_user(self, user):
        if user:
            self.set_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")

# optional logout_url, available as curdoc().session_context.logout_url
logout_url = "/logout"

# optional logout handler for logout_url
class LogoutHandler(RequestHandler):

    def get(self):
        self.clear_cookie("user")
        self.redirect("/")

class CredentialsHasherExeption(Exception):
    pass


class CredentialsHasher(object):
    """@brief Responsible for storing hashed credentials to a local file.
              There are issues storing hashed credentials and so this is not 
              recommended for high security systems but is aimed at providing 
              a simple credentials storage solution for Bokeh servers."""
              
    def __init__(self, userHashFile):
        """@brief Construct an object that can be used to generate a credentials has file and check 
                  credentials entered by a user. 
           @param userHashFile A file that contains the hashed (via argon2) login credentials."""
        self._userHashFile = userHashFile
        self._passwordHasher = PasswordHasher()
        self._credDict = self._getCredDict()
        
    def _getCredDict(self):
        """@brief Get a dictionary containing the current credentials.
           @return A dict containing the credentials. 
                   value = username
                   key = hashed password."""
        credDict = {}
        # If the hash file exists
        if os.path.isfile(self._userHashFile):
            # Add the hash a a line in the file 
            with open(self._userHashFile, 'r') as fd:
                contents = fd.read()
            credDict = json.loads(contents)
        return credDict
                
    def isUsernameAvailable(self, username):
        """@brief Determine if the username is not already used.
           @param username The login username.
           @return True if the username is not already used."""
        usernameAvailable = True
        if username in self._credDict:
            usernameAvailable = False
        return usernameAvailable
        
    def _saveCredentials(self):
        """@brief Save the cr3edentials to the file."""
        with open(self._userHashFile, 'w', encoding='utf-8') as f:
            json.dump(self._credDict, f, ensure_ascii=False, indent=4)
                
    def add(self, username, password):
        """@brief Add credential to the stored hashes.
           @param username The login username.
           @param password The login password."""
        if self.isUsernameAvailable(username):
            hash = self._passwordHasher.hash(password)
            self._credDict[username] = hash
            self._saveCredentials()
            
        else:
            raise CredentialsHasherExeption(f"{username} username is already in use.")
        
    def remove(self, username):
        """@brief Remove a user from the stored hashes.
                  If the username is not present then this method will return without an error.
           @param username The login username.
           @return True if the username/password was removed"""
        removed = False        
        if username in self._credDict:
            del self._credDict[username]
            self._saveCredentials()
            removed = True
        return removed
        
    def verify(self, username, password):
        """@brief Check the credentials are valid and stored in the hash file.
           @param username The login username.
           @param password The login password.
           @return True if the username and password are authorised."""
        validCredential = False
        if username in self._credDict:
            storedHash = self._credDict[username]
            try:
                self._passwordHasher.verify(storedHash, password)
                validCredential = True
                
            except VerificationError:
                pass        
        
        return validCredential
                
    def getCredentialCount(self):
        """@brief Get the number of credentials that are stored.
           @return The number of credentials stored."""
        return len(self._credDict.keys())    
    
    def getUsernameList(self):
        """@brief Get a list of usernames.
           @return A list of usernames."""
        return list(self._credDict.keys())    

class CredentialsManager(object):
    """@brief Responsible for allowing the user to add and remove credentials to a a local file."""
    
    def __init__(self, uio, userHashFile):
        """@brief Constructor.
           @param uio A UIO instance that allows user input output.
           @param userHashFile A file that contains the hashed (via argon2) login credentials."""
        self._uio = uio
        self._userHashFile = userHashFile
        self.credentialsHasher = CredentialsHasher(self._userHashFile)
        
    def _add(self):
        """@brief Add a username/password to the list of credentials."""
        self._uio.info('Add a username/password')
        username = self._uio.getInput('Enter the username: ')
        if self.credentialsHasher.isUsernameAvailable(username):
            password = self._uio.getInput('Enter the password: ')
            self.credentialsHasher.add(username, password)
        else:
            self._uio.error(f"{username} is already in use.")
    
    def _delete(self):
        """@brief Delete a username/password from the list of credentials."""
        self._uio.info('Delete a username/password')
        username = self._uio.getInput('Enter the username: ')
        if not self.credentialsHasher.isUsernameAvailable(username):
            if self.credentialsHasher.remove(username):
                self._uio.info(f"Removed {username}")
            else:
                self._uio.error(f"Failed to remove {username}.")
            
        else:
            self._uio.error(f"{username} not found.")
        
    def _check(self):
        """@brief Check a username/password from the list of credentials."""
        self._uio.info('Check a username/password')
        username = self._uio.getInput('Enter the username: ')
        password = self._uio.getInput('Enter the password: ')
        if self.credentialsHasher.verify(username, password):
            self._uio.info(f"The username and password match.")
        else:
            self._uio.error(f"The username and password do not match.")
        
    def _showUsernames(self):
        """@brief Show the user a list of the usernames stored."""
        table = [["USERNAME"]]
        for username in self.credentialsHasher.getUsernameList():
            table.append([username])
        self._uio.showTable(table)
        
    def manage(self):
        """@brief Allow the user to add and remove user credentials from a local file."""
        while True:
            self._uio.info("")
            self._showUsernames()
            self._uio.info(f"{self.credentialsHasher.getCredentialCount()} credentials stored in {self._userHashFile}")
            self._uio.info("")
            self._uio.info("A - Add a username/password.")
            self._uio.info("D - Delete a username/password.")
            self._uio.info("C - Check a username/password is stored.")
            self._uio.info("Q - Quit.")
            response = self._uio.getInput('Enter one of the above options: ')
            response = response.upper()
            if response == 'A':
                self._add()
            elif response == 'D':
                self._delete()
            elif response == 'C':
                self._check()
            elif response == 'Q':
                return
            else:
                self._uio.error(f"{response} is an invalid response.")
        
        
        
        
        
    
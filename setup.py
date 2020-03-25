import setuptools

MODULE_NAME="p3lib"                                                             #The python module name
VERSION = "1.0"                                                                 #The version of the application
AUTHOR  = "Paul Austen"                                                         #The name of the applications author
AUTHOR_EMAIL = "pausten.os@gmail.com"                                           #The email address of the author
DESCRIPTION = "A number of python3 library modules."                            # A short description of the application
PYTHON_VERSION = 3                                                              #The python applications version
LICENSE = "MIT License"	                                                        #The License that the application is distributed under
REQUIRED_LIBS = []                                                              #A python list of required libs (optionally including versions, E.G 'pjalib>=3.3')

with open("README.md", "r") as fh:
    long_description = fh.read()

#sudo apt-get install libffi-dev
#sudo pip3 install pipenv --force-reinstall
setuptools.setup(
    name=MODULE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description="", #This will be read from the README.md file
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: %d" % (PYTHON_VERSION),
        "License :: %s" % (LICENSE),
        "Operating System :: OS Independent",
    ],
    install_requires=[
        REQUIRED_LIBS
    ],
)

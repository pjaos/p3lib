#!/usr/bin/env python3

import  os
import  sys
import  platform
import  getpass

from    subprocess import check_call, DEVNULL, STDOUT, Popen, PIPE
from    datetime import datetime

class BootManager(object):
    """Responsible for adding and removing startup processes (python programs) when the computer boots.
       Currently supports the following platforms
       Linux"""

    LINUX_OS_NAME       = "Linux"
    ENABLE_CMD_OPT      = "--enable_auto_start"
    DISABLE_CMD_OPT     = "--disable_auto_start"
    CHECK_CMD_OPT       = "--check_auto_start"

    @staticmethod
    def AddCmdArgs(parser):
        """@brief Add cmd line arguments to enable, disable and show the systemd boot state.
           @param parser An instance of argparse.ArgumentParser."""
        parser.add_argument(BootManager.ENABLE_CMD_OPT,  help="Auto start when this computer starts.", action="store_true", default=False)
        parser.add_argument(BootManager.DISABLE_CMD_OPT, help="Disable auto starting when this computer starts.", action="store_true", default=False)
        parser.add_argument(BootManager.CHECK_CMD_OPT,   help="Check the status of an auto started icons_gw instance.", action="store_true", default=False)

    @staticmethod
    def HandleOptions(uio, options, enable_syslog, serviceName=None, restartSeconds=1):
        """@brief Handle one of the bot manager command line options if the 
                  user passed it on the cmd line.
           @param uio A UIO instance.
           @param options As returned from parser.parse_args() where parser 
                          is an instance of argparse.ArgumentParser.
           @param enable_syslog True to enable systemd syslog output.
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used.
           @param restartSeconds The number of seconds to sleep before restarting a service that has stopped (default=1).
           @return True if handled , False if not."""
        handled = False
        if options.check_auto_start:
            BootManager.CheckAutoStartStatus(uio, serviceName)
            handled = True
            
        elif options.enable_auto_start:
            BootManager.EnableAutoStart(uio, enable_syslog, serviceName, restartSeconds)
            handled = True
            
        elif options.disable_auto_start:
            BootManager.DisableAutoStart(uio, serviceName)
            handled = True

        return handled

    @staticmethod
    def EnableAutoStart(uio, enable_syslog, serviceName, restartSeconds):
        """@brief Enable this program to auto start when the computer on which it is installed starts.
           @param uio A UIO instance.
           @param options As returned from parser.parse_args() where parser 
                          is an instance of argparse.ArgumentParser.
           @param enable_syslog True to enable systemd syslog output.
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used.
           @param restartSeconds The number of seconds to sleep before restarting a service that has stopped (default=1)."""
        bootManager = BootManager(uio=uio, ensureRootUser=True, serviceName=serviceName, restartSeconds=restartSeconds)
        arsString = " ".join(sys.argv)
        bootManager.add(argString=arsString, enableSyslog=enable_syslog)

    @staticmethod
    def DisableAutoStart(uio, serviceName):
        """@brief Enable this program to auto start when the computer on which it is installed starts.
           @param uio A UIO instance.
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used."""
        bootManager = BootManager(uio=uio, ensureRootUser=True, serviceName=serviceName)
        bootManager.remove()
        
    @staticmethod
    def CheckAutoStartStatus(uio, serviceName):
        """@brief Check the status of a process previously set to auto start.
           @param uio A UIO instance.
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used."""
        bootManager = BootManager(uio=uio, serviceName=serviceName)
        lines = bootManager.getStatus()
        if lines and len(lines) > 0:
            for line in lines:
                uio.info(line)
        
    def __init__(self, uio=None, allowRootUser=True, ensureRootUser=False, serviceName=None, restartSeconds=1):
        """@brief Constructor
           @param uio A UIO instance to display user output. If unset then no output
                  is displayed to user.
           @param allowRootUser If True then allow root user to to auto start
                  programs. Note that as the BootManager is responsible for 
                  ensuring programs are started up when a machine boots up 
                  the installed program should be installed for the root 
                  user on Linux systems.
           @param ensureRootUser If True the current user must be root user (Linux systems).
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used.
           @param restartSeconds The number of seconds to sleep before restarting a service that has stopped (default=1)."""
        self._uio = uio
        self._allowRootUser=allowRootUser
        self._osName = platform.system()
        self._platformBootManager = None
        if self._osName == BootManager.LINUX_OS_NAME:
            self._platformBootManager = LinuxBootManager(uio, self._allowRootUser, ensureRootUser, serviceName, restartSeconds)
        else:
            raise Exception("{} is an unsupported OS.".format(self._osName) )

    def add(self, user=None, argString=None, enableSyslog=False):
        """@brief Add an executable file to the processes started at boot time.
           @param exeFile The file/program to be executed. This should be an absolute path.
           @param user The user that will run the executable file. If left as None then the current user will be used.
           @param argString The argument string that the program is to be launched with.
           @param enableSyslog If True enable stdout and stderr to be sent to syslog."""
        if self._platformBootManager:
            self._platformBootManager.add(user, argString, enableSyslog)

    def remove(self):
        """@brief Remove an executable file to the processes started at boot time.
           @param exeFile The file/program to be removed. This should be an absolute path.
           @param user The Linux user that will run the executable file."""
        if self._platformBootManager:
            self._platformBootManager.remove()
            
    def getStatus(self):
        """@brief Get a status report.
           @return Lines of text indicating the status of a previously started process."""
        statusLines = []
        if self._platformBootManager:
            statusLines = self._platformBootManager.getStatusLines()
        return statusLines
        

class LinuxBootManager(object):
    """@brief Responsible for adding/removing Linux services using systemd."""

    LOG_PATH            ="/var/log"
    ROOT_SERVICE_FOLDER = "/etc/systemd/system/"
    SYSTEM_CTL_1        = "/bin/systemctl"
    SYSTEM_CTL_2        = "/usr/bin/systemctl"

    @staticmethod
    def GetSystemCTLBin():
        """@brief Get the location of the systemctl binary file on this system.
           @return The systemctl bin file."""
        binFile = None
        if os.path.isfile(LinuxBootManager.SYSTEM_CTL_1):
            binFile = LinuxBootManager.SYSTEM_CTL_1
        elif os.path.isfile(LinuxBootManager.SYSTEM_CTL_2):
            binFile = LinuxBootManager.SYSTEM_CTL_2
        else:
            raise Exception("Failed to find the location of the systemctl bin file on this machine.")
        return binFile

    @staticmethod
    def GetServiceFolder(rootUser):
        """"@brief Get the service folder to use.
            @param rootUser False if non root user.
            @return The folder that should hold the systemctl service files."""
        serviceFolder = None
        if rootUser:
            serviceFolder = LinuxBootManager.ROOT_SERVICE_FOLDER
        else:
            homeFolder = os.path.expanduser('~')
            serviceFolder = os.path.join(homeFolder, '.config/systemd/user/')
            if not os.path.isdir(serviceFolder):
                os.makedirs(serviceFolder)

        if not os.path.isdir(serviceFolder):
            raise Exception(f"{serviceFolder} folder not found.")
        return serviceFolder

    def __init__(self, uio, allowRootUser, ensureRootUser, serviceName, restartSeconds):
        """@brief Constructor
           @param uio A UIO instance to display user output. If unset then no output is displayed to user.
           @param allowRootUser If True then allow root user to to auto start programs.
           @param ensureRootUser If True the current user must be root user.
           @param serviceName The name of the service. If not set then the name of the initially executed 
                              python file is used.
           @param restartSeconds The number of seconds to sleep before restarting a service that has stopped."""
        self._uio = uio
        self._logFile = None
        self._allowRootUser=allowRootUser
        self._info("OS: {}".format(platform.system()) )
        self._rootMode = False # If True run as root, else False.
        self._systemCtlBin = LinuxBootManager.GetSystemCTLBin()
        if ensureRootUser and os.geteuid() != 0:
            self._fatalError(self.__class__.__name__ + ": Not root user. Ensure that you are root user and try again.")

        if os.geteuid() == 0:
            if not allowRootUser:
                self._fatalError(self.__class__.__name__ + f": You are running as root user but allowRootUser={allowRootUser}.")
            else:
                self._rootMode = True
        if not self._rootMode:
            self._cmdLinePrefix = self._systemCtlBin + " --user"
        else:
            self._cmdLinePrefix = self._systemCtlBin
        self._username = getpass.getuser()
        self._serviceFolder = LinuxBootManager.GetServiceFolder(self._rootMode)
        self._serviceName = serviceName
        self._restartSeconds = restartSeconds

    def _getInstallledStartupScript(self):
        """@brief Get the startup script full path. The startup script must be
                  named the same as the python file executed without the .py suffix.
           @return The startup script file (absolute path)."""""
        startupScript=None
        argList = sys.argv
        # If the first argument in the arg is a file.
        if len(argList) > 0:
            firstArg = argList[0]
            if os.path.isfile(firstArg) or os.path.islink(firstArg):
                startupScript = firstArg
        if startupScript is None:
            raise Exception("Failed to find the startup script.")
        return startupScript

    def _getPaths(self):
        """@brief Get a list of the paths from the PATH env var.
           @return A list of paths or None if PATH env var not found."""
        pathEnvVar = os.getenv("PATH")
        envPaths = pathEnvVar.split(os.pathsep)
        return envPaths

    def _fatalError(self, msg):
        """@brief Record a fatal error.
           @param msg The message detailing the error."""
        raise Exception(msg)

    def _info(self, msg):
        """@brief Display an info level message to the user
           @param msg The message to be displayed."""
        self._log(msg)
        if self._uio:
            self._uio.info(msg)

    def _error(self, msg):
        """@brief Display an error level message to the user
           @param msg The message to be displayed."""
        self._log(msg)
        if self._uio:
            self._uio.error(msg)

    def _log(self, msg):
        """@brief Save a message to the log file.
           @param msg The message to save"""
        if self._logFile:
            timeStr = datetime.now().strftime("%d/%m/%Y-%H:%M:%S.%f")
            fd = open(self._logFile, 'a')
            fd.write("{}: {}\n".format(timeStr, msg) )
            fd.close()

    def _runLocalCmd(self, cmd):
        """@brief Run a command
           @param cmd The command to run.
           @return The return code of the external cmd."""
        self._log("Running: {}".format(cmd) )
        check_call(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)

    def _getApp(self):
        """@brief Get details of the app to run
           @return a tuple containing
                  0 = The name of the app
                  1 = The absolute path to the app to run"""
        exeFile = self._getInstallledStartupScript()
        exePath = os.path.dirname(exeFile)
        if len(exePath) == 0:
            self._fatalError("{} is invalid as executable path is undefined.".format(exeFile) )

        if not os.path.isdir(exePath):
            self._fatalError("{} path not found".format(exePath))

        appName = os.path.basename(exeFile)
        if len(appName) == 0:
            self._fatalError("No app found to execute.")

        absApp = os.path.join(exePath, appName)
        if not os.path.isfile( absApp ):
            self._fatalError("{} file not found.".format(absApp) )

        appName = appName.replace(".py", "")
        if self._rootMode:
            # We can only save to /var/log/ is we are root user.
            self._logFile = os.path.join(LinuxBootManager.LOG_PATH, appName)

        return (appName, absApp)

    def _getServiceName(self):
        """@brief Get the name of the service.
           @return The name of the service."""
        if self._serviceName:
            serviceName = self._serviceName
        else:
            appName, _ = self._getApp()
            serviceName = appName
        return "{}.service".format(serviceName)

    def _getServiceFile(self, appName):
        """@brief Get the name of the service file.
           @param appName The name of the app to execute.
           @return The absolute path to the service file """
        serviceName = self._getServiceName()
        serviceFile = os.path.join(self._serviceFolder, serviceName)
        self._uio.info(f"SERVICE FILE: {serviceFile}")
        return serviceFile

    def add(self, user, argString=None, enableSyslog=False):
        """@brief Add an executable file to the processes started at boot time.
                  This will also start the process. The executable file must be
                  named the same as the python file executed without the .py suffix.
           @param user The Linux user that will run the executable file.
                       This should not be root as config files will be be saved
                       to non root user paths on Linux systems and the startup
                       script should then be executed with the same username in
                       order that the same config file is used.
                       If set to None then the current user is used.
           @param argString The argument string that the program is to be launched with.
           @param enableSyslog If True enable stdout and stderr to be sent to syslog."""
        if user is None:
            user = self._username

        appName, absApp = self._getApp()
        serviceName = self._getServiceName()

        serviceFile = self._getServiceFile(serviceName)

        lines = []
        lines.append("[Unit]")
        lines.append("After=network.target")
        lines.append("StartLimitIntervalSec=0")
        lines.append("")
        lines.append("[Service]")
        lines.append("Type=simple")
        lines.append("Restart=always")
        lines.append(f"RestartSec={self._restartSeconds}")
        if enableSyslog:
            lines.append("StandardOutput=syslog")
            lines.append("StandardError=syslog")
        else:
            lines.append("StandardOutput=null")
            lines.append("StandardError=journal")
        if self._rootMode and user != 'root':
            lines.append("User={}".format(user))

        #We add the home path env var so that config files (if stored in/under 
        # the users home dir) can be found by the prgram.
        if user and len(user) > 0:
            lines.append('Environment="HOME=/home/{}"'.format(user))
        if argString:
            argString = argString.strip()
            if argString.startswith(absApp):
                argString=argString.replace(absApp, "")
            # We don't want the enable cmd opt in the cmd we add to the systemd file.
            if argString.find(BootManager.ENABLE_CMD_OPT):
                argString = argString.replace(BootManager.ENABLE_CMD_OPT, "")
            argString = argString.strip()
            lines.append("ExecStart={} {}".format(absApp, argString))
        else:
            lines.append("ExecStart={}".format(absApp))
        lines.append("")
        lines.append("[Install]")
        lines.append("WantedBy=multi-user.target")
        lines.append("")

        try:
            fd = open(serviceFile, 'w')
            fd.write( "\n".join(lines) )
            fd.close()
            self._info(f"Created {serviceFile}")
        except IOError:
            self._fatalError("Failed to create {}".format(serviceFile) )

        cmd = "{} daemon-reload".format(self._cmdLinePrefix)
        self._runLocalCmd(cmd)
        cmd = "{} enable {}".format(self._cmdLinePrefix, serviceName)
        self._info("Enabled {} on restart".format(serviceName))
        self._runLocalCmd(cmd)
        cmd = "{} start {}".format(self._cmdLinePrefix, serviceName)
        self._runLocalCmd(cmd)
        self._info("Started {}".format(serviceName))

    def remove(self):
        """@brief Remove the executable file to the processes started at boot time.
                  Any running processes will be stopped.  The executable file must be
                  named the same as the python file executed without the .py suffix."""
        appName, _ = self._getApp()

        serviceName = self._getServiceName()
        serviceFile = self._getServiceFile(appName)
        if os.path.isfile(serviceFile):
            cmd = "{} disable {}".format(self._cmdLinePrefix, serviceName)
            self._runLocalCmd(cmd)
            self._info("Disabled {} on restart".format(serviceName))

            cmd = "{} stop {}".format(self._cmdLinePrefix, serviceName)
            self._runLocalCmd(cmd)
            self._info("Stopped {}".format(serviceName))

            os.remove(serviceFile)
            self._log("Removed {}".format(serviceFile))
        else:
            self._info("{} service not found".format(serviceName))

    def getStatusLines(self):
        """@brief Get a status report.
           @return Lines of text indicating the status of a previously started process."""
        serviceName = self._getServiceName()
        if self._rootMode:
            p = Popen([self._systemCtlBin, 'status', serviceName], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([self._systemCtlBin, '--user', 'status', serviceName], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate(b"input data that is passed to subprocess' stdin")
        response = output.decode() + "\n" + err.decode()
        lines = response.split("\n")
        return lines

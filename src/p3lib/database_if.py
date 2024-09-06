#!/usr/bin/env python

import  MySQLdb as mysqldb
from    datetime import datetime

class DBConfig(object):
    """@brief responsible for holding the attributes if the database configuration."""

    DEFAULT_TCP_PORT = 3306

    def __init__(self):
        self.serverAddress      =   ""
        self.serverPort         =   DBConfig.DEFAULT_TCP_PORT
        self.username           =   ""
        self.password           =   ""
        self.dataBaseName       =   ""
        self.uio                =   None

class DatabaseIFError(Exception):
  pass

class DatabaseIF(object):
    """@brief Responsible for providing an interface to a database to allow
              Creation of database
              Creation of tables
              Execution of database sql commands
              """

    """@brief Set this to True to see the SQL statements executed."""
    DEBUG=False

    @staticmethod
    def CheckTableExists(connection, tableName):
        """@brief Check if a table exists in the selected database.
           @param connection The connection to the database.
           @param tableName The name of the table to check for.
           @return True if the table exists, False if not."""
        cursor = connection.cursor()
        cmd="""SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{0}'""".format(tableName.replace('\'', '\'\''))
        cursor.execute(cmd)
        tableExists = cursor.fetchone()[0] == 1
        cursor.close()
        return tableExists

    @staticmethod
    def GetValidColName(colName):
        """@brief Get a valid database column name."""

        VALID_CHAR_LIST = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$_"
        for aChar in colName:
            if aChar not in VALID_CHAR_LIST:
                colName = colName.replace(aChar, '_')

        return colName

    @staticmethod
    def CreateTable(connection, tableName, tableSchemaDict):
        """"@brief Create a table in the currently USED database..
            @param connection The connection to the database.
            @param param:
            @param tableSchemaDict A python dictionary that defines the table schema.
                                   Each dictionary key is the name of the column in the table.
                                   Each associated value is the SQL definition of the column type (E.G VARCHAR(64), FLOAT(5,2) etc)."""
        cursor = connection.cursor()

        sqlCmd = 'CREATE TABLE IF NOT EXISTS `{}` ('.format(tableName)
        for colName in list(tableSchemaDict.keys()):
            colDef = tableSchemaDict[colName]
            correctedColName = DatabaseIF.GetValidColName(colName)
            sqlCmd = sqlCmd + "`{}` {},\n".format(correctedColName, colDef)

        sqlCmd = sqlCmd[:-2]
        sqlCmd = sqlCmd + ");"
        DatabaseIF.ExecuteSQL(connection, cursor, sqlCmd)
        cursor.close()

    @staticmethod
    def GetQuotedValue(value):
        return '\"{}"'.format(str(value))

    @staticmethod
    def InsertRow(connection, tableName, myDict):
        """@brief Insert a row into the table."""
        cursor = connection.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        myDict['TIMESTAMP'] = timestamp

        keyList = list(myDict.keys())
        valueList = []
        for key in keyList:
            valueList.append(str(myDict[key]))

        sql = 'INSERT INTO `' + tableName
        sql += '` ('
        sql += ', '.join(keyList)
        sql += ') VALUES ('
        sql += ', '.join(map(DatabaseIF.GetQuotedValue, valueList))
        sql += ');'
        DatabaseIF.ExecuteSQL(connection, cursor, sql)
        cursor.close()

    @staticmethod
    def ExecuteSQL(connection, cursor, cmd):
        try:
            if DatabaseIF.DEBUG:
                print('ExecuteSQL(): ',cmd)
            rowsAffected = cursor.execute(cmd)
            connection.commit()
        except:
            connection.rollback();
            raise

        return rowsAffected

    @staticmethod
    def GetInsertableDict(self, rxDict, tableSchema):
        """@brief Convert the dict into a dict that can be stored in the database.
                  All the keys must have names that only contain characters that are valid for table columns.
                  Only those keys that are in the tableSchema will be inserted."""
        keys = list(rxDict.keys())
        convertedDict = {}
        for key in keys:
            colName = DatabaseIF.GetValidColName(key)
            #Only add the keys that we wish to store in the database
            if colName in list(tableSchema.keys()):
                convertedDict[colName] = rxDict[key]
        return convertedDict

    def __init__(self, config):
        """@brief Constructor
           @param config The database configuration instance."""
        self._dbConfig = config

        self._dbCon = None

    def _info(self, msg):
        if self._dbConfig.uio:
            self._dbConfig.uio.info(msg)


    def _debug(self, msg):
        if self._dbConfig.uio and self._dbConfig.uio.debug:
            self._dbConfig.uio.debug(msg)

    def connect(self):
        """@brief connect to the database server."""
        self._info("Connecting to {}:{} (database = {})".format(self._dbConfig.serverAddress, self._dbConfig.serverPort, self._dbConfig.dataBaseName))
        self._dbCon = mysqldb.Connection(host=self._dbConfig.serverAddress,\
                                                port=self._dbConfig.serverPort,\
                                                user=self._dbConfig.username,\
                                                passwd=self._dbConfig.password,\
                                                db=self._dbConfig.dataBaseName)
        self._info("Connected")

    def connectNoDB(self):
        """@brief connect to the database server."""
        self._info("Connecting to database server @ {}:{}".format(self._dbConfig.serverAddress, self._dbConfig.serverPort))
        self._dbCon = mysqldb.Connection(host=self._dbConfig.serverAddress,\
                                                port=self._dbConfig.serverPort,\
                                                user=self._dbConfig.username,\
                                                passwd=self._dbConfig.password)
        self._info("Connected")

    def checkTableExists(self, tableName):
        """@brief Check if a table exists in any database.
           @param tableName The name of the table to check for.
           @return True if the table exists, False if not."""
        cursor = self._dbCon.cursor()
        cmd="""SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{0}'""".format(tableName.replace('\'', '\'\''))
        self._debug("EXECUTE SQL: {}".format(cmd))
        #self.executeSQL(cmd)
        cursor.execute(cmd)
        tableExists = cursor.fetchone()[0] == 1
        cursor.close()
        return tableExists

    def _createTable(self, tableName, tableSchemaDict):
        """"@brief Create a table in the currently used database..
            @param tableName The name of the database table.
            @param tableSchemaDict A python dictionary that defines the table schema.
                                   Each dictionary key is the name of the column in the table.
                                   Each associated value is the SQL definition of the column type (E.G VARCHAR(64), FLOAT(5,2) etc)."""
        cursor = self._dbCon.cursor()

        sqlCmd = 'CREATE TABLE IF NOT EXISTS `{}` ('.format(tableName)
        for colName in list(tableSchemaDict.keys()):
            colDef = tableSchemaDict[colName]
            correctedColName = DatabaseIF.GetValidColName(colName)
            sqlCmd = sqlCmd + "`{}` {},\n".format(correctedColName, colDef)

        sqlCmd = sqlCmd[:-2]
        sqlCmd = sqlCmd + ");"
        self.executeSQL(sqlCmd)
        cursor.close()

    def createTable(self, tableName, tableSchemaDict):
        """@brief Create the table in the connected database.
           @param tableName The table we're innterested in.
           @param tableSchemaDict The schema for the table in dict form."""
        self._createTable(tableName, tableSchemaDict)

    def getTableRowCount(self, tableName):
        """@brief Get the number of rows in a table.
           @param tableName The name of the table. 
           @return the number of rows in the table or -1 if not found."""
        count = -1
        cmd = "SELECT COUNT(*) as count from {};".format(tableName)
        retList = self.executeSQL(cmd)
        if len(retList) > 0:
            count = retList[0]['count']
        return count
    
    def deleteRows(self, tableName, rowCount):
        """@brief Delete rows from a table.
           @param tableName The name of the table. 
           @param rowCount The number of rows to delete."""
        cmd = "DELETE FROM {} LIMIT {};".format(tableName, rowCount)
        self.executeSQL(cmd)
        
    def ensureTableExists(self, tableName, tableSchemaDict, autoCreate):
        """@brief Check that the table a table exists in the database.
           @param tableName The table we're interested in.
           @param tableSchemaDict The schema for the table in dict form.
           @param autoCreate Now redundant. It used to be the case that if True then auto create the table."""
        self._createTable(tableName, tableSchemaDict)

    def insertRow(self, dataDict, tableName, tableSchemaDict):
        """@brief Insert a row into a database table.
                Must have previously connected to the database.
           @param dataDict The dict holding the table data
           @param tableName The name of the table to insert data into
           @param tableSchemaDict The schema for the database table."""
        insertableDict = DatabaseIF.GetInsertableDict(tableName, dataDict, tableSchemaDict)
        cursor = self._dbCon.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insertableDict['TIMESTAMP'] = timestamp

        keyList = list(insertableDict.keys())
        valueList = []
        for key in keyList:
            valueList.append(str(insertableDict[key]))

        sql = 'INSERT INTO `' + tableName
        sql += '` ('
        sql += ', '.join(keyList)
        sql += ') VALUES ('
        sql += ', '.join(map(DatabaseIF.GetQuotedValue, valueList))
        sql += ');'
        self.executeSQL(sql)
        cursor.close()

    def executeSQL(self, sqlCmd):
        """@brief execute an SQL cmd"""
        self._debug("EXECUTE SQL: {}".format(sqlCmd))
        dictCursor = self._dbCon.cursor(mysqldb.cursors.DictCursor)

        dictCursor.execute(sqlCmd)
        resultDict = dictCursor.fetchall()
        self._dbCon.commit()
        return resultDict

    def disconnect(self):
        """@brief Disconnect from the database server."""
        try:
            if self._dbCon:
                self._dbCon.close()
                self._dbCon = None
                self._info("Disconnected from {}:{}".format(self._dbConfig.serverAddress, self._dbConfig.serverPort))
        except:
            pass

    def createDatabase(self):
        """@brief Create the database"""
        sql = "CREATE DATABASE `{}`;".format(self._dbConfig.dataBaseName)
        self.executeSQL(sql)
        self._info("Created {} database.".format(self._dbConfig.dataBaseName))

    def dropDatabase(self):
        """@brief Delete the database"""
        sql = "DROP DATABASE `{}`;".format(self._dbConfig.dataBaseName)
        self.executeSQL(sql)
        self._info("Deleted {} database.".format(self._dbConfig.dataBaseName))

    def dropTable(self, tableName):
        """@brief Delete a table in the database
           @param tableName The table to drop."""
        sql = "DROP TABLE `{}`;".format(tableName)
        self.executeSQL(sql)
        self._info("Deleted {} database table.".format(tableName))

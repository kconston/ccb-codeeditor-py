import requests
import json
import pickle
import time
import os
from ccb.CCBDocument import CCBDocument

class CCBSession:
      ST_SESSION = 'Session'
      ST_SECURITYTOKEN = 'SecurityToken'
      ST_ERROR = 'ERROR'
      ST_WARNING = 'WARNING'
      ST_OK = 'OK'

      def __init__(self):
          self.securityToken = ""
          self.isLoggedIn = False
          self.sessionTracker = {}

      def __safeDeleteAttr(self, attrname):
          if hasattr(self, attrname):
              delattr(self, attrname)

      def _loadSession(self, uname):
          uname = uname.upper()
          self.sessionFileName = '/tmp/.' + uname + '_cesession'
          try:
              with open(self.sessionFileName, 'rb') as sessionFile:
                  self.sessionTracker = pickle.load(sessionFile)
                  self.session = self.sessionTracker[self.ST_SESSION]
                  self.securityToken = self.sessionTracker[self.ST_SECURITYTOKEN]
                  print("Security token" + self.securityToken)
                  self.isSessLoadedFromFile = True

              cookiesDict = self.session.cookies.get_dict()
              sessionExp = cookiesDict['ORA_OUAF_SESSION_EXP']
              if (time.time() * 1000 > int(sessionExp)):
                  print("session expired")
                  print(self.sessionFileName)
                  os.remove(self.sessionFileName)
                  #GH-2 fix
                  self.__safeDeleteAttr(self.session)
                  self.__safeDeleteAttr(self.securityToken)
                  self.isSessLoadedFromFile = False
          except:
              self.isSessLoadedFromFile = False

      def _saveSession(self, objectKey, objectToSave):
          self.sessionTracker[objectKey] = objectToSave
          with open(self.sessionFileName, 'wb') as sessionFile:
              pickle.dump(self.sessionTracker, sessionFile)

      def _getJsonBodyFromResponse(self, content):
          pageBodyByteCode=content[9:]
          decodedPageBody=pageBodyByteCode.decode("utf-8")
          self.pageBody=json.loads(decodedPageBody)
          return self.pageBody



      def checkSession(self, uname):
          uname = uname.upper()
          self._loadSession(uname)
          return self.isSessLoadedFromFile

      def login(self, uname, password):
          uname = uname.upper()
          self.sessionFileName = '/tmp/.' + uname + '_cesession'
          statusCode = 0

          self._loadSession(uname)

          sessionExists = False
          try:
              self.session
          except Exception as e:
              sessionExists = False
          else:
              sessionExists = True
              statusCode = 200

          if not sessionExists:
              data={'j_username': uname, 'j_password': password}
              self.session = requests.Session()
              try:
                 response = self.session.post('https://cetst.ebill.lus.org:6601/ouaf/j_security_check', data=data, timeout=5)
                 statusCode = response.status_code
                 print("login response: " + response)
              except requests.Timeout:
                  print("Connection attempt timed out")
                  statusCode = 408
                  return statusCode #Request timed out
              except:
                  print (response)
                  print ("Unknown error during login")
                  statusCode = 500
                  return statusCode

          if (statusCode == 200):
              self.isLoggedIn = True
              #Save copy of session.
              try:
                  if not self.isSessLoadedFromFile:
                      self._saveSession(objectKey=self.ST_SESSION, objectToSave=self.session)

              except Exception as e:
                  print("something went wrong trying to create session file")
                  print (str(e))
                  statusCode = 500

          return statusCode

#CCBSession - Security Token
      def getSecurityToken(self):
          print("Self security: " + self.securityToken)
          #skip if a security token for this session already exists
          #  Oracle doesnt allow a user to retrieve multiple security
          #  tokens for the same session
          if (self.securityToken != ""):
              return self.securityToken

          resp = self.session.post('https://cetst.ebill.lus.org:6601/ouaf/restSecurityToken')
          if (resp.status_code == 200):
              try:
                  self.securityToken = resp.headers['OUAF-Security-Token']
              except:
                  print("Unable to retrieve security token")
                  self.securityToken = None
              if not self.isSessLoadedFromFile:
                  self._saveSession(objectKey=self.ST_SECURITYTOKEN, objectToSave=self.securityToken)

          print(self.securityToken)
          return self.securityToken

      def readPageBody(self, scriptCode):
          payload={'SCR_CD':scriptCode, 'COPY_TO_SCR_CD':'', 'ouafSecurityToken':self.securityToken}
          headers = {'Content-Type': 'application/x-www-form-urlencoded'}
          response = self.session.post('https://cetst.ebill.lus.org:6601/ouaf/pageRead?service=CILZSCRP&ignoreWarnings=false', data=payload, headers=headers)

          if response.status_code != 200:
              return

          #if response.status_code == 400

          #Strip away while(1), then convert the body to a json object
          ccbDocument = CCBDocument()
          self._getJsonBodyFromResponse(response.content)

          if (self.pageBody['resultCode'] == "E"):
              return

          ccbDocument.addSteps(self.pageBody)


          return ccbDocument

      def savePageBody(self, saveData):
          scriptCode = self.pageBody['pageBody']['SCR_CD']
          #print(html.unescape(saveData))
          payload={'SCR_CD':'CmGroovyTest', 'COPY_TO_SCR_CD':'', 'ouafSecurityToken':self.securityToken, 'pageBody': saveData}
          headers = {'Content-Type': 'application/x-www-form-urlencoded'}
          print("\n\nAttempting to save")
          response = self.session.post('https://cetst.ebill.lus.org:6601/ouaf/pageChange?service=CILZSCRP', data=payload, headers=headers)

          if response.status_code != 200:
              print("uh-oh")
              return {'status': self.ST_ERROR, 'message': response}

          saveResponse = self._getJsonBodyFromResponse(response.content)

          if saveResponse['resultCode'] == 'W':
              return {'status': self.ST_WARNING, 'message': saveResponse['serverWarnings']}

          return {'status': self.ST_OK, 'message': saveResponse}



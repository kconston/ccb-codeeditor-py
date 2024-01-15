import getpass
import os
import hashlib 
import subprocess
from ccb.CCBSession import CCBSession
from converters import pageBodyJsonToXML as bodyConverter

def clearScreen():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')
        
ccbSession = CCBSession()
"securityToken = ccbSession.getSecurityToken()"
securityToken = ""
userInput = ""
scriptUpdated = False
saveData = ""
scriptName = ""
saveResponse = {'status': ccbSession.ST_OK, 'message': None }
stepData = {}
ccbDocument = None
stepChangeTracker = {}

def login():
    while True: 
        uname = input("Username: ")
        sessionLoaded = ccbSession.checkSession(uname)
        if sessionLoaded:
            break
        password = getpass.getpass("Password: ")
        ccbSession.login(uname, password)
        if(ccbSession.isLoggedIn):
            break
        print("Login failed \n\n")
    

def displayScriptMenu():
    clearScreen()
    scriptName = input("Script: ")
    return scriptName
        
def displayStepsMenu(ccbSession, scriptName):
    stepChangeTracker = {}
    ccbDocument = ccbSession.readPageBody(scriptName)
    if ccbDocument is None:
        print("Unable to retrieve a valid CC&B Document")

    stepData = ccbDocument.getAllSteps()
    clearScreen()   
    
    #for key, value in stepData.items():
    #    menuDisplay = '{num:2d}'.format(num=int(key)) +  ": " +value['info']
    #    if int(key) in stepChangeTracker:
    #        if stepChangeTracker[int(key)] == True:
    #            menuDisplay = '** ' + menuDisplay 
    #        else:
    #            menuDisplay = '   ' + menuDisplay
    #    else:
    #        stepChangeTracker[int(key)] = False
    #print(menuDisplay)
    #userInput = input("\nEnter step to edit or [(q)uit, (l)oad script, (s)ave]: ")
    userInput = ""
    saveResponse = {'status': ccbSession.ST_OK, 'message': None }

    while True:
        if (userInput.upper() == 'Q'):
            break

        if (userInput.upper() == 'L'):
            displayStepsMenu(ccbSession, scriptName)
            break
            
        if (userInput.upper() == 'S'):
            saveResponse = ccbSession.savePageBody(saveData) 
            if saveResponse['status'] == ccbSession.ST_OK:
                print(scriptName + " updated successfully")
                break

        if saveResponse['status'] == ccbSession.ST_OK:
            clearScreen()
            #scriptName = input("Script: ")

            ccbDocument = ccbSession.readPageBody(scriptName)
            if ccbDocument is None:
                continue

            stepData = ccbDocument.getAllSteps()
            scriptUpdated = False
        
        while True:
            clearScreen()   
            
            if saveResponse['status'] != ccbSession.ST_OK:
                print(saveResponse['message'] + "\n\n")
                saveResponse['status'] = ccbSession.ST_OK

            for key, value in stepData.items():
                menuDisplay = '{num:2d}'.format(num=int(key)) +  ": " +value['info']
                if int(key) in stepChangeTracker:
                    if stepChangeTracker[int(key)] == True:
                        menuDisplay = '** ' + menuDisplay 
                    else:
                        menuDisplay = '   ' + menuDisplay
                else:
                    menuDisplay = '   ' + menuDisplay
                    stepChangeTracker[int(key)] = False
                print(menuDisplay)
                                
            userInput = input("\nEnter step to edit or [(q)uit, (l)oad script, (s)ave]: ")

            if (userInput.upper() == 'Q') or (userInput.upper() == 'L'):
                if scriptUpdated:
                    disregardChanges = input("You have unsaved changes.  Are you sure? (Y/N): ") 
                    if disregardChanges.upper() == 'N':
                        continue
                break

            if (userInput.upper() == 'S'):
                currentPageBody = ccbDocument.getCurrentPageBody()

                #check if editDataArea is blank for all steps.......  
                removeList = []
                for index, val in enumerate(currentPageBody['pageBody']['lists']['STEP']['list']):
                    if not val['EDIT_DATA_AREA']:
                        removeList.append(val)
                #........ remove from currentPageBody if found in the list     
                for val in removeList:
                    currentPageBody['pageBody']['lists']['STEP']['list'].remove(val)
                                
                ccbPageBodyDocument = bodyConverter.convert(currentPageBody['pageBody'], 'pageBody')
                ccbPageBodyDocumentXML = ccbPageBodyDocument.toprettyxml()

                saveData = ccbPageBodyDocumentXML
                #TODO: Remove.  Used for debugging
                #print(saveData)
                break

            os.makedirs(".groovyTmp", exist_ok=True)
            scriptFileName = ".groovyTmp/" + scriptName + userInput + ".groovy"
            scriptDataFile = open(scriptFileName, "w")
            scriptData = {}
            try:
                scriptData = stepData[userInput] 
            except:
                print("script data: ", scriptData) 
                continue

            scriptDataFile.write(scriptData['data'])
            originalHash = hashlib.md5()
            originalHash.update(str.encode(scriptData['data']))
            origDigest = originalHash.digest()

            scriptDataFile.close()
            sp = subprocess.Popen(["/bin/zsh", "-i", "-c", "vi " + scriptFileName])
            #sp = subprocess.Popen(["/bin/zsh", "-i", "-c", "code " + scriptFileName])

            sp.communicate()
            scriptDataFile = open(scriptFileName, "r")
            updatedDataAreaText = scriptDataFile.read()
            scriptDataFile.close()
            updatedHash = hashlib.md5()
            updatedHash.update(str.encode(updatedDataAreaText))
            updateDigest = updatedHash.digest()

            if (origDigest != updateDigest):
                stepChangeTracker[int(userInput)] = True
                ccbDocument.updateStep(userInput, updatedDataAreaText, scriptData['info'])
                scriptUpdated = True

if __name__ == '__main__':
    login()
    securityToken = ccbSession.getSecurityToken()
    if (securityToken == ""):
        print("Unable to retrieve a valid security token")
        exit()
    scriptName = displayScriptMenu()
    displayStepsMenu(ccbSession, scriptName)
    exit() 



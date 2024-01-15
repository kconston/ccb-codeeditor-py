import requests
import getpass
import os
import subprocess
from ccb.CCBSession import CCBSession


url = "https://cetst.ebill.lus.org:6601/ouaf/restSecurityToken"

ccbSession = CCBSession()
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

login()




url = "https://cetst.ebill.lus.org:6601/ouaf/j_security_check"

payload='j_username=KENC7086&j_password=Kconston7086'
headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': 'ORA_OUAF_Language=ENG; ORA_OUAF_Language_Dir=ltr; ORA_OUAF_Locale_Info=en-US%2CTERTIARY; ORA_OUAF_SERVER_TIME=1672943958221; ORA_OUAF_SESSION_EXP=1672972758221; JSESSIONID=0x2DOvihz9vjw_76YdqcLOXmR6lKsX_DJRxEWWfiQBvz4Cb8cVXC!497987566; _WL_AUTHCOOKIE_JSESSIONID=xZk4Qj1AJ7djo0QKPUIG'
}


response = requests.request("POST", url, headers=headers, data=payload)



url = "https://cetst.ebill.lus.org:6601/ouaf/restSecurityToken"

payload={}

response = requests.request("POST", url, headers=response.headers, data=payload)

print(response.text)
print(response.headers)

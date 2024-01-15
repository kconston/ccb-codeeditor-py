# pageBodyJsonToXML.py

import json
import xml.etree.ElementTree as ElementTree
import xml.dom.minidom as minidom
import time

def convert(jsonObj, rootElementName):
    root = minidom.Document()
    xml = root.createElement(rootElementName)
    #print(jsonObj)
    #pageBodyElement = ElementTree.Element("pageBody")
    for key in jsonObj:
        xmlElementColl = [] 
        if type(jsonObj[key]) is dict:
            #subDocument = convert(jsonObj[key], "listHeader")
            try:
                if key == 'header':
                    subDocument = convert(jsonObj[key], 'listHeader')
                else:
                    subDocument = convert(jsonObj[key]['STEP'], 'list')
            except:
                continue
            currentElement = subDocument.documentElement 
            xmlElementColl.append(currentElement)
            if key != 'header':
                currentElement.setAttribute('name', "STEP")
        elif type(jsonObj[key]) is list:
            for bodyItem in jsonObj[key]:
                try:
                    subDocument = convert(bodyItem, "listBody")   
                    currentElement = subDocument.documentElement
                    currentElement.setAttribute('action', "C")
                    xmlElementColl.append(currentElement)
                except:
                    continue
        else:
            if key == 'name' or key == 'service' :
                continue

            currentElement = root.createElement('field')
            currentElement.setAttribute('name', key)
            currentValue = jsonObj[key]
            if currentValue is None:
                currentValue = ''
            #for some reason CCB doesnt like True/False
            if str(currentValue) == "True":
                currentValue = "true"
            if str(currentValue) == "False":
                currentValue = "false"
            #if key == 'EDIT_DATA_AREA':
            #    currentValue = currentValue 
            currentElementText = root.createTextNode(str(currentValue))
            currentElement.appendChild(currentElementText)
            xmlElementColl.append(currentElement)

        for currentElement in xmlElementColl:
            xml.appendChild(currentElement)

        root.appendChild(xml)

    return root

   
    





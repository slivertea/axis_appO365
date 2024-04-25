import requests
import json
import os
import csv

#Define static values
TOKEN = os.getenv('AXIS_TOKEN')
axisUrl = "https://admin-api.axissecurity.com/api/v1.0/applications?pageSize=100&pageNumber=1"
o365Url = "https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7"
sourceO365JS = "samples/sample_o365Source.json"
sourceAxisImport_NR = "samples/sample_axisImport_NR.csv"
outputAxisImport_NR_CSV = "axisImport_NR.csv"
outputAppDestinationsCSV='output_AppsByDestinations.csv'
outputAppNamesJS='output_AppsByName.json'
outputDuplicatesJS='output_Duplicates.json'
apiToken = 'Bearer '+TOKEN
payload = ""
headers = {
    'Authorization': apiToken,
    'Content-Type': 'application/json'
}


#STEP1 - Collect existing o365 data - either online or local json input.json file
## Collect from online direct
#o365Source = (requests.request("GET", o365Url, headers=headers, data=payload).json())
#o365SourceJS = json.dumps(o365Source)
# Dump output to the sample file
#with open(sourceO365JS, 'w', encoding='utf-8') as fh:
#    json.dump(o365Source, fh, ensure_ascii=False, indent=4)
## Collect form existing sourceO365JS sample_o365Source.json by default
with open(sourceO365JS, 'r', encoding='utf-8') as fh:
    o365Source = json.load(fh)

# Breakdown the source data by destination, one row per destination
appsByDestination = []
for o365Id in o365Source:
    #print (o365Id['serviceAreaDisplayName'], o365Id.keys())
    # Destinations
    # URL
    if "urls" in o365Id.keys():
        for url in o365Id['urls']:
            appByDest= {
                "id": o365Id['id'],
                "category": o365Id['category'],
                "name": o365Id['serviceAreaDisplayName'],
                "destination": url,
                "tcpPorts": None,
                "udpPorts": None,
                "required": o365Id['required'],
                "notes": None
            }
            if "tcpPorts" in o365Id.keys():
                appByDest['tcpPorts'] = o365Id['tcpPorts']
            if "udpPorts" in o365Id.keys():
                appByDest['udpPorts'] = o365Id['udpPorts']
            if "notes" in o365Id.keys():
                appByDest['notes'] = o365Id['notes']
            appsByDestination.append(appByDest)
    # IP Address
    if "ips" in o365Id.keys():
        for iP in o365Id['ips']:
            if ":" in iP:
                () # Skip ipv6
            else:
                appByDest= {
                    "id": o365Id['id'],
                    "category": o365Id['category'],
                    "name": o365Id['serviceAreaDisplayName'],
                    "destination": iP,
                    "tcpPorts": None,
                    "udpPorts": None,
                    "required": o365Id['required'],
                    "notes": None
                }
            if "tcpPorts" in o365Id.keys():
                appByDest['tcpPorts'] = o365Id['tcpPorts']
            if "udpPorts" in o365Id.keys():
                appByDest['udpPorts'] = o365Id['udpPorts']
            if "notes" in o365Id.keys():
                appByDest['notes'] = o365Id['notes']
            appsByDestination.append(appByDest)


# Define an array of the appnames to consolidate
dupDestinations = []
appsNameList = []
for o365DisplayName in o365Source:
    if o365DisplayName['serviceAreaDisplayName'] in appsNameList:
        ()
    else:
        appsNameList.append(o365DisplayName['serviceAreaDisplayName'])

# Parse out the appnames, and consolidate destinations and ports
appsByName = []
for appName in appsNameList:
    appByName = {
        "ids": [], # numerical value to all MS Apps in the source.  For tracking only
        "categories": [], # Microsoft given category - Optimzed, Rquired/Default, Allow
        "name": appName, # Detailed display name
        "destIP": [],
        "destUrl": [],
        "tcpPorts": [],
        "udpPorts": [],
        "allPorts": [], # used for bulk import csv template
        "isIcmp": True, # Default value
        "czName": "Default Connector Zone", # Default value
        "czId": None, # applicable only in API push
        "notes": [],  # for human readability
        "tags": "MS 365 All Apps" # Default tag name
    }

    for o365Name in o365Source:
        if appName in o365Name["serviceAreaDisplayName"]:

            # Append common traits
            appByName["ids"].append(o365Name["id"])
            if o365Name["category"] in appByName["categories"]:
                ()
            else:
                appByName["categories"].append(o365Name["category"])

            if "notes" in o365Name.keys():
                appByName['notes'].append(o365Name['notes'])
            if "ips" in o365Name.keys():
                # dictionary to track duplicates - for human log readout
                dupDestination = {
                    "id": None,
                    "appName": None,
                    "category": None,
                    "ip": None,
                    "url": None
                }
                for iP in o365Name['ips']:
                    if ":" in iP:
                        () # Skip ipv6
                    else:
                        if iP in appByName['destIP']:
                            # Add to duplicates
                            dupDestination["id"] = o365Name["id"]
                            dupDestination["appName"] = o365Name["serviceAreaDisplayName"]
                            dupDestination["category"] = o365Name["category"]
                            dupDestination["ip"] = iP
                            dupDestinations.append(dupDestination)
                        else:
                            appByName['destIP'].append(iP)
            if "urls" in o365Name.keys():
                dupDestination = {
                    "id": None,
                    "ip": None,
                    "url": None
                }
                for url in o365Name["urls"]:
                    # Add to duplicates
                    ()
                else:
                    appByName['destUrl'].append(o365Name["urls"])

            # Concatenate all unique tcp ports
            if "tcpPorts" in o365Name.keys():
                tcpPortList = o365Name['tcpPorts'].split(',')
                for tcpPort in tcpPortList:

                    if (tcpPort+":tcp")in appByName['tcpPorts']:
                        ()
                    else:
                        appByName['tcpPorts'].append(tcpPort +":tcp")
                        appByName['allPorts'].append(tcpPort +":tcp")

            # Concatenate all unique udp ports
            if "udpPorts" in o365Name.keys():
                udpPortList = o365Name['udpPorts'].split(',')
                for udpPort in udpPortList:

                    if (udpPort+":udp") in appByName['udpPorts']:
                        ()
                    else:
                        appByName['udpPorts'].append(udpPort +":udp")
                        appByName['allPorts'].append(udpPort +":udp")

                    # Teams guidence recomends adding tcp as well.
                    if (udpPort+":tcp") in appByName['tcpPorts']:
                        ()
                    else:
                        appByName['tcpPorts'].append(udpPort +":tcp")
                        appByName['allPorts'].append(udpPort +":tcp")


    appsByName.append(appByName)
# Dump output to the sample file
with open(outputAppNamesJS, 'w', encoding='utf-8') as fh:
    json.dump(appsByName, fh, ensure_ascii=False, indent=4)
# DUmp duplicates for human error checking - not working yet
#with open(outputDuplicatesJS, 'w', encoding='utf-8') as fh:
    #json.dump(dupDestinations, fh, ensure_ascii=False, indent=4)


# Dump to JSON for API automation
axisBodyTemplate = {
"name":None,
"type": "NetworkRange",
"enabled": True,
"networkRangeApplicationData": {
        "ipRangesOrCIDRs": [],
        "dnsSearches": [],
        "excludedDnsSearches": [],
        "enableICMP": True,
        #"portsAndProtocols": ["1-10","11-20:tcp","21-30:udp","40","45:tcp"]
        "portsAndProtocols": []
    },
"connectorZoneID": None
}

# import and transpose the Axis sample header row to begin a new import file
Axis_NRdict = {}
with open(sourceAxisImport_NR, 'r') as importFh:
    reader = csv.reader(importFh, delimiter = ',')
    for csvRow in reader:
        for header in csvRow:
            Axis_NRdict[header] = None
        break # Only capture the header row of the sample
# Build out the consolidated template by app display name match.
importAxis_NRs = []
for appByName in appsByName:
    dict = Axis_NRdict # refresh values to None
    dict["Name"] = appByName["name"]
    dict["ICMP enabled (Optional)"] = True
    dict["Connector Zone"] = appByName["czName"]
    dict["Tags (Optional)"] = appByName["tags"]
    dict["Allowed Ports & Protocols"] = str(appByName["allPorts"])
    if appByName["destIP"]:
        dict["IP Ranges"] = str(appByName["destIP"])
    if appByName["destUrl"]:
        dict["DNS Searches"] = str(appByName["destUrl"])
    importAxis_NRs.append(dict)
# Dump to CSV
with open(outputAxisImport_NR_CSV, 'w') as csvFh:
    writer = csv.DictWriter(csvFh, fieldnames=Axis_NRdict)
    writer.writeheader()
    writer.writerows(importAxis_NRs)



# Dump to CSV based on destination.  For Human readability of data
fields = appsByDestination[0].keys()
with open(outputAppDestinationsCSV, 'w') as csvFh:
    writer = csv.DictWriter(csvFh, fieldnames=fields)
    writer.writeheader()
    writer.writerows(appsByDestination)




# Convert CSV to bulkImport

import requests
from requests.auth import HTTPBasicAuth
import getpass
import json

user_name = input("Enter your user name for auth: ")
creds= getpass.getpass("\nEnter your password for auth: ")
#Enter the hostname and port for your nexpose server, replace example below with your implementation details
base_url = 'https:/nexpose.yourdomain:1111'

#our naming convention for sites was turbot-'aaa' with different 3 lett combos. change the search in search_site function

#Function creates a site. need to define engine and name. returns the Site ID of new site
def create_site(site_name,site_engine):
    #API call info
    headers = {'Content-type':'application/json', 'Accept':'application/json'}
    data = {"engineId": site_engine, "name": site_name, "scan": {"assets": {"includedTargets": {"addresses": [""]}}}, "scanTemplateId": "_mhe-full-audit-turbot"}
    url = base_url+'/api/3/sites'
    #API call
    response = requests.post(url, json=data, auth=HTTPBasicAuth(user_name,creds), headers=headers)
    print(response.status_code)
    #For successful API call, response code will be (OK)
    if response.ok:

    #Loading the response data into a dict variable
    # json.loads takes in only binary or string variables so using content to fetch binary content
    # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
        jdata = json.loads(response.text)

        #Prints new site ID, raises issue if one is not found in response
        print("\n")
        for keys in jdata:
            if keys == "id":
                print("Site ID = " + str(jdata[keys]))
                site_id = jdata[keys]

    else:
    #If response code is not ok (200), print the resulting http error code with description
        response.raise_for_status()
    return site_id


#Function searches for and returns the site ID of the old site, based on the turbot account code
def search_site_id(turbot_account):
    turbot_account = "turbot-" + turbot_account
    url = base_url +'/api/3/sites'
    params = {'page': '0', 'size': '250', 'sort': ''}
    response = requests.get(url, params=params,auth=HTTPBasicAuth(user_name,creds))
    if response.ok:
        print("\nSearching for old site ID...")
        jdata = json.loads(response.text)
        # Parse the json for the resource information which contains each site, and the corresponding information
        for keys in jdata:
            if keys == "resources":
                # Parse the resources for the site name that matches the input, then get the site ID for that site
                for resource_dict in jdata[keys]:
                    for key, value in resource_dict.items():
                        if key == "name":
                            if turbot_account in str.lower(value):
                                print('Match: ' + value)
                                for i, site_id in resource_dict.items():
                                    if i == "id":
                                        return site_id
    else:
        response.raise_for_status()

#gets schedule of old site, and applies it to the new site
def schedule_swap(new_site_id_1,old_site_id_2):
    get_url = base_url + "/api/3/sites/" + str(old_site_id_2) + "/scan_schedules"
    start_time = ''
    repeat = ''
    post_url = base_url+ "/api/3/sites/" + str(new_site_id_1) + "/scan_schedules"
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}


    response = requests.get(get_url, auth=HTTPBasicAuth(user_name, creds))
    jdata = json.loads(response.text)
    if response.ok:
        #same process for parsing the returned Json as in the searc_site_is function
        for keys in jdata:
            if keys == "resources":
                # Parse the resources for the site name that matches the input, then get the site ID for that site
                for resource_dict in jdata[keys]:
                    for key, value in resource_dict.items():
                        if key == "nextRuntimes":
                            start_time = value[0]
                    #       print("\nstart time: " + start_time)
                        elif key == "repeat":
                            repeat = value
    #                       print("\nrepeat schedule: " + str(value))
    else:
        response.raise_for_status()

    data = {"enabled": "true", "onScanRepeat": "restart-scan", "repeat": repeat, "start": str(start_time)}
    response = requests.post(post_url, json=data, auth=HTTPBasicAuth(user_name, creds), headers=headers)
    if response.ok:
        print("\nSchedule Post successful")
    else:
        response.raise_for_status()


#Deletes old site
def delete_old_site(old_site_id_2):
    delete_url = base_url + "/api/3/sites/" + str(old_site_id_2)
    response = requests.delete(delete_url, auth=HTTPBasicAuth(user_name, creds))

    if response.ok:
        print("\nDelete successful\n")
    else:
        response.raise_for_status()



#main code: runs the above functions to create a site, find the old site it is replacing, add the scan schedule of the old site to the new site, then delete the old site

turbot_account = input("Enter the account code for the Turbot account: ")
old_site_id_2 = search_site_id(turbot_account)

site_name = input("Enter new site name: ")
prod_nprod = input("Enter \"prod\" or \"nprod\": ")
site_engine = 0

if prod_nprod == 'prod':
    print('\nUsing Prod scan engine')
    site_engine = "26"
elif prod_nprod == 'nprod':
    print('\nUsing Nprod scan engine')
    site_engine = "27"
else:
    print('\nError, please enter prod or nprd')

new_site_id_1 = create_site(site_name,site_engine)
print("\nNew Site ID: " + str(new_site_id_1))




print("\nAdding old scan schedule to new site...\n")
schedule_swap(new_site_id_1,old_site_id_2)
if input("\nConfirm deletion of old site (press 'y' to delete or anything else to move on): ") == "y":
    delete_old_site(old_site_id_2)







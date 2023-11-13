import logging
import azure.functions as func
from azure.cosmos import cosmos_client
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from shared_code.Player import Player
import json

with open('local.settings.json') as settings_file:
    settings = json.load(settings_file)
MyCosmos = cosmos_client.CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    # Parse the request body (check incorrect format)
    try:
        req_body = req.get_json()
        method = req.method
        username = req_body.get("username")
        password = req_body.get("password")
        logging.info('Python HTTP trigger function processed a request:{}'.format(req_body))
    except:
        return func.HttpResponse("Invalid JSON format in the request body.",status_code=400)
    
    if method == "GET":
        try:

            # Query CosmosDB to find the player
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": username}]
            players = list(PlayerContainerProxy.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            #Check if username has been retrieved
            if not players:
                return func.HttpResponse(json.dumps({"result": False, "msg": "Username or password incorrect"}), status_code=400)

            # Retrieve the stored password
            stored_password = players[0]['password']

            # Compare the input password with the stored password
            if password == stored_password:
                return func.HttpResponse(json.dumps({"result": True, "msg": "OK"}), status_code=200)
            else:
                return func.HttpResponse(json.dumps({"result": False, "msg": "Username or password incorrect"}), status_code=400)

        # Exceptional exceptions
        except Exception as e:
            logging.error("An error occurred: %s", str(e))
            logging.stack_trace(e)
            return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
    
    #If method is not get, then return error 
    return func.HttpResponse("Request method not supported.", status_code=405)

import logging
import azure.functions as func
from azure.cosmos import cosmos_client
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from shared_code.Player import Player
import json

# Initialize CosmosDB client using the local.settings file information
with open('local.settings.json') as settings_file:
    settings = json.load(settings_file)
MyCosmos = cosmos_client.CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
TreeHuggersDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
PlayerContainerProxy = TreeHuggersDBProxy.get_container_client(settings['Values']['PlayerContainerName'])

def main(req: func.HttpRequest) -> func.HttpResponse:
    req_body = req.get_json()
    logging.info('Python HTTP trigger function processed a request:{}'.format(req_body))
    
    # Parse the request body (check incorrect format)
    try:
        method = req.method
        username = req_body.get("username")
        password = req_body.get("password")
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

    elif method == "POST":
            try:
                 

                # Validate username and password
                if len(username) < 4 or len(username) > 14:
                    return func.HttpResponse(json.dumps({"result": False, "msg": "Username less than 4 characters or more than 14 characters"}), status_code=400)
                if len(password) < 10 or len(password) > 20:
                    return func.HttpResponse(json.dumps({"result": False, "msg": "Password less than 10 characters or more than 20 characters"}), status_code=400)

                # Check if username already exists
                query = f"SELECT * FROM c WHERE c.username = '{username}'"
                items = list(PlayerContainerProxy.query_items(query=query, enable_cross_partition_query=True))
                if len(items) > 0 :
                    return func.HttpResponse(json.dumps({"result": False, "msg": "Username already exists"}), status_code=400)

                # If all checks pass
                try:
                    new_player = Player(id=0, username=username, password= password, games_played=0, total_score=0)
                    PlayerContainerProxy.create_item(new_player.to_dict(), enable_automatic_id_generation=True)
                    return func.HttpResponse(json.dumps({"result": True, "msg": "OK"}), mimetype="application/json")
                    #hash password for big security 
                    
                except:
                    Exception("There was an error in creating or adding the player", status_code=500)
            
            #Error in processing HTTP response
            except Exception as e:
                logging.error("An error occurred: %s", str(e))
                logging.stack_trace(e)
                return func.HttpResponse(f"Unknown error occurred: {str(e)}",status_code=500)

    return func.HttpResponse("Request method not supported.", status_code=405)
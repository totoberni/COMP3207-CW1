import logging
import azure.functions as func
from azure.cosmos import cosmos_client
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
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
        games_to_add = req_body.get("add_to_games_played")
        score_to_add = req_body.get("add_to_score")
        logging.info('Python HTTP trigger function processed a request:{}'.format(req_body))
    
    except Exception as e:
        logging.error(f'Error parsing JSON: {str(e)}')
        logging.stacktrace(e)
        return func.HttpResponse("Invalid JSON format in the request body.", status_code=400)
    
    if method == "PUT":
        try:
            # Query CosmosDB to find the player
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": username}]
            players = list(PlayerContainerProxy.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            player = players[0]
        except Exception as e:
            logging.error(f'Error in searching for player: {str(e)}')
            return func.HttpResponse("Error in searching for the player", status_code=400)
            
        #Check that we are only editing one player
        if len(players) == 0:
            return func.HttpResponse(json.dumps({"result": False, "msg": "Player does not exist"}), status_code=404)
        
        elif len(players) > 1:
            # Handle the unexpected case of multiple players with the same username
            return func.HttpResponse("Multiple players found with the same username", status_code=500)
        
        try:
            player["games_played"] += games_to_add
            player["total_score"] += score_to_add
            PlayerContainerProxy.upsert_item(player.to_dict())
            return func.HttpResponse(json.dumps({"result": True, "msg": "OK"}), status_code=200)
        
        except Exception as e:
            logging.error(f'Error processing request: {str(e)}')
            return func.HttpResponse(f"Error updating player data: {str(e)}", status_code=500)    
    
    #If method is not PUT, then return error 
    return func.HttpResponse("Request method not supported.", status_code=405)
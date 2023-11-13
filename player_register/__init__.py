import logging
import azure.functions as func
from azure.cosmos import cosmos_client
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from shared_code.Player import Player
import os
import json

#TODO: Store keys in a better fashion

# Initialize CosmosDB client
MyCosmos = cosmos_client.CosmosClient.from_connection_string(conn_str = "AccountEndpoint=https://ab3u21.documents.azure.com:443/;AccountKey=lp7TSQlsQQpNBm9sSpesrtmMavv5UHENWaxGngRVrn2X5cgEMsAsStZ6H0yR7lhlRDD9AK6vxnLRACDbfOXg0A==;")
QuiplashDBProxy = MyCosmos.get_database_client(database = "quiplash")
PlayerContainerProxy = QuiplashDBProxy.get_container_client(container = "player")

#endpoint = os.environ["CosmosDB_Endpoint"]
#key = os.environ["CosmosDB_Key"]
#client = CosmosClient(endpoint, credential=key)

#database_name = 'quiplash'
#container_name = 'player'
#container = client.get_database_client(database_name).get_container_client(container_name)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    ##Determine HTTP method
    method = req.method
    
    if method == "GET":
        # Existing GET logic...
        pass

    elif method == "POST":
            try:
                # Parse the request body
                req_body = req.get_json()
                username = req_body.get("username")
                password = req_body.get("password")


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
                #hash password for big security
                #hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                new_player = Player(id=0, username=username, password= password, games_played=0, total_score=0)
                PlayerContainerProxy.create_item(new_player.to_dict(), enable_automatic_id_generation=True)
                return func.HttpResponse(json.dumps({"result": True, "msg": "OK"}), mimetype="application/json")
            
            #Request body is not accepable    
            except ValueError as e:
                logging.error({str(e)})
                logging.stack_trace(e)
                return func.HttpResponse(
                    "Invalid JSON format in the request body.",
                    status_code=400
                )
            #Error in processing HTTP response
            except CosmosHttpResponseError as e:
                #log error message
                logging.error("An error occurred: %s", str(e))
                logging.stack_trace(e)
                # For any other exceptions
                return func.HttpResponse(
                    f"Unknown error occurred: {str(e)}",
                    status_code=500
                )

    return func.HttpResponse("Request method not supported.", status_code=405)

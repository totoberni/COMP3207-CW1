import unittest
import json
import requests
from azure.cosmos import cosmos_client

class TestPlayerFunctions(unittest.TestCase):
    TEST_LOGIN_URL='http://localhost:7071/api/player/login'
    TEST_UPDATE_URL='http://localhost:7071/api/player/update'
    TEST_REGISTER_URL='http://localhost:7071/api/player/register'
    PUBLIC_URL=''
    #{"username": "pisell1", "password": "abracadabra01"}
    # Setup CosmosDB client for verification
    
    @classmethod
    #setup necessary proxies using local settings information
    def setUpClass(cls):
        with open('local.settings.json') as settings_file:
            settings = json.load(settings_file)
        MyCosmos = cosmos_client.CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
        QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
        PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
        
        cls.client = MyCosmos
        cls.container = PlayerContainerProxy
        
    def test_register_player(self):
        # Add a player
        payload = {"username": "ubuntuser", "password": "correctpassword"}
        response = requests.post(self.TEST_REGISTER_URL, json=payload)
        
        #validate username
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": payload['username']}]
        player = list(self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        self.assertEqual(player[0]["username"], payload['username'])
        
        # Test correct status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})
    
    def test_login_player(self): 
        # Test login with correct credentials
        payload = {"username": "ncazzuser", "password":"questaecatania"}
        requests.post(self.TEST_REGISTER_URL, json=payload)
        response = requests.get(self.TEST_LOGIN_URL, json=payload)
        
        if response.status_code != 200:
            print("-----AIUTO-----")  # Log the response body for debugging
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

    def test_update_player(self):
        # Update a player
        payload = {"username": "ubuntuser", "add_to_games_played": 1, "add_to_score": 50}
        response = requests.put(self.TEST_UPDATE_URL, json=payload)
        
        if response.status_code != 200:
                print("Response Body:", response.text)  # Log the response body for debugging
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})
    
    @classmethod
    def tearDownClass(cls):
        # Clean up test data from CosmosDB after tests
        for item in cls.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            cls.container.delete_item(item, partition_key=item['id'])

if __name__ == '__main__':
    unittest.main()
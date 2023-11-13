import unittest
import json
import requests
from azure.cosmos import cosmos_client

class TestPlayerLoginFunction(unittest.TestCase):
    TEST_LOGIN_URL='http://localhost:7071/api/player/login'
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
        TreeHuggersDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
        PlayerContainerProxy = TreeHuggersDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
        
        cls.client = MyCosmos
        cls.container = PlayerContainerProxy

    def test_login_existing_user_correct_password(self):
        # Ensure the user exists in the database
        payload = {"username": "testuser", "password": "correctpassword"}
        requests.post(self.TEST_REGISTER_URL, json=payload)

        # Test GET method
        response = requests.get(self.TEST_LOGIN_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})
        
    # If user doesn't exist their password can't be incorrect or correct ;)
    def test_login_nonexistent_user(self):
        payload = {"username": "nonexistent", "password": "wrongpassword"}
        response = requests.get(self.TEST_LOGIN_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username or password incorrect"})

    def test_login_existing_user_wrong_password(self):
        # Ensure the user exists in the database
        payload = {"username": "testuser", "password": "correctpassword"}
        requests.post(self.TEST_REGISTER_URL, json=payload)

        # Test GET method with wrong password
        payload = {"username": "testuser", "password": "wrongpassword"}
        response = requests.get(self.TEST_LOGIN_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username or password incorrect"})
        
    @classmethod
    def tearDownClass(cls):
        # Clean up test data from CosmosDB after tests
        for item in cls.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            cls.container.delete_item(item, partition_key=item['id'])

if __name__ == '__main__':
    unittest.main()
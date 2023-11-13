import unittest
import json
import requests
from azure.cosmos import cosmos_client
import os

class TestPlayerRegisterFunction(unittest.TestCase):
    #{"username": "pisell1", "password": "abracadabra01"}
    # Setup CosmosDB client for verification
    
    @classmethod
    def setUpClass(cls):
        MyCosmos = cosmos_client.CosmosClient.from_connection_string(conn_str = "AccountEndpoint=https://ab3u21.documents.azure.com:443/;AccountKey=lp7TSQlsQQpNBm9sSpesrtmMavv5UHENWaxGngRVrn2X5cgEMsAsStZ6H0yR7lhlRDD9AK6vxnLRACDbfOXg0A==;")
        QuiplashDBProxy = MyCosmos.get_database_client(database = "quiplash")
        PlayerContainerProxy = QuiplashDBProxy.get_container_client(container = "player")
        
        cls.client = MyCosmos
        cls.database_name = 'quiplash'
        cls.container_name = 'player'
        cls.container = PlayerContainerProxy

    def test_insert_player_empty_db(self):
        # Clear the database before testing
        for item in self.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            self.container.delete_item(item, partition_key=item['id'])

        payload = {"username": "testuser1", "password": "password12345"}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

        # Verify that the player is in the database
        query = f"SELECT * FROM c WHERE c.username = '{payload['username']}'"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        self.assertEqual(len(items), 1)

    def test_insert_player_non_empty_db(self):
        payload = {"username": "testuser2", "password": "password12345"}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

    def test_username_length(self):
        # Test with username less than 4 characters
        payload = {"username": "abc", "password": "password12345"}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username less than 4 characters or more than 14 characters"})

        # Test with username more than 14 characters
        payload = {"username": "a" * 15, "password": "password12345"}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username less than 4 characters or more than 14 characters"})

    def test_password_length(self):
        # Test with password less than 10 characters
        payload = {"username": "testuser", "password": "pass"}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Password less than 10 characters or more than 20 characters"})

        # Test with password more than 20 characters
        payload = {"username": "testuser", "password": "p" * 21}
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Password less than 10 characters or more than 20 characters"})

    def test_duplicate_username(self):
        payload = {"username": "uniqueuser", "password": "password12345"}
        # Insert the user first
        requests.post('http://localhost:7071/api/player_register', json=payload)

        # Try inserting the same user again
        response = requests.post('http://localhost:7071/api/player_register', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username already exists"})

    @classmethod
    def tearDownClass(cls):
        # Clean up test data from CosmosDB after tests
        for item in cls.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            cls.container.delete_item(item, partition_key=item['id'])

if __name__ == '__main__':
    unittest.main()
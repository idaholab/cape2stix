from taxii2client.v21 import Server
import os, json

server = Server('http://inl604320:5000/taxii2/', user = 'admin', password='Password0')
print(f'The server title is: {server.title}')

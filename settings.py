"""
client_id - 'Your client_id from https://stepic.org/oauth2/applications/'
client_secret - 'Your client_secret from https://stepic.org/oauth2/applications/'
"""

import os

client_id = os.environ.get('STEPIC_CLIENT_ID')
client_secret = os.environ.get('STEPIC_CLIENT_SECRET')

# print("client_id = {}\nclient_secret={}".format(client_id, client_secret))

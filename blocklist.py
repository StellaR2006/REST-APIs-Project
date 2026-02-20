"""
blocklist.py

this file just contains the blocklist of the JWT tokens. it will be imported by 
app and the logout resource so that token can be added to blocklist when the user
logs out
"""

BLOCKLIST = set()
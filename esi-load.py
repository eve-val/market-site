#!/usr/bin/env python3

STRUCTURE=1021149293700

from esipy import App, EsiSecurity, EsiClient

FILE='refresh.code'

def init_esi():
    esi_app = App.create('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')
    esi_security = EsiSecurity(
        app=esi_app,
        redirect_uri='https://www.msully.net/stuff/get-token',
        client_id='720c0d0aa9714cec9d08c36a068f20c3',
        # XXX: THIS IS A SECRET KEY BUT I DON'T UNDERSTAND WHY IT IS SECRET
        secret_key='q33qUBc6UJHgHHxEt1qB9Wq70gvMjmRx2j1pB7ik',
    )
    return (esi_app, esi_security)


def updateRefreshToken():
    esi_app, esi_security = init_esi()
    url = esi_security.get_auth_uri(scopes=['esi-markets.structure_markets.v1'])
    print("Visit: ", url)
    print("Enter code: ", end = '')
    code = input()

    auth = esi_security.auth(code)
    refresh_token = auth['refresh_token']
    with open(FILE, 'w') as f:
        f.write(refresh_token)


def auth(esi_security):
    refresh = open(FILE).read().strip()
    esi_security.update_token({'refresh_token': refresh,
                               'access_token': None, 'expires_in': 0})
    esi_security.refresh()

def getOrders(structure=STRUCTURE):
    esi_app, esi_security = init_esi()
    auth(esi_security)
    esi_client = EsiClient(esi_security)
    op=esi_app.op['get_markets_structures_structure_id'](
        structure_id=STRUCTURE
    )
    return esi_client.request(op).data

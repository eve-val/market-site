#!/usr/bin/env python3

from collections import defaultdict, namedtuple
from esipy import App, EsiSecurity, EsiClient
import codecs

FILE='refresh.code'

ESI = namedtuple('ESI', ['app', 'security', 'client'])


def init_esi():
    esi_app = App.create('https://esi.evetech.net/_latest/swagger.json?datasource=tranquility')
    esi_security = EsiSecurity(
        app=esi_app,
        redirect_uri='https://www.msully.net/stuff/get-token',
        client_id='fca36d677f9a4b8e8581d8cd2c738c2c',
        # 'The "Secret Key" should never be human-readable in your application.'
        secret_key=codecs.decode('AIUr5ntWiEIXiavPjKtUCiNFwlvTBlJqmElgAk4x',
                                 'rot_13'),
        headers={'User-Agent':'sound-market-checker'},
    )
    esi_client = EsiClient(esi_security,
                           headers={'User-Agent':'sound-market-checker'},
    )
    return ESI(esi_app, esi_security, esi_client)

def getRefreshToken():
    esi = init_esi()
    url = esi.security.get_auth_uri(scopes=['esi-markets.structure_markets.v1',
                                            'esi-search.search_structures.v1'],
                                    state='ofsoundmind')
    print("Visit: ", url)
    print("Enter code: ", end = '')
    code = input()

    auth = esi.security.auth(code)
    refresh_token = auth['refresh_token']
    with open(FILE, 'w') as f:
        f.write(refresh_token)

def auth(esi):
    refresh = open(FILE).read().strip()
    esi.security.update_token({'refresh_token': refresh,
                               'access_token': None, 'expires_in': 0})
    esi.security.refresh()

def initAndAuth():
    esi = init_esi()
    auth(esi)
    return esi

def getStructures(esi, structure, strict=False):
    subject=esi.security.verify()['sub']
    charId=subject.split(':')[2]
    op=esi.app.op['characters_character_id_search'](
        character_id=charId,
        categories=['structure'],
        strict=strict,
        search=structure
    )
    return esi.client.request(op).data

def getOrders(esi, structure):
    # TODO: ok this might get paginated at some point and then we'll
    # need to do multiple pages??
    op=esi.app.op['get_markets_structures_structure_id'](
        structure_id=structure
    )
    return esi.client.request(op, raise_on_error=True).data

def summarizeOrders(orders):
    sells = [x for x in orders if not x.is_buy_order]
    groups = defaultdict(list)
    for order in sells:
        groups[order.type_id] += [order]

    summary = defaultdict(lambda:(0, 0))
    for id, orders in groups.items():
        price = min(x.price for x in orders)
        volume = sum(x.volume_remain for x in orders)
        summary[id] = (price, volume)

    return summary

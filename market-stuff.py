#!/usr/bin/env python3

from collections import namedtuple
import collections
import email
import json
import sqlite3
import sys
import urllib.request as urlreq
import esi_load

CHUNK_SIZE = 100
ITEM_LIST = 'items'
EVECENTRAL_HOURS = 48
MARKET_HUB = 'Jita'

ColumnProperties = namedtuple('ColumnProperties', ['display_name', 'is_numeric'])
column_properties = collections.OrderedDict([
        ('Group',
         ColumnProperties(is_numeric=False, display_name='Group')),
        ('Item',
         ColumnProperties(is_numeric=False, display_name='Item')),
        ('Volume',
         ColumnProperties(is_numeric=True,  display_name='Volume')),
        ('Price',
         ColumnProperties(is_numeric=True,  display_name='Price')),
        ('HubVolume',
         ColumnProperties(is_numeric=True,  display_name='%s Volume' % MARKET_HUB)),
        ('HubPrice',
         ColumnProperties(is_numeric=True,  display_name='%s Price' % MARKET_HUB)),
        ('HubRelative',
         ColumnProperties(is_numeric=True,  display_name='Relative to %s' % MARKET_HUB)),
])

Item = namedtuple('Item', ['id', 'name', 'group', 'category', 'market_group_id'])
Row = namedtuple('Row', column_properties.keys())
MarketGroup = namedtuple('MarketGroup', ['id', 'parent_id', 'name', 'good_name'])

id2item = {}
name2item = {}
market_groups = {}
market_group_useful_names = {}

esi = None
conn = None
try:
    conn = sqlite3.connect('eve-dump.db')
    conn.text_factory = lambda x: str(x, 'latin1') # ASDF
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    if len(cursor.fetchall()) == 0:
        raise Exception("database is empty")
except Exception as e:
    print("Could not open Eve database dump:", str(e), file=sys.stderr)
    sys.exit(1)

def get_system_id(name):
    c = conn.cursor()
    c.execute("SELECT itemID from invnames where itemName = ?", (name,))
    return c.fetchone()[0]

def load_items():
    c = conn.cursor()
    c.execute("select typeId, typeName, groupName, categoryName, marketGroupID from invtypes join invgroups on invtypes.groupID = invgroups.groupID join invcategories on invgroups.categoryID = invcategories.categoryID")

    for entry in c:
        item = Item(*entry)
        name2item[item.name] = item
        id2item[item.id] = item


def load_marketgroups():
    c = conn.cursor()
    c.execute("select marketGroupID, parentGroupID, marketGroupName from invmarketgroups")

    for entry in c:
        market_group = MarketGroup(*entry, good_name=None)
        market_groups[market_group.id] = market_group

    for (id, mg) in market_groups.items():
        market_groups[id] = mg._replace(good_name = useful_market_group_name(id))

# Get the list of all parents of a market group
def get_parents(id):
    trace = []
    while id:
        mg = market_groups[id]
        trace.append(mg.name)
        id = mg.parent_id
    return trace

# This, using some ad-hoc rules, tries to produce a useful category
# name.  There is nothing particularly principled about this, but I
# like the results.
def useful_market_group_name(id):
    # Grab the list of all of the parent market groups
    parents = list(reversed(get_parents(id)))
    if len(parents) == 1:
        return parents[0]
    elif parents[0] == 'Ship Modifications':
        if len(parents) >= 3 and parents[1] == 'Rigs':
            # Rig groups are named like "Electronics Superiority Rigs".
            # We want "Rigs - Electronics Superiority"
            name_body = parents[2].rsplit(None, 1)[0]
            rig_name = 'Rigs - ' + name_body
            return rig_name
        else: # This is just Subsystems, I think
            return parents[1]
    elif parents[0] == 'Ship Equipment':
        # Everything under "Ship Equipment" is a module... except for deployables
        if parents[1] == 'Deployable Equipment':
            return parents[1]
        else:
            # "Electronics and Sensor Upgrades" is really long and should be shorter.
            name = parents[1] if parents[1] != "Electronics and Sensor Upgrades" else "Electronics Upgrades"
            return 'Modules - ' + name
    elif parents[0] == 'Ships':
        # Get the real name for t2 ship classes
        if len(parents) >= 4 and parents[2].startswith("Advanced"):
            return 'Ships - ' + parents[3]
        else:
            return 'Ships - ' + parents[1]
    else:
        return parents[0]


def download_data(ids):
    url = 'https://evepraisal.com/appraisal/structured.json?persist=no'
    payload = ", ".join('{"type_id": %d}' % i for i in ids)
    payload = '{"market_name": "jita", "items": [%s]}' % payload
    req = urlreq.Request(url, data=payload.encode(), headers={'User-Agent': 'market.of-sound-mind.com', 'Content-Type': 'application/json'})
    s = urlreq.urlopen(req)
    s = "".join(x.decode() for x in s)

    obj = json.loads(s)
    return obj

def chunk(l, size):
    chunked = []
    i = 0
    while i < len(l):
        chunked.append(l[i:i+size])
        i += size
    return chunked

def read_xml_field(node, key):
    return node.getElementsByTagName(key)[0].childNodes[0].data

def summarize_json(data):
    l = []
    items = data["appraisal"]["items"]
    for item in items:
        id = item["typeID"]
        min_price = item["prices"]["sell"]["min"]
        volume = item["prices"]["sell"]["volume"]
        l += [(id, (min_price, volume))]
    return l


def handle_data(target_items, hub_items):
    table = []

    # If we couldn't get data from evemarketer for hub relative stuff,
    # fill in dummy data.
    if not hub_items:
        hub_items = [(id, (0,"?")) for (id, _) in target_items]
    hub_items = sorted(hub_items, key=lambda i: i[0])
    target_items = sorted(target_items, key=lambda i: i[0])

    for item, hub_item in zip(target_items, hub_items):
        id, (min_price, volume) = item
        hub_id, (hub_min_price, hub_volume) = hub_item
        item = id2item[id]
        assert(id == hub_id)

        hub_relative_formatted = "?"
        if volume > 0 and hub_min_price > 0:
            hub_relative = (min_price - hub_min_price) * 100.0 / (hub_min_price)
            hub_relative_formatted = "{:.1f}%".format(hub_relative)

        group_name = (market_groups[item.market_group_id].good_name
                      if item.market_group_id else "WTF")

        row = Row(Item=item.name, Volume=volume, Price=min_price, HubVolume=hub_volume, HubPrice=hub_min_price, HubRelative=hub_relative_formatted, Group=group_name)
        table.append(row)

    return table

def text_output(table, system, name):
    f = open(system + ".txt", "w")
    for parts in table:
        print(parts, file = f)
    f.close()

def json_output(table, system, name):
    table = [{
        "group": row.Group,
        "item": row.Item,
        "itemID": name2item[row.Item].id,
        "volume": row.Volume,
        "price": row.Price,
        "hub_volume": row.HubVolume,
        "hub_price": row.HubPrice,
    } for row in table]
    f = open(system + ".json", "w")
    print(json.dumps(table), file = f)
    f.close()

def make_tag(name, attribs=None):
    if attribs:
        return "<%s %s>" % (name, ' '.join("{!s}={!r}".format(key,val) for (key,val) in attribs.items()))
    else:
        return "<%s>" % name

def make_row(open_tag, close_tag, entries, classes=None):
    fmt_string = (open_tag + "%s" + close_tag) * len(entries)
    cells = fmt_string % tuple(entries)
    attribs = {}
    if classes:
        attribs['class'] = ' '.join(classes)
    return "%s%s%s" % (make_tag('tr', attribs), cells, '</tr>')

def format_table(table):
    table_output = ""
    for entry in table:
        price_fmted = "{:,.2f}".format(entry.Price)
        hub_price_fmted = "{:,.2f}".format(entry.HubPrice)
        row = Row(Item=entry.Item, Volume=entry.Volume, Price=price_fmted, HubVolume=entry.HubVolume, HubPrice=hub_price_fmted, HubRelative=entry.HubRelative, Group=entry.Group)
        classes = []
        if row.Volume == 0:
            classes.append('market_hole')
        elif not row.HubRelative.startswith("?"):
            if row.HubRelative[0] == '-':
                classes.append('relative_negative')
            else:
                classes.append('relative_positive')

        table_output += make_row("<td>", "</td>", row, classes=classes) + "\n"

    return table_output

def html_output(table, system, name):
    page_template = """
<html><head><title>%(system)s market data</title>
<!-- DataTables CSS -->
<link rel="stylesheet" type="text/css" href="https://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css">
<link rel="stylesheet" type="text/css" href="market.css">

<!-- jQuery -->
<script type="text/javascript" charset="utf8" src="https://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js"></script>

<!-- DataTables -->
<script type="text/javascript" charset="utf8" src="https://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js"></script>
<script type="text/javascript" charset="utf-8">

// formatted numbers sorting based on http://datatables.net/plug-ins/sorting#formatted_numbers
jQuery.extend( jQuery.fn.dataTableExt.oSort, {
    "formatted-num-pre": function ( a ) {
        if (a === "-" || a === "") {
            return 0;
        } else if (a === "?") {
          // Special case for unknowns
          return Number.POSITIVE_INFINITY;
        } else {
          // Replace characters that aren't digits, '-' or '.'.
          return parseFloat(a.replace(/[^\d\-\.]/g, ""));
       }
    },

    "formatted-num-asc": function ( a, b ) {
        return a - b;
    },

    "formatted-num-desc": function ( a, b ) {
        return b - a;
    }
} );

$(document).ready(function() {
  $('#market').dataTable( {
    "aoColumnDefs": [
      { "sType": "formatted-num", "aTargets": %(numeric_columns)s }
    ],
    "bPaginate": false,
    "bLengthChange": false,
  } );
} );
</script>

</head><body>
<p>Price shown is the lowest price. If you want to edit the item list, see instructions in #indy.

<h1>%(name)s market</h1>
<em>Last updated %(timestamp)s [EVE time], from ESI and
<a href="http://evemarketer.com">evemarketer</a> data no more than %(data_age)d hours old
at that time.</em><br>

<table border=1 id='market'>
<thead>%(header)s</thead>
<tbody>
%(table)s
</tbody></table></body></html>"""

    f = open(system + ".html", "w")

    print(page_template % {
        'system': system,
        'name': name,
        'numeric_columns': [index for index, column in enumerate(column_properties.values()) if column.is_numeric],
        'header': make_row("<th>", "</th>", [column.display_name for column in column_properties.values()]),
        'timestamp': email.utils.formatdate(usegmt=True),
        'data_age': EVECENTRAL_HOURS,
        'table': format_table(table),
        },
          file = f)
    f.close()

def make_table(formatters, system):
    item_names = [s.strip() for s in open(ITEM_LIST)]
    item_ids = [name2item[name].id for name in item_names]

    esi = None
    citadel_id = None, None
    if not '@' in system:
        raise ValueError
    esi = esi_load.initAndAuth()
    citadel_name, system = system.split('@')
    name = system + " - " + citadel_name
    citadels = esi_load.getStructures(esi, name, True)
    citadel_id = citadels['structure'][0]
    data = []
    hub_data = []
    for part in chunk(item_ids, CHUNK_SIZE):
        hub_data += summarize_json(download_data(part))
    # if it is a citadel, get the data from there!
    if citadel_id:
        orders = esi_load.summarizeOrders(esi_load.getOrders(esi, citadel_id))
        data = [(id, orders[id]) for id in item_ids]

    table = handle_data(data, hub_data)

    for f in formatters:
        f(table, system, name)

def make_tables(formatters, systems):
    for system in systems:
        make_table(formatters, system)

def filter_input():
    names = [n.strip() for n in sys.stdin]
    valid = {name for name in names if name and name in name2item}
    for name in sorted(valid):
        print(name)

def main(args):
    load_items()
    load_marketgroups()

    if len(args) > 1 and args[1] == "--filter":
        filter_input()
    elif len(args) > 2 and args[1] == "--json":
        make_tables([json_output], args[2:])
    elif len(args) > 2 and args[1] == "--text":
        make_tables([text_output], args[2:])
    elif len(args) > 1 and args[1] == "--html":
        make_tables([html_output], args[1:])
    elif len(args) == 1 and args[1] == "--help":
        sys.stderr.write("usage: %s --filter | --text <systems or citadel@systems> | <systems or citadel@systems>\n" % args[0])
        return 1
    else:
        make_tables([html_output, json_output], args[1:])

if __name__ == '__main__':
    sys.exit(main(sys.argv))

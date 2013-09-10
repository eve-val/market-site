#!/usr/bin/env python3

# This requires a sqlite database dump from
# http://pozniak.pl/dbdump/ody110-sqlite3-v1.db.bz2

# Something that I ran to extract module lists from copy pasted forum posts:
# cat new-list | tr '[' '\n' | tr ',' '\n' | sed -e 's/^[ \t]*//' | sed 's/ x.$//' | sort | uniq | ./market-stuff.py --filter

from collections import namedtuple
import email
import sys
import sqlite3
import urllib.request as urlreq
from xml.dom.minidom import parseString

CHUNK_SIZE = 100
SYSTEM = 'Hemin'
ITEM_LIST = 'items'

Item = namedtuple('Item', ['id', 'name', 'group', 'category', 'market_group_id'])
Row = namedtuple('Row', ['Item', 'quantity', 'price', 'group'])
MarketGroup = namedtuple('MarketGroup', ['id', 'parent_id', 'name', 'good_name'])

id2item = {}
name2item = {}
market_groups = {}
market_group_useful_names = {}

conn = sqlite3.connect('ody110-sqlite3-v1.db')

def get_system_id(name):
    c = conn.cursor()
    c.execute("SELECT itemID from invnames where itemName = ?", (name,))
    return c.fetchone()

system_id = get_system_id(SYSTEM)

def load_items():
    c = conn.cursor()
    c.execute("select typeId, typeName, groupName, categoryName, marketGroupID from invtypes join invgroups on invtypes.groupID = invgroups.groupID join invcategories on invgroups.categoryID = invcategories.categoryID")

    for entry in c:
        item = Item(*entry)
#        print(item)
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
            name_body = parents[2].rsplit(maxsplit=1)[0]
            rig_name = 'Rigs - ' + name_body
            return rig_name
        else: # This is just Subsystems, I think
            return parents[1]
    elif parents[0] == 'Ship Equipment':
        # Everything under "Ship Equipment" is a module... except for deployables
        if parents[1] == 'Deployable Equipment':
            return parents[1]
        else:
            return 'Modules - ' + parents[1]
    elif parents[0] == 'Ships':
        # Get the real name for t2 ship classes
        if len(parents) >= 4 and parents[2].startswith("Advanced"):
            return 'Ships - ' + parents[3]
        else:
            return 'Ships - ' + parents[1]
    else:
        return parents[0]


def download_data(ids):
    base_url = 'http://api.eve-central.com/api/marketstat?hours=24&usesystem=%d&' % system_id
    suffix = "&".join("typeid=%d" % i for i in ids)
    url = base_url + suffix
#    print(url)
    s = urlreq.urlopen(url)
    s = "".join(x.decode() for x in s)
#    print(s)

    obj = parseString(s)
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

def handle_data(table, xml):
    items = xml.getElementsByTagName("type")
    for item_report in items:
        i = int(item_report.getAttribute("id"))
        item = id2item[i]

        sell = item_report.getElementsByTagName("sell")[0]
        volume = int(read_xml_field(sell, "volume"))
        min_price = float(read_xml_field(sell, "min"))
        price_fmted = "{:,.2f}".format(min_price)

        row = Row(item.name, volume, price_fmted, market_groups[item.market_group_id])
        table.append(row)

def text_output(table):
    for parts in table:
        print("%s: %d at %s (%s)" % parts)

def make_row(open_tag, close_tag, entries):
    fmt_string = (open_tag + "%s" + close_tag) * len(entries)
    return fmt_string % entries

def format_table(table):
    table_output = ""
    for entry in table:
        table_output += "<tr>" + make_row("<td>", "</td>", entry) + "</tr>\n"

    return table_output


def html_output(table):
    page_template = """
<html><head><title>%(system)s market data</title>
<!-- DataTables CSS -->
<link rel="stylesheet" type="text/css" href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css">

<!-- jQuery -->
<script type="text/javascript" charset="utf8" src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js"></script>

<!-- DataTables -->
<script type="text/javascript" charset="utf8" src="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js"></script>
<script type="text/javascript" charset="utf-8">

// formatted numbers sorting from http://datatables.net/plug-ins/sorting#formatted_numbers
jQuery.extend( jQuery.fn.dataTableExt.oSort, {
    "formatted-num-pre": function ( a ) {
        a = (a === "-" || a === "") ? 0 : a.replace( /[^\d\-\.]/g, "" );
        return parseFloat( a );
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
        { "sType": "formatted-num", "aTargets": [ %(price_column)d ] }
      ],
      "bPaginate": false,
      "bLengthChange": false,
    } );
  } );
</script>

</head><body>
<p>Data may be out of date or missing. Items might be in the wrong station. Price shown is the lowest price. If you want more items on here, message sully on IRC with links to lists of items (probably pastebinned).
<p><strong>Want to help out and keep this up-to-date?
Run the <a href="/poller">poller</a> while ship-spinning in Curse!</strong>

<h1>%(system)s market</h1>
<em>Last updated %(timestamp)s [EVE time], from
<a href="http://eve-central.com">eve-central</a> data no more than 24 hours old
at that time.</em><br>

<table border=1 id='market'>
<thead><tr>%(header)s</tr></thead>
<tbody>
%(table)s
</tbody></table></body></html>"""

    print(page_template % {
        'system': SYSTEM,
        'price_column': Row._fields.index("price"),
        'header': make_row("<th>", "</th>", Row._fields),
        'timestamp': email.utils.formatdate(usegmt=True),
        'table': format_table(table)
        })

def make_table(formatter):
    item_names = [s.strip() for s in open(ITEM_LIST)]
#    print(item_names)
    item_ids = [name2item[name].id for name in item_names]
#    print(item_ids)

#    for name in item_names:
#        item = name2item[name]
#        print(item.name, "----", market_groups[item.market_group_id].good_name, "----", get_parents(item.market_group_id))

    table = []
    for part in chunk(item_ids, CHUNK_SIZE):
        data = download_data(part)
        handle_data(table, data)

    formatter(table)

def make_poller():
    item_names = [s.strip() for s in open(ITEM_LIST)]
    item_ids = [name2item[name].id for name in item_names]
    print("item_ids = %s;" % str(item_ids))

def filter_input():
    for name in sys.stdin:
        name = name.strip()
        if name in name2item:
            print(name)

def main(args):
    load_items()
    load_marketgroups()

    if len(args) > 1 and args[1] == "--filter":
        filter_input()
    elif len(args) > 1 and args[1] == "--poller":
        make_poller()
    elif len(args) > 1 and args[1] == "--text":
        make_table(text_output)
    else:
        make_table(html_output)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

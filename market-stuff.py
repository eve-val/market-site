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

Item = namedtuple('Item', ['id', 'name', 'group'])

id2item = {}
name2item = {}

conn = sqlite3.connect('ody110-sqlite3-v1.db')

def get_system_id(name):
    c = conn.cursor()
    c.execute("SELECT itemID from invnames where itemName = ?", (name,))
    return c.fetchone()

system_id = get_system_id(SYSTEM)

def load_items():
    c = conn.cursor()
    c.execute("select typeId, typeName, groupName from invtypes join invgroups on invtypes.groupID = invgroups.groupID")

    for (itemid, name, group) in c:
        item = Item(itemid, name, group)
#        print(item)
        name2item[name] = item
        id2item[itemid] = item

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
        table.append((item.name, volume, min_price, item.group))

def text_output(table):
    for parts in table:
        print("%s: %d at %s (%s)" % parts)

def html_output(table):
    print("<html><head><title>%s market data</title>" % SYSTEM)
    print("""
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
        { "sType": "formatted-num", "aTargets": [ 2 ] }
      ],
      "bPaginate": false,
      "bLengthChange": false,
    } );
  } );
</script>

</head><body>""")
    print("<p>Data may be out of date or missing. Items might be in the wrong station. Price shown is the lowest price. If you want more items on here, message sully on IRC with links to lists of items (probably pastebinned).")
    print("""<p><strong>Want to help out and keep this up-to-date?
Run the <a href="/poller">poller</a> while ship-spinning in Curse!</strong>""")

    print("<h1>%s market</h1>" % SYSTEM)
    print("""<em>Last updated %s [EVE time], from
<a href="http://eve-central.com">eve-central</a> data no more than 24 hours old
at that time.</em><br>""" % email.utils.formatdate(usegmt=True))
    print("<table border=1 id='market'>")
    print("<thead><tr><th>Item</th><th>quantity</th><th>price</th><th>group</th></tr></thead>")
    print("<tbody>")
    for (name, count, price, group) in table:
        price_fmt = "{:,.2f}".format(price)
        print("<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>" % (name, count, price_fmt, group))
    print("</tbody></table></body></html>")

def make_table(formatter):
    item_names = [s.strip() for s in open(ITEM_LIST)]
#    print(item_names)
    item_ids = [name2item[name].id for name in item_names]
#    print(item_ids)

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

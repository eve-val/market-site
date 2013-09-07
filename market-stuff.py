#!/usr/bin/env python3

# This requires a sqlite database dump from
# http://pozniak.pl/dbdump/ody101-sqlite3-v12.db.bz2

# Something that I ran to extract module lists from copy pasted forum posts:
# cat new-list | tr '[' '\n' | tr ',' '\n' | sed -e 's/^[ \t]*//' | sed 's/ x.$//' | sort | uniq | ./market-stuff.py --filter

import sys
import sqlite3
import urllib.request as urlreq
from xml.dom.minidom import parseString

CHUNK_SIZE = 100
SYSTEM = 'Hemin'
ITEM_LIST = 'items'

name2id = {}
id2name = {}

conn = sqlite3.connect('ody101-sqlite3-v12.db')

def get_system_id(name):
    c = conn.cursor()
    c.execute("SELECT itemID from invnames where itemName = ?", (name,))
    return c.fetchone()

system_id = get_system_id(SYSTEM)

def load_items():
    c = conn.cursor()
    c.execute("SELECT typeId, typeName from invTypes")

    for (itemid, name) in c:
#        print(itemid, name)
        name2id[name] = itemid
        id2name[itemid] = name

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
    for item in items:
        i = int(item.getAttribute("id"))
        sell = item.getElementsByTagName("sell")[0]
        volume = int(read_xml_field(sell, "volume"))
        min_price = float(read_xml_field(sell, "min"))
        table.append((id2name[i], volume, min_price))

def text_output(table):
    for parts in table:
        print("%s: %d at %s" % parts)

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
    print("Data may be out of date or missing. Items might be in the wrong station. Price shown is the lowest price. If you want more items on here, message sully on IRC with links to lists of items (probably pastebinned).<br>")

    print("<h1>%s market</h1>" % SYSTEM)

    print("<table border=1 id='market'>")
    print("<thead><tr><th>Item</th><th>quantity</th><th>price</th></tr></thead>")
    print("<tbody>")
    for (name, count, price) in table:
        price_fmt = "{:,.2f}".format(price)
        print("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (name, count, price_fmt))
    print("</tbody></table></body></html>")

def make_table(formatter):
    item_names = [s.strip() for s in open(ITEM_LIST)]
#    print(item_names)
    item_ids = [name2id[name] for name in item_names]
#    print(item_ids)

    table = []
    for part in chunk(item_ids, CHUNK_SIZE):
        data = download_data(part)
        handle_data(table, data)

    formatter(table)

def make_poller():
    item_names = [s.strip() for s in open(ITEM_LIST)]
    item_ids = [name2id[name] for name in item_names]
    print("item_ids = %s;" % str(item_ids))

def filter_input():
    for name in sys.stdin:
        name = name.strip()
        if name in name2id:
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

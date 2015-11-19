#!/usr/bin/env python3

# Script to update the items list from old names of items to new ones
# when they change.

import sys
import sqlite3

ITEM_LIST = 'items'

def load_items(name):
    name2id = {}
    id2name = {}

    conn = sqlite3.connect(name)
    conn.text_factory = lambda x: str(x, 'latin1') # ASDF
    c = conn.cursor()
    c.execute("SELECT typeId, typeName from invTypes")

    for (itemid, name) in c:
        name2id[name] = itemid
        id2name[itemid] = name

    return (name2id, id2name)

def main(args):
    if len(args) != 3:
        print("usage: change-names.py <old-db> <new-db>")
        return 1

    name2id, _ = load_items(args[1])
    _, id2name = load_items(args[2])

    item_names = [s.strip() for s in open(ITEM_LIST)]
    for name in item_names:
        print(id2name[name2id[name]])

if __name__ == '__main__':
    sys.exit(main(sys.argv))

#!/usr/bin/env python3

import sys
import sqlite3

ITEM_LIST = 'items'

def load_items(name):
    name2id = {}
    id2name = {}

    conn = sqlite3.connect(name)
    c = conn.cursor()
    c.execute("SELECT typeId, typeName from invTypes")

    for (itemid, name) in c:
        name2id[name] = itemid
        id2name[itemid] = name

    return (name2id, id2name)

def main(args):
    name2id, _ = load_items('ody101-sqlite3-v12.db')
    _, id2name = load_items('ody110-sqlite3-v1.db')

    item_names = [s.strip() for s in open(ITEM_LIST)]
    for name in item_names:
        print(id2name[name2id[name]])

if __name__ == '__main__':
    sys.exit(main(sys.argv))

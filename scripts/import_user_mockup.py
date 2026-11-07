#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
import urllib.request
from collections import defaultdict

BASE_URL = "http://127.0.0.1:8080"
CSV_FILE = "/home/ion/Scaricati/ezBookkeeping_Doi_export_data(8).csv"

def main():
    print("1. Authenticating as user 'test'...")
    req = urllib.request.Request(
        f"{BASE_URL}/api/authorize.json",
        data=json.dumps({"loginName": "test", "password": "password123"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data["result"]["token"]
    print("   Authenticated successfully.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Timezone-Offset": "-60"
    }

    print("2. Parsing CSV file to extract categories and tags...")
    expense_map = defaultdict(set)
    income_map = defaultdict(set)
    transfer_map = defaultdict(set)
    tags = set()

    with open(CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_type = row.get("Type", "").strip()
            cat = row.get("Category", "").strip()
            sub = row.get("Sub Category", "").strip()
            t_tags = row.get("Tags", "").strip()

            if t_tags:
                for tag in t_tags.split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)

            if not cat or not sub:
                continue

            if t_type == "Expense":
                expense_map[cat].add(sub)
            elif t_type == "Income":
                income_map[cat].add(sub)
            elif t_type == "Transfer":
                transfer_map[cat].add(sub)

    print(f"   Found {len(expense_map)} expense categories, {len(income_map)} income, {len(transfer_map)} transfer, {len(tags)} tags.")

    # 3. Create Categories Batch
    categories_batch = []
    
    # Expense categories (type 2)
    colors = ["f44336", "e91e63", "9c27b0", "673ab7", "3f51b5", "2196f3", "00bcd4", "009688", "4caf50", "8bc34a", "cddc39", "ffeb3b", "ffc107", "ff9800", "ff5722", "795548"]
    for i, (cat, subs) in enumerate(expense_map.items()):
        color = colors[i % len(colors)]
        sub_list = [
            {
                "name": s,
                "type": 2,
                "parentId": "0",
                "icon": "1",
                "color": color,
                "comment": ""
            }
            for s in sorted(subs)
        ]
        categories_batch.append({
            "name": cat,
            "type": 2,
            "icon": "1",
            "color": color,
            "comment": "",
            "subCategories": sub_list
        })

    # Income categories (type 1)
    for i, (cat, subs) in enumerate(income_map.items()):
        color = "4caf50"
        sub_list = [
            {
                "name": s,
                "type": 1,
                "parentId": "0",
                "icon": "1",
                "color": color,
                "comment": ""
            }
            for s in sorted(subs)
        ]
        categories_batch.append({
            "name": cat,
            "type": 1,
            "icon": "1",
            "color": color,
            "comment": "",
            "subCategories": sub_list
        })

    # Transfer categories (type 3)
    for i, (cat, subs) in enumerate(transfer_map.items()):
        color = "2196f3"
        sub_list = [
            {
                "name": s,
                "type": 3,
                "parentId": "0",
                "icon": "1",
                "color": color,
                "comment": ""
            }
            for s in sorted(subs)
        ]
        categories_batch.append({
            "name": cat,
            "type": 3,
            "icon": "1",
            "color": color,
            "comment": "",
            "subCategories": sub_list
        })

    print("3. Sending batch category creation request...")
    cat_req = urllib.request.Request(
        f"{BASE_URL}/api/v1/transaction/categories/add_batch.json",
        data=json.dumps({"categories": categories_batch}).encode("utf-8"),
        headers=headers
    )
    try:
        with urllib.request.urlopen(cat_req) as resp:
            cat_resp = json.loads(resp.read().decode("utf-8"))
            print(f"   Categories created successfully: {cat_resp.get('success')}")
    except urllib.error.HTTPError as e:
        print(f"   Category creation error: {e.code} - {e.read().decode('utf-8')}")

    # 4. Create Tags Batch
    if tags:
        print("4. Sending batch tag creation request...")
        tag_list = [{"name": t, "groupId": "0"} for t in sorted(tags)]
        tag_req = urllib.request.Request(
            f"{BASE_URL}/api/v1/transaction/tags/add_batch.json",
            data=json.dumps({"tags": tag_list, "groupId": "0", "skipExists": True}).encode("utf-8"),
            headers=headers
        )
        try:
            with urllib.request.urlopen(tag_req) as resp:
                tag_resp = json.loads(resp.read().decode("utf-8"))
                print(f"   Tags created successfully: {tag_resp.get('success')}")
        except urllib.error.HTTPError as e:
            print(f"   Tag creation error: {e.code} - {e.read().decode('utf-8')}")

    print("5. Running ezbookkeeping transaction-import CLI...")
    cmd = [
        "go", "run", "ezbookkeeping.go", "userdata", "transaction-import",
        "--username", "test",
        "--file", CSV_FILE,
        "--type", "ezbookkeeping_csv"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("CLI Output:")
    print(res.stdout)
    if res.stderr:
        print("CLI Stderr:")
        print(res.stderr)

    if res.returncode == 0:
        print("=== SUCCESS! All mockup transactions imported for user 'test' ===")
    else:
        print(f"CLI exited with returncode {res.returncode}")

if __name__ == "__main__":
    main()

import csv
import math
import requests
from typing import List, Dict, Iterable
import os
from collections import defaultdict
from pathlib import Path
import time

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
ADRESS_REGISTER_ENDPOINT = 'http://localhost:6969/match'
SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT") or "http://localhost:8890/sparql"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/sparql-results+json",
}
HEADERS_ADRESS = {
  "Accept": "application/json",
}

#####################################################
# QUERIES
#####################################################
def get_addresses() -> Dict:
    """
    Fetch broken addresses
    """
    query = """
SELECT DISTINCT
  ?graph
  ?address
  ?addressStreet
  ?addressGemeenteNaam
  ?addressGemeenteLand
  ?addressGemeentePostCode
  ?addressGemeenteNummer
  ?site
  WHERE {{
  GRAPH ?graph {{
    ?address a <http://www.w3.org/ns/locn#Address>;
        <http://www.w3.org/ns/locn#thoroughfare> ?addressStreet;
        <https://data.vlaanderen.be/ns/adres#gemeentenaam> ?addressGemeenteNaam;
        <https://data.vlaanderen.be/ns/adres#land> ?addressGemeenteLand;
        <http://www.w3.org/ns/locn#postCode> ?addressGemeentePostCode;
        <https://data.vlaanderen.be/ns/adres#Adresvoorstelling.huisnummer>
          ?addressGemeenteNummer.
  }}

    ?site a <http://www.w3.org/ns/org#Site>;
      <https://data.vlaanderen.be/ns/organisatie#bestaatUit> ?address.

    FILTER NOT EXISTS {{
      ?address <https://data.vlaanderen.be/ns/adres#verwijstNaar> ?foo.
    }}

    }}
    """
    result = exec_sparql(query)
    rows = extract_bindings(result)
    return rows

def try_match_address(entry: Dict) -> str | None:
    """
    Try to match an address via the address register.
    If exactly one result is returned and the formatted address matches,
    return the adres identificator id.
    """

    params = {
        "municipality": entry.get("addressGemeenteNaam"),
        "zipcode": entry.get("addressGemeentePostCode"),
        "thoroughfarename": entry.get("addressStreet"),
        "housenumber": entry.get("addressGemeenteNummer"),
    }

    response = get_with_retry(
        ADRESS_REGISTER_ENDPOINT,
        params=params,
        headers=HEADERS_ADRESS,
        retries=5,
        backoff_factor=0.5,
    )

    data = response.json()

    matches = []
    for result in data:
        volledig_adres = (
            result
            .get("volledigAdres", {})
            .get("geografischeNaam", {})
            .get("spelling", "")
        )

        expected = f"{entry.get('addressStreet')} {entry.get('addressGemeenteNummer')}, " \
                   f"{entry.get('addressGemeentePostCode')} {entry.get('addressGemeenteNaam')}, " \
                   f"{entry.get('addressGemeenteLand')}"

        if volledig_adres.strip() != expected.strip():
            continue
        else:
            matches.append(result)

    matches = [m for m in matches if m.get("adresStatus") == "inGebruik"]

    if len(matches) == 0:
        print("No matches found for " + entry.get('address'))
        return None

    if len(matches) > 1:
        import pdb; pdb.set_trace()
        print("Too many matches found for " + entry.get('address'))
        return None

    identificator = matches[0].get("identificator", {})

    id = identificator.get("id")
    print('found URI:   ' + id)

    return id
#####################################################
# HELPERS
#####################################################
def exec_sparql(query: str) -> Dict:
    """
    Execute a SPARQL query using POST with application/x-www-form-urlencoded.
    """

    print("--------- EXECUTING QUERY --------- ")
    print(query.strip())
    resp = requests.post(
        SPARQL_ENDPOINT,
        headers=HEADERS,
        data={"query": query},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def extract_bindings(result: Dict) -> List[Dict[str, str]]:
    """
    Flatten SPARQL JSON bindings into simple dicts.
    """
    keys = result["head"]["vars"]
    bindings = result.get("results", {}).get("bindings", [])
    rows = []
    for binding in bindings:
        row = {}
        for key in keys:
            row[key] = binding.get(key, {}).get("value", "")
        rows.append(row)
    return rows

def write_insert_data_sparql(entries: list[dict], output_path: str) -> None:
    """
    Write INSERT DATA statements grouped per graph into a .sparql file.
    """

    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[entry["graph"]].append(entry)

    blocks: list[str] = []

    for graph, items in grouped.items():
        lines: list[str] = []
        for item in items:
            subject = f"<{item['address']}>"
            obj = f"<{item['addressRegister']}>"
            lines.append(f"    {subject} <https://data.vlaanderen.be/ns/adres#verwijstNaar> {obj} .")
            lines.append(f"""  {obj} <http://www.w3.org/2004/02/skos/core#note> "Re-attached with script. Data-quality issue. SeeAlso OP-3721" .""")

        block = (
            "INSERT DATA {\n"
            f"  GRAPH <{graph}> {{\n"
            + "\n".join(lines)
            + "\n  }\n"
            "}\n"
        )
        blocks.append(block)

    content = "\n;\n\n".join(blocks) + "\n;"

    Path(output_path).write_text(content, encoding="utf-8")


def get_with_retry(
    url,
    params=None,
    headers=None,
    retries=3,
    backoff_factor=1.0,
    timeout=10,
):
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            print(f"It seems request failed for attempt " +  str(attempt))
            if attempt == retries - 1:
                print(f"Request failed for {params}: {e}")
                return None

            sleep_time = backoff_factor * (2 ** attempt)
            print("sleeping " + str(sleep_time) + " seconds..")
            time.sleep(sleep_time)

#####################################################
# MAIN
#####################################################
def main():
    addresses = get_addresses()

    if DRY_RUN:
        addresses = addresses[:10]

    completed_addresses = []
    for address in addresses:
        adress_register = try_match_address(address)
        if(adress_register):
            address['addressRegister'] = adress_register
            completed_addresses.append(address)

    write_insert_data_sparql(completed_addresses, "output.sparql")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import logging
import requests
import json
import mprouter
from mprouter import MONOTCH_URI_BASE, MONOTCH_USABLE_PARKINGS, MONOTCH_KEY

logging.getLogger().setLevel(logging.DEBUG)

#BBOX = 4.3193, 52.1527,4.4529, 51.9396
BBOX = mprouter.get_bbox((4.37212, 52.00234), 30000)

uri = (MONOTCH_URI_BASE + "list?" + "w=%f&n=%f&e=%f&s=%f" % BBOX +
       "&types=" + MONOTCH_USABLE_PARKINGS +
       "&api_key=" + MONOTCH_KEY
      )
logging.debug("Contacting uri: %s", uri)
response = requests.get(uri)
while response.status_code == 403:
    time.sleep(1)
    logging.debug("retrying a bit later")
    response = requests.get(uri)
logging.debug("Got response: %s", response.content)
r = response.json()

json_sum = json.dumps(r, sort_keys=True, indent=4)
f = open("monotch_parkings_2.json", "w+")
f.write(json_sum)

pks = dict(mprouter.MONOTCH_CACHE_PARKING_DETAILS)
try:
    for pj in r:
        pid = pj["id"]
        if pid in pks:
            continue
        try:
            p_details = mprouter.monotch_get_parking_details(pid)
        except Exception:
            logging.exception("Failed to get %s", pid)
            continue
        pks[pid] = p_details
except KeyboardInterrupt:
    pass

fulls = json.dumps(pks, sort_keys=True, indent=4)
f = open("monotch_parking_details.json", "w+")
f.write(fulls)
f.close()

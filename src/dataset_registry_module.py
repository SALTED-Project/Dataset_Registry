import hmac
import hashlib
from flask import Flask, abort, request
from waitress import serve

import re
from urllib.parse import urlparse
import json

from ngsildclient import Entity

from injector_ngsildclient import NgsildBrokerDataInjector

import logging
log = logging.getLogger(__name__)


CATALOG_DESCRIPTION_KEYS = ["name", "title", "description", "publisher", "homepage", "rights", "license"]
DATASET_DESCRIPTION_KEYS = [ ]
DISTRIBUTION_DESCRIPTION_KEYS = ["base_url", "availability"]

form_key = ""

def is_valid_signature(timestamp, body, signature, key) -> bool:
    h = hmac.new(
        key.encode("utf-8"),
        (timestamp + "." + body).encode("utf-8"),
        hashlib.sha256,
    )
    return h.hexdigest() == signature


def validate_signature(request):
    header_signature = request.headers.get("x-wpforms-webhook-signature")
    # request.headers.getlist("x-wpforms-webhook-signature")
    if header_signature is None:
        abort(401, description="Missing signature")

    header_signature = dict(re.findall(r"(\w+)=(\w+)", header_signature))
    if not is_valid_signature(
        header_signature["t"],
        request.data.decode("utf-8"),
        header_signature["v"],
        form_key,
    ):
        abort(401, description="Invalid signature")


PORT = 5000
app = Flask(__name__)

broker = None
# To be initalized on first request
catalog: Entity = None


@app.route("/injector", methods=["POST"])
def form_to_ngsild():
    log.info(request)

    validate_signature(request)

    if request.is_json:
        form = request.json
    else:
        abort(415, description="Content type is not supported.")

    # Strip all fields
    form = {key: value.strip() for key, value in form.items()}

    # TODO: In case there is an error, any modification has to be reversed
    broker.inject_csource(form)
    broker.inject_dataset(catalog, form)
    return ("", 201)



if __name__ == "__main__":
    dcat_entities = {}
    with open("config.json") as f:
        conf = json.load(f)

        form_key = conf.get("form_key", None)
        if not form_key:
            raise ValueError("Form key not provided")

        dcat_entities["catalog"] = conf.get("catalog", {})
        missing = [key for key in CATALOG_DESCRIPTION_KEYS if key not in dcat_entities["catalog"].keys()]
        if missing:
            raise ValueError("Missing keys in catalog description:", missing)
       
        dcat_entities["dataset"] = conf.get("dataset", {})
        missing = [key for key in DATASET_DESCRIPTION_KEYS if key not in dcat_entities["dataset"].keys()]
        if missing:
            raise ValueError("Missing keys in dataset description:", missing)

        dcat_entities["distribution"] = conf.get("distribution", {})
        missing = [key for key in DISTRIBUTION_DESCRIPTION_KEYS if key not in dcat_entities["distribution"].keys()]
        if missing:
            raise ValueError("Missing keys in distribution description:", missing)

        context_broker = conf.get("context_broker", None)
        if not context_broker:
            raise ValueError("Context broker URL not provided")
       
        context_broker_url = context_broker.get("url", None)
        if not context_broker_url:
            raise ValueError("Context broker URL not provided")

        port = conf.get("port", PORT)

        context = conf.get("context", None)

    broker = NgsildBrokerDataInjector(
        context_broker_url, 
        context=context, 
        dcat_entities=dcat_entities
    )
    
    catalog = broker.inject_catalog(dcat_entities["catalog"]["name"])
    log.info("Catalog created/available %s", catalog.to_json())

    serve(app, host="0.0.0.0", port=port)

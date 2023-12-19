from datetime import datetime, timezone
# import pytz
import re
from urllib.parse import quote_plus, urljoin, urlparse

from validators import (
    is_valid_url,
    is_valid_hostname,
    is_valid_ip,
    is_valid_port,
    get_theme,
    get_access_rights,
    get_language,
    get_location,
    ACCESS_RIGHTS
)

from ngsildclient import Entity, Client
from ngsildclient.api.exceptions import (
    NgsiAlreadyExistsError,
    NgsiResourceNotFoundError,
    ProblemDetails,
)
from ngsildclient.api.helper.csourceregistration import (
    CSourceRegistration,
    CSourceRegistrationBuilder,
    RegistrationInfo,
)

from rdflib import Namespace
from rdflib.namespace import DCAT, DCTERMS
SDM = Namespace("https://smartdatamodels.org/")
SDMDCAT = Namespace("https://smartdatamodels.org/dataModel.DCAT-AP/")
NGSILD = Namespace("https://uri.etsi.org/ngsi-ld/")

import logging
log = logging.getLogger(__name__)

DEFAULT_CATALOG = {
    "id": "SALTED_Project",
    "name": "SALTED_Project",
    "title": "SALTED Project",
    "description": "This is the SALTED Project Catalogue",
    "publisher": "salted-project",
    "homepage": "https://salted-project.eu",
    "rights": "PUBLIC",
    "license": "https://creativecommons.org/licenses/by/4.0/",
}

DEFAULT_DATASET = {
    "base_id": "urn:ngsi-ld:Dataset:",
}

DEFAULT_DISTRIBUTION = {
    "base_id": "urn:ngsi-ld:Distribution:",
    # "base_url": "https://salted-project.eu/download",
    "base_url": "https://ckan.salted-project.eu/retriever",
    "availability": "FOREVER",
}

RESOURCE_TYPES = [
    {"name": "JSON", "ext": "json", "mimetype": "application/json"},
    {"name": "JSON_LD", "ext": "jsonld", "mimetype": "application/ld+json"},
    # {"name": "CSV", "ext": "csv", "mimetype": "text/csv"},
    # {"name": "XML", "ext": "xml", "mimetype": "application/xml"},
    # {"name": "RDF", "ext": "rdf", "mimetype": "application/rdf+xml"},
    # {"name": "Turtle", "ext": "ttl", "mimetype": "text/turtle"},
    # {"name": "N-Triples", "ext": "nt", "mimetype": "application/n-triples"},
    # {"name": "N3", "ext": "n3", "mimetype": "text/n3"},
]

# We are going to work with long names
# DEFAULT_CONTEXT = "https://raw.githubusercontent.com/SALTED-Project/contexts/main/wrapped_contexts/dcat-ap-context.jsonld"
DEFAULT_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.7.jsonld"

# https://stackoverflow.com/questions/36189261/python-join-multiple-components-to-build-a-url
def multi_urljoin(*parts):
    return urljoin(
        parts[0],
        "/".join(quote_plus(part.strip("/"), safe="") for part in parts[1:]), # changing safe="/" to safe="" --> using URLs as parameters (need / to be encoded too)
    )


def create_list(item_a, item_b):
    a_list = item_a if isinstance(item_a, list) else [item_a]
    b_list = item_b if isinstance(item_b, list) else [item_b]
    final_list = list(set(a_list + b_list))
    return final_list


def create_string(string_chain, substring):
    if substring not in string_chain:
        string_chain = string_chain + "," + substring
    return string_chain


def to_ckan_valid_name(name: str) -> str:
    return name.lower().replace(" ", "_")


def entity_name_type_from_id(entity_id: str) -> str:
    pattern = r"urn:ngsi-ld:(.*?):(.*)$"
    matches = re.match(pattern, entity_id)
    return (matches.group(2), matches.group(1)) if matches else (None, None)


# def create_id(a: str, b: str) -> str:
#     id = "urn:ngsi-ld:" + a + ":" + b
#     return id


class NgsildBrokerDataInjector(object):
    ngsild_api = None
    context = ""

    def __init__(self, broker_url, dcat_entities={}, context=DEFAULT_CONTEXT) -> None:
        self.broker_url = broker_url
        self.context = context
       
        # TODO: Modify ngsildclient library to support url
        urlparsed = urlparse(broker_url)
        self.ngsild_api = Client(
            hostname=urlparsed.hostname, port=urlparsed.port, secure=True
        )

        if not context:
            context=DEFAULT_CONTEXT
    
        DEFAULT_CATALOG.update(dcat_entities.get("catalog", {}))
        DEFAULT_DATASET.update(dcat_entities.get("dataset", {}))
        DEFAULT_DISTRIBUTION.update(dcat_entities.get("distribution", {}))
    

        # self.ngsild_api.set_link_header(
        #     "<"
        #     + DEFAULT_CONTEXT
        #     + '>;rel="http://www.w3.org/ns/json-ld#context";type="application/ld+json"'
        # )

    def get_ngsild_api(self):
        return self.ngsild_api

    # def update_context(self, jsonld):
    #     jsonld.update({"@context": [DEFAULT_CONTEXT]})
    #     return jsonld

    # def remote_create_entity(self, entity) -> str:
    #     # Append context to entity (just in case)
    #     entity.set_context(DEFAULT_CONTEXT)

    #     self.ngsild_api.create_entity(entity.as_json())

    # def remote_update_entity(self, entity) -> None:
    #     # Append context to entity (just in case)
    #     entity.set_context(DEFAULT_CONTEXT)

    #     # self.ngsild_api.update_entity_attributes(
    #     #     entity_id, attributes_data=json.dumps(attrs)
    #     # )
    

    # Smart Data Model https://github.com/smart-data-models/dataModel.DCAT-AP/blob/master/Distribution/doc/spec.md
    def create_new_distribution(self, catalog: Entity, dataset: Entity, resource_type: dict) -> Entity:      
        dataset_name, dataset_type = entity_name_type_from_id(dataset.id)
        id = dataset_name + ":" + resource_type["ext"]

        # resource = Entity(str(SDMDCAT["Distribution"]), id, ctx=self.context)
        # resource['id'] = create_id("Distribution", id)

        resource = Entity("Distribution", id, ctx=self.context)
        resource["type"] = str(SDMDCAT["Distribution"])
        
        # name
        # resource.prop("name", "{} realtime data in {} format".format(dataset["title"].value, resource_type["name"]))

        # title
         # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["title"]
        resource.prop("title", "Realtime data in {}".format(resource_type["name"])) # resource.prop(str(DCTERMS["title"]), "Realtime data in {}".format(resource_type["name"]))

        # description
        # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["description"]
        resource.prop("description", ["{} realtime data represented in {} format".format(dataset["title"].value, resource_type["name"])]) # resource.prop(str(DCTERMS["description"]), ["{} realtime data represented in {} format".format(dataset["title"].value, resource_type["name"])])
        
        # format
        # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment NGSILD["format"]
        resource.prop("format", resource_type["name"]) # resource.prop(str(NGSILD["format"]), resource_type["name"])
        
        # mediaType
        resource.prop(str(SDMDCAT["mediaType"]), resource_type["mimetype"])


        # hash
        # resource.prop("hash", "")  # Unable to get hash as it's realtime data

        # license --> inherited from dataset when imported to CKAN
        # resource.prop("license", catalog["license"].value)

        # rights
        resource.prop(str(SDMDCAT["rights"]), dataset[str(SDMDCAT["accessRights"])].value.split("/")[-1])

        # dateCreated
        resource.prop(str(SDM["dateCreated"]), dataset[str(SDM["dateCreated"])].value)

        # dateModified
        resource.prop(str(SDM["dateModified"]), dataset[str(SDM["dateCreated"])].value)

        # --- URLs ---
        # realtime #    /retriever/realtime/__https://smartdatamodels.org/dataModel.DCAT-AP/DistributionDCAT-AP__.json
        # encoded url :/retriever/realtime/__https%3A%2F%2Fsmartdatamodels.org%2FdataModel.Environment%2FAirQualityObserved__.json
        resource_url = multi_urljoin(DEFAULT_DISTRIBUTION["base_url"], "retriever", "realtime", "__" + dataset[str(SDMDCAT["Type"])].value + "__") + "." + resource_type["ext"] 
        

        # temporal
        # Default:/retriever/realtime/__https%3A%2F%2Fsmartdatamodels.org%2FdataModel.DCAT-AP%2FDistributionDCAT-AP__.jsonld
        #          days=5
        # Custom: /realtime/__https%3A%2F%2Fsmartdatamodels.org%2FdataModel.DCAT-AP%2FDistributionDCAT-AP__.jsonld?<unit>=<value> 
        #         unit = ['years', 'months', 'weeks', 'days', 'hours']
        # resource_url = multi_urljoin(DEFAULT_DISTRIBUTION["base_url"], "temporal", "__" + dataset["Type"].value + "__") + "." + resource_type["ext"] 

        # downloadURL
        resource.prop(str(SDMDCAT["downloadURL"]), resource_url)

        # accessUrl
        resource.prop(str(SDMDCAT["accessUrl"]), resource_url)

        # availability
        resource.prop(str(SDMDCAT["availability"]), DEFAULT_DISTRIBUTION["availability"])

        # resource.set_context(DEFAULT_CONTEXT)

        return resource

    def get_dataset(self, dataset_id: str) -> Entity:
        # Check if dataset exists
        try:
            id = "urn:ngsi-ld:Dataset:" + dataset_id
            dataset = self.ngsild_api.get(id, ctx=self.context)
        except NgsiResourceNotFoundError as err:
            return None
        return dataset

    # Smart Data Model  https://github.com/smart-data-models/dataModel.DCAT-AP/blob/master/Dataset/doc/spec.md
    def create_new_dataset(self, catalog: Entity, dataset_form: dict) -> Entity:
        catalog_name, catalog_type = entity_name_type_from_id(catalog.id)
        id = catalog_name + ":" + dataset_form["type"]

        # dataset = Entity(str(SDMDCAT["Dataset"]), id, ctx=self.context)
        # dataset['id'] = create_id("Dataset", id)
        dataset = Entity("Dataset", id, ctx=self.context)
        dataset["type"] = str(SDMDCAT["Dataset"])

        # Check if dataset entity already exists --> append new values (form) to properties
        current_dataset = self.get_dataset(id)
        if current_dataset:
            # description
            # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["description"]
            dataset.prop("description", create_list(current_dataset["description"].value, dataset_form["description"])) # dataset.prop(str(DCTERMS["description"]), create_list(current_dataset[str(DCTERMS["description"])].value, dataset_form["description"]))

            # creator
            dataset.prop(str(SDMDCAT["creator"]), create_list(current_dataset[str(SDMDCAT["creator"])].value, dataset_form["creator"]))
            
            # dataProvider
            dataset.prop(str(SDM["dataProvider"]), create_list(current_dataset[str(SDM["dataProvider"])].value, dataset_form["dataProvider"]))
            
            # language
            dataset.prop(str(SDMDCAT["language"]), create_list(current_dataset[str(SDMDCAT["language"])].value, dataset_form["language"]))

            # keyword
            dataset.prop(str(SDMDCAT["keyword"]), create_list(current_dataset[str(SDMDCAT["keyword"])].value, dataset_form["keyword"]))
            
            # theme 
            dataset.prop(str(SDMDCAT["theme"]), create_list(current_dataset[str(SDMDCAT["theme"])].value, dataset_form["theme"])) # [theme1, theme2, ...]
            # theme_url = [multi_urljoin("http://publications.europa.eu/resource/authority/data-theme/", theme) for theme in dataset_form["theme"]]
            # dataset.prop("theme", create_list(current_dataset["theme"].value, theme_url)) # [url/theme1, url/theme2, ...]

            # spatial
            dataset.prop(str(SDMDCAT["spatial"]), create_list(current_dataset[str(SDMDCAT["spatial"])].value, dataset_form["spatial"])) # [location1, location2, ...]
            # spatial_url = [(
            #     multi_urljoin("http://publications.europa.eu/resource/authority/country/",location)
            #     if location != "EUROPE"
            #     else multi_urljoin("http://publications.europa.eu/resource/authority/continent/",location)
            #     ) 
            #     for location in dataset_form["spatial"]]
            # dataset.prop("spatial", create_list(current_dataset["spatial"].value, spatial_url)) [url/location1, url/location2, ...]

            # Access_Rights: less restrictive 
            if ACCESS_RIGHTS.index(dataset_form["accessRights"]) <  ACCESS_RIGHTS.index(current_dataset[str(SDMDCAT["accessRights"])].value): 
                dataset.prop(str(SDMDCAT["accessRights"]), dataset_form["accessRights"]) # "accessRights"
            else:
                dataset.prop(str(SDMDCAT["accessRights"]), current_dataset[str(SDMDCAT["accessRights"])].value) # "accessRights"
            # if ACCESS_RIGHTS.index(dataset_form["accessRights"]) <  ACCESS_RIGHTS.index(current_dataset["accessRights"].value.split("/")[-1]): 
            #     access_right_url = multi_urljoin("http://publications.europa.eu/resource/authority/access-right/", dataset_form["accessRights"])
            #     dataset.prop("accessRights", access_right_url)  # "url/accessRights"
            # else:
            #     dataset.prop("accessRights", current_dataset["accessRights"].value) # "url/accessRights"
                        
        else:
            # description
            # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["description"]
            dataset.prop("description", dataset_form["description"]) # dataset.prop(DCTERMS["description"], dataset_form["description"])

            # creator
            dataset.prop(
                str(SDMDCAT["creator"]),
                dataset_form["creator"]
                if "creator" in dataset_form
                else catalog[str(SDMDCAT["publisher"])].value,
            ) 

            # dataProvider
            dataset.prop(
                str(SDM["dataProvider"]),
                dataset_form["dataProvider"]
                if "dataProvider" in dataset_form
                else catalog[str(SDMDCAT["publisher"])].value, 
            )

            # theme
            dataset.prop(str(SDMDCAT["theme"]), dataset_form["theme"]) # [theme1, theme2, ...]
            # theme_url = [multi_urljoin("http://publications.europa.eu/resource/authority/data-theme/", theme) for theme in dataset_form["theme"]]
            # dataset.prop("theme", theme_url) # [url/theme1, url/theme2, ...]
            
            # language
            dataset.prop(str(SDMDCAT["language"]), dataset_form["language"])

            # keyword
            dataset.prop(str(SDMDCAT["keyword"]), dataset_form["keyword"])
            
            # spatial
            dataset.prop(str(SDMDCAT["spatial"]), dataset_form["spatial"]) # [location1, location2, ...]
            # spatial_url = [(
            #     multi_urljoin("",location)
            #     if location != "EUROPE"
            #     else multi_urljoin("http://publications.europa.eu/resource/authority/continent/",location)
            #     ) 
            #     for location in dataset_form["spatial"]]
            # dataset.prop("spatial", spatial_url) # [url/location1, url/location2, ...]
            
            # accessRigths
            dataset.prop(str(SDMDCAT["accessRights"]), dataset_form["accessRights"]) # "accessRights"
            # access_right_url = multi_urljoin("http://publications.europa.eu/resource/authority/access-right/", dataset_form["accessRights"])
            # dataset.prop("accessRights", access_right_url) # "url/accessRights"


        # Type
        dataset.prop(str(SDMDCAT["Type"]), dataset_form["Type"]) # original type --> long name (https://smartdatamodels.org....)

        # title
        # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["title"]
        dataset.prop("title", dataset_form["type"]) # dataset.prop(DCTERMS["title"], dataset_form["type"])
        
        # name
        # dataset.prop("name", to_ckan_valid_name(dataset_form["title"]))           
        
        # publisher
        dataset.prop(str(SDMDCAT["publisher"]), catalog[str(SDMDCAT["publisher"])].value)
        
        # versionInfo
        dataset.prop(str(SDMDCAT["versionInfo"]), "1.0")

        # TODO: Check if dataset already exists
        dataset.prop(
            str(SDM["dateCreated"]),
            # CKAN doesn't support timezone
            datetime.now(timezone.utc).isoformat().split("+")[0]
            # datetime.now().isoformat() 
            # datetime.now(pytz.timezone("Europe/Madrid")).isoformat(),
        ).prop(
            str(SDM["dateModified"]),
            # CKAN doesn't support timezone
            datetime.now(timezone.utc).isoformat().split("+")[0]
            # datetime.now().isoformat(),
            # datetime.now(pytz.timezone("Europe/Madrid")).isoformat(),
        )

        # license
        dataset.prop(str(SDMDCAT["license"]), catalog[str(SDMDCAT["license"])].value)

        # TODO: Analyse if it has to be retrieved from the broker itself
        # temporal
        dataset.prop(str(SDMDCAT["temporal"]), dataset_form["temporal"])

        # landingPage
        dataset.prop(str(SDMDCAT["landingPage"]), "https://salted-project.eu/")

        # distributions
        distributions = []
        dataset.rel(str(SDMDCAT["distribution"]), [])
        for resource_type in RESOURCE_TYPES:
            distribution = self.create_new_distribution(catalog, dataset, resource_type)
            # distribution.pprint()

            distributions.append(distribution)
            dataset[str(SDMDCAT["distribution"])].value.append(distribution.id) 
        
        return dataset, distributions

    def form_validate_dataset(self, form: dict):
        dataset_form = {}
                
        # Save the original type --> long name
        dataset_form["Type"] = form["DatasetType"]

        smartdatamodels_pattern = r'https:\/\/smartdatamodels\.org\/dataModel.(.*)'
        fiware_pattern = r'https:\/\/uri\.fiware\.org\/ns\/data\-models#(.*)'
        salted_pattern = r'https:\/\/uri\.salted-project\.eu\/dataModel.(.*)'
        expression = re.compile(smartdatamodels_pattern + r'|'+ fiware_pattern + r'|'+ salted_pattern)
        results = expression.findall(form["DatasetType"])

        type_ = [r for r in results[0] if r][0]
        if "/" not in type_: type_ = "Fiware" + "/" + type_
        
        dataset_form["type"] = type_.replace("/", ":")
        dataset_form["id"] = to_ckan_valid_name(dataset_form["type"])
        
        dataset_form["title"] = type_
        dataset_form["description"] = form["DatasetTypeDescription"]

        dataset_form["creator"] = [creator.strip() for creator in form["DatasetCreator"].split(",")]
        
        dataset_form["dataProvider"] = form["DatasetProvider"]

        themes = form["DatasetTypeTopic"].split("||")
        dataset_form["theme"] = [
            get_theme(int(theme.split(" ")[-1][:-3])) for theme in themes
        ]
        # t = get_theme(int(theme.split(" ").last()))

        dataset_form["language"] = get_language(int(form["DatasetLanguage"].split(" ")[-1][:-3])) 
        dataset_form["accessRights"] = get_access_rights(int(form["DatasetAccessRights"].split(" ")[-1][:-3]))

        dataset_form["keyword"] = [
            keyword.strip() for keyword in form["DatasetKeywords"].split(",")
        ]

        dataset_form["temporal"] = datetime.now(timezone.utc).isoformat().split("+")[0]
        locations = form["DatasetLocation"].split("||")
        dataset_form["spatial"] = [
            get_location(int(location.split(" ")[-1][:-3])) for location in locations
        ]

        # TODO: add extra attribute "context_url" or something like that in order to save the type context 
        #   context_link = (
        #       contexts + subject.lower() + '-context.jsonld'
        #       if subject in known_subjects
        #       else contexts + "default-context.jsonld"
        #   )

        return dataset_form

    def inject_dataset(self, catalog: Entity, form: dict) -> None:
        dataset_form = self.form_validate_dataset(form)
        dataset, distributions = self.create_new_dataset(catalog, dataset_form)

        if str(SDMDCAT["dataset"]) not in catalog.to_dict():
            catalog.rel(str(SDMDCAT["dataset"]), [dataset.id])
        else:
            if not isinstance(catalog[str(SDMDCAT["dataset"])].value, list):
                # https://github.com/jlanza/python-ngsild-client/blob/8e55ab2103a98b97826bb3b8a9fb8c26bc85682a/src/ngsildclient/model/entity.py#L190-L191
                #     >>> # Update a value using the dot notation
                #     >>> e["NO2.accuracy.value"] = 0.96
                catalog[str(SDMDCAT["dataset"])]["object"] = [ catalog[str(SDMDCAT["dataset"])].value ]
            
            if dataset.id not in catalog[str(SDMDCAT["dataset"])].value: # Append just new datasets
                catalog[str(SDMDCAT["dataset"])]["object"].append(dataset.id)
        
        self.ngsild_api.upsert(*distributions, dataset, catalog)

    def create_new_catalog(self, id) -> Entity:
        # ngsi-ld-core-context-v1.7.jsonld is stored in the context broker --> if not, uncomment DCTERMS["title"], DCTERMS["description"]
        catalog = Entity("Catalogue", id, ctx=self.context)
        catalog["type"] = str(SDMDCAT["Catalogue"])
        
        # .prop("name", DEFAULT_CATALOG["name"])
        catalog.prop(
            "title", DEFAULT_CATALOG["title"] # DCTERMS["title"], DEFAULT_CATALOG["title"]
        ).prop(
            "description", DEFAULT_CATALOG["description"], # DCTERMS["description"], DEFAULT_CATALOG["description"]
        ).prop(
            str(SDMDCAT["publisher"]), DEFAULT_CATALOG["publisher"]
        ).prop(
            str(SDMDCAT["homepage"]), DEFAULT_CATALOG["homepage"]
        ).prop(
            str(SDMDCAT["rights"]), DEFAULT_CATALOG["rights"]
        ).prop(
            str(SDMDCAT["license"]), DEFAULT_CATALOG["license"]
        ) 
        # .set_context(self.context)
        
        # catalog['id'] = create_id("Catalogue", id)

        return catalog

    def get_catalog(self, catalog_id: str) -> Entity:
        # Check if catalog exists
        try:
            id = "urn:ngsi-ld:Catalogue:" + catalog_id
            catalog = self.ngsild_api.get(id, ctx=self.context)
        except NgsiResourceNotFoundError as err:
            return None

        return catalog

    def inject_catalog(self, catalog_id: str) -> Entity:
        # Check if catalog exists
        catalog = self.get_catalog(catalog_id)
        if catalog != None:
            return catalog

        # Create organization as new catalog
        catalog = self.create_new_catalog(catalog_id)
        self.ngsild_api.create(catalog)

        catalog = self.get_catalog(catalog_id)
        # Return reference to catalog
        return catalog

    def create_new_csource(self, csource_id, entities, endpoint) -> dict:
        csource = {}
        csource["id"] = csource_id
        csource["type"] = "ContextSourceRegistration"
        csource["information"] = [{"entities": entities}]
        csource["endpoint"] = endpoint

        return csource

    def form_validate_csource(self, form):
        id = "urn:ngsi-ld:ContextSourceRegistration:" + form[
            "DatasetProvider" 
        ].replace(" ", "-") 
        # DatasetProvider --> TODO: should be an unique urn for each Broker federated. 
        # What if two different Brokers want to be federated and inject to the same organization?
        # DatasetCreator/DatasetProvider cannot be the organization name or some common name.

        endpoint = form["ScorpioSatelliteURL"] 
        if not is_valid_url(endpoint):
            raise Exception("Satellite URL is not a valid URL.")
            # (400, description="Satellite URL is not a valid URL.")

        # TODO: check against valid NGSI-LD Smart Data Models
        entity_type = form["DatasetType"]
        entity_pattern = form["DatasetIDPattern"]
        if not entity_pattern.startswith("urn:ngsi-ld:"):
            entity_pattern = "urn:ngsi-ld:" + entity_pattern

        return {
            "id": id,
            "endpoint": endpoint,
            "entity": {"type": entity_type, "idPattern": entity_pattern},
        }

    def get_csource(self, csource_id: str) -> CSourceRegistration:
        # Check if catalog exists
        try:
            csource = self.ngsild_api.csourceregs.get(csource_id)
        except NgsiResourceNotFoundError as err:
            return None
        return CSourceRegistration.from_dict(csource)

    def inject_csource(self, form) -> CSourceRegistration:
        # Retrieve the necessary data from the form
        csource_form = self.form_validate_csource(form)

        # Check if csource exists
        csource = self.get_csource(csource_form["id"])

        if csource is None:
            entity_info = RegistrationInfo.EntityInfo(
                type = csource_form["entity"]["type"],
                id_pattern = csource_form["entity"]["idPattern"],
            )
            csource = (
                CSourceRegistrationBuilder(
                    endpoint = csource_form["endpoint"],
                    information = RegistrationInfo([entity_info]),
                    context = [self.context],
                )
                .id(csource_form["id"])
                .build()
            )

            csource_id = self.ngsild_api.csourceregs.register(csource)

        else:
            # is it the type federated/registered too?
            if not any(csource_form["entity"]["type"] == e.type for e in csource.information[0].entities):
                # TODO: implement patch for cSourceRegistrations
                # Right now: DELETE and REGISTER the new and updated cSourceRegistarion

                # DELETE
                deleted = self.ngsild_api.csourceregs.delete(csource_form["id"])
                
                # CREATE and REGISTER new cSourceRegistration
                entity_info = csource.information[0].entities # Previous entity_info
                
                entity_info.append(RegistrationInfo.EntityInfo(
                    type = csource_form["entity"]["type"],
                    id_pattern = csource_form["entity"]["idPattern"],
                )) # New entity_info
                
                csource = (
                    CSourceRegistrationBuilder(
                        endpoint = csource_form["endpoint"],
                        information = RegistrationInfo(entity_info),
                        context = [self.context],
                    )
                    .id(csource_form["id"])
                    .build()
                )
                
                csource_id = self.ngsild_api.csourceregs.register(csource)

        # Get the last updated version
        csource = self.get_csource(csource_form["id"])

        return csource

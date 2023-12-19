# Dataset Registry
This respository contains the source code of the Dataset Registry module developed within the WP3 of the SALTED Project. The aim of this module is the registration of datasets, as part of the User Connector within the SALTED Platform to EDP connector. 

To this end, this component receives the information filled in by the partner in our [CKAN form](https://salted-project.eu/ckan-type-form/), transforms it to NGSI-LD using the DCAT-AP data models (Catalogue, Dataset and Distribution) provided by the Smart Data Models initiative, and it finally upserts these entities into the Federator Context Broker.
This way, fully customise descriptions are achieves, allowing the partners to characterise their datasets to their needs.


## Installation
Once you have the repository code in your machine, follow the next steps:
1. Create a `.env` file and add your information (parameters to change: `EXTERNAL_PORT`, `INTERNAL_PORT`, `HOST_NAME`).
    ```bash
    cp .env.template .env
    ```

2. Create a `config.json` file in the `src/` folder and set up the variables to your needs.
    ```bash
    cp config.json.template config.json
    ```

3. Deploy the docker
    ```bash
    docker-compose -f docker-compose.yml build
    docker-compose -f docker-compose.yml up

    # or do it together
    docker-compose -f docker-compose.yml up --build
    ```


## Authors
The Dataset Registry module has been written by:
- [Laura Martín](https://github.com/lauramartingonzalezzz)
- [Jorge Lanza](https://github.com/jlanza)
- [Víctor González](https://github.com/vgonzalez7)
- [Juan Ramón Santana](https://github.com/juanrasantana)
- [Pablo Sotres](https://github.com/psotres)
- [Luis Sánchez](https://github.com/sanchezgl)


## Acknowledgement
This work was supported by the European Commission CEF Programme by means of the project SALTED "Situation-Aware Linked heTerogeneous Enriched Data" under the Action Number 2020-EU-IA-0274.


## License
This material is licensed under the GNU Lesser General Public License v3.0 whose full text may be found at the *LICENSE* file.

It mainly makes use of the following libraries and frameworks (dependencies of dependencies have been omitted):

| Library / Framework |   Licence    |
|---------------------|--------------|
| Flask          | BSD          |
| ngsildclient             | Apache 2.0          |
| rdflib                 | BSD-3-Clause          |
| waitress          | ZPL 2.1          |
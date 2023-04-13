"""Tests federated SPARQL queries between the curies mapping service and popular triplestores."""

import unittest
from textwrap import dedent
from typing import Set, Tuple

from curies.mapping_service.utils import (
    get_sparql_record_so_tuples,
    get_sparql_records,
    sparql_service_available,
)
from tests.test_mapping_service import VALID_CONTENT_TYPES

# NOTE: federated queries need to use docker internal URL
LOCAL_MAPPING_SERVICE = "http://localhost:5000/sparql"
LOCAL_BLAZEGRAPH = "http://localhost:9999/blazegraph/namespace/kb/sparql"
LOCAL_VIRTUOSO = "http://localhost:8890/sparql"

DOCKER_MAPPING_SERVICE = "http://mapping-service:8888/sparql"
DOCKER_BLAZEGRAPH = "http://localhost:8080/blazegraph/namespace/kb/sparql"
DOCKER_VIRTUOSO = "http://virtuoso:8890/sparql"


def get_pairs(endpoint: str, sparql: str, accept: str) -> Set[Tuple[str, str]]:
    """Get a response from a given SPARQL query."""
    records = get_sparql_records(endpoint=endpoint, sparql=sparql, accept=accept)
    return get_sparql_record_so_tuples(records)


def require_service(url, name):
    """Skip a test unless the service is available."""
    return unittest.skipUnless(
        sparql_service_available(url), reason=f"No local {name} service is running on {url}"
    )

SPARQL_VALUES = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{DOCKER_MAPPING_SERVICE}> {{
        VALUES ?s {{ <http://purl.obolibrary.org/obo/CHEBI_24867> <http://purl.obolibrary.org/obo/CHEBI_24868> }} .
        ?s owl:sameAs ?o .
    }}
}}
""".rstrip()

SPARQL_SIMPLE = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{DOCKER_MAPPING_SERVICE}> {{
        <http://purl.obolibrary.org/obo/CHEBI_24867> owl:sameAs ?o .
        ?s owl:sameAs ?o .
    }}
}}
""".rstrip()


@require_service(LOCAL_MAPPING_SERVICE, "Mapping")
class TestSPARQL(unittest.TestCase):
    """Tests federated SPARQL queries between the curies mapping service and blazegraph/virtuoso triplestores.

    Run and init the required triplestores locally:
    1. docker compose up
    2. ./tests/resources/init_triplestores.sh
    """

    def assert_endpoint(self, endpoint: str, query: str, *, accept: str):
        """Assert the endpoint returns favorable results."""
        records = get_pairs(endpoint, query, accept=accept)
        self.assertIn(
            ("http://purl.obolibrary.org/obo/CHEBI_24867", "https://bioregistry.io/chebi:24867"),
            records,
        )

    @require_service(LOCAL_BLAZEGRAPH, "Blazegraph")
    def test_from_blazegraph_to_mapping_service(self):
        """Test a federated query from a Blazegraph triplestore to the curies service."""
        for mimetype in VALID_CONTENT_TYPES:
            with self.subTest(mimetype=mimetype):
                self.assert_endpoint(LOCAL_BLAZEGRAPH, SPARQL_SIMPLE, accept=mimetype)
                self.assert_endpoint(LOCAL_BLAZEGRAPH, SPARQL_VALUES, accept=mimetype)

    @require_service(LOCAL_VIRTUOSO, "Virtuoso")
    def test_from_virtuoso_to_mapping_service(self):
        """Test a federated query from a OpenLink Virtuoso triplestore to the curies service."""
        for mimetype in VALID_CONTENT_TYPES:
            with self.subTest(mimetype=mimetype):
                self.assert_endpoint(LOCAL_VIRTUOSO, SPARQL_SIMPLE, accept=mimetype)
                # TODO: Virtuoso fails to resolves VALUES in federated query
                # self.assert_endpoint(LOCAL_VIRTUOSO, SPARQL_VALUES, accept=mimetype)

    @require_service(DOCKER_VIRTUOSO, "Virtuoso")
    def test_from_mapping_service_to_virtuoso(self):
        """Test a federated query from the curies service to a OpenLink Virtuoso triplestore."""
        query = dedent(
            f"""\
                SELECT ?s ?o WHERE {{
                    <https://identifiers.org/uniprot/P07862> <http://www.w3.org/2002/07/owl#sameAs> ?s .
                    SERVICE <{DOCKER_VIRTUOSO}> {{
                        ?s ?p ?o .
                    }}
                }}
            """.rstrip()
        )
        for mimetype in VALID_CONTENT_TYPES:
            with self.subTest(mimetype=mimetype):
                records = get_pairs(LOCAL_MAPPING_SERVICE, query, accept=mimetype)
                self.assertGreater(len(records), 0)

    @require_service(LOCAL_BLAZEGRAPH, "Blazegraph")
    def test_from_mapping_service_to_blazegraph(self):
        """Test a federated query from the curies service to a OpenLink Virtuoso triplestore."""
        query = dedent(
            f"""\
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX bl: <https://w3id.org/biolink/vocab/>
                SELECT ?s ?o WHERE {{
                  <https://www.ensembl.org/id/ENSG00000006453> owl:sameAs ?s .
                
                  SERVICE <{LOCAL_BLAZEGRAPH}> {{
                      ?s bl:category ?o .
                  }}
                }}
            """.rstrip()
        )
        for mimetype in VALID_CONTENT_TYPES:
            with self.subTest(mimetype=mimetype):
                records = get_pairs(LOCAL_MAPPING_SERVICE, query, accept=mimetype)
                self.assertGreater(len(records), 0)
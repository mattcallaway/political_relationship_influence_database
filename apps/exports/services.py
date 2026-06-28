import csv
import json
import openpyxl
from io import StringIO, BytesIO
from apps.entities.models import Entity
from apps.assertions.models import Assertion

def export_entities_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['PublicID', 'CanonicalName', 'EntityType', 'Status', 'PublicationStatus'])
    for e in Entity.objects.all():
        writer.writerow([e.public_id, e.canonical_name, e.entity_type, e.status, e.publication_status])
    return output.getvalue()

def export_network_graphml():
    # Basic GraphML XML exporter for Gephi network analysis
    graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
    graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
    graphml.append('  <graph id="SonomaNetwork" edgedefault="directed">')
    
    # Nodes
    for e in Entity.objects.all():
        graphml.append(f'    <node id="{e.public_id}"><data key="name">{e.canonical_name}</data></node>')
        
    # Edges from assertions
    edge_id = 1
    for ast in Assertion.objects.filter(object_entity__isnull=False):
        graphml.append(f'    <edge id="e{edge_id}" source="{ast.subject_entity.public_id}" target="{ast.object_entity.public_id}"><data key="predicate">{ast.predicate}</data></edge>')
        edge_id += 1
        
    graphml.append('  </graph>')
    graphml.append('</graphml>')
    return '\n'.join(graphml)

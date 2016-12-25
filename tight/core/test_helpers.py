import pytest, os, sys, importlib, yaml, json, shutil
from botocore import session as boto_session
from tight.providers.aws.clients import boto3_client
from tight.providers.aws.clients import dynamo_db
import placebo

@pytest.fixture
def app():
    return importlib.import_module('app_index')

@pytest.fixture
def event():
    with open('tests/fixtures/lambda_proxy_event.yml') as data_file:
        event = yaml.load(data_file)
    return event

def placebos_path(file, namespace, mode='playback'):
    test_path = '/'.join(file.split('/')[0:-1])
    placebo_path = '/'.join([test_path, 'placebos'])
    namespaced_path = '{}/{}'.format(placebo_path, namespace)
    if mode == 'record':
        if os.path.exists(namespaced_path):
            shutil.rmtree(namespaced_path)
            os.mkdir(namespaced_path)
        else:
            os.mkdir(namespaced_path)
    return namespaced_path

def spy_on_session(file, session, placebo_path):
    pill = placebo.attach(session, data_path=placebo_path)
    return pill

def record(file, dynamo_db_session, namespace):
    this = sys.modules[__name__]
    placebo_path = placebos_path(file, namespace, mode='record')
    if not hasattr(this, 'pill') or not hasattr(this, 'boto3_pill'):
        boto3_session = boto3_client.session()
        boto3_pill = spy_on_session(file, boto3_session, placebo_path)
        boto3_pill.record()
        pill = spy_on_session(file, dynamo_db_session, placebo_path)
        os.environ['RECORD'] = 'True'
        pill.record()
        setattr(this, 'pill', pill)
        setattr(this, 'boto3_pill', boto3_pill)

def playback(file, dynamo_db_session, namespace):
    this = sys.modules[__name__]
    placebo_path = placebos_path(file, namespace, mode='playback')
    if not hasattr(this, 'pill') or not hasattr(this, 'boto3_pill'):
        boto3_session = boto3_client.session()
        boto3_pill = spy_on_session(file, boto3_session, placebo_path)
        boto3_pill.playback()
        pill = spy_on_session(file, dynamo_db_session, placebo_path)
        os.environ['PLAYBACK'] = 'True'
        pill.playback()
        setattr(this, 'pill', pill)
        setattr(this, 'boto3_pill', boto3_pill)
    else:
        getattr(this, 'pill')._data_path = placebos_path(file)
        getattr(this, 'boto3_pill')._data_path = placebos_path(file)

def expected_response_body(dir, expectation_file, actual_response):
    file_path = '/'.join([dir, expectation_file])
    if 'PLAYBACK' in os.environ and os.environ['PLAYBACK'] == 'True':
        return json.loads(yaml.load(open(file_path))['body'])
    if 'RECORD' in os.environ and os.environ['RECORD'] == 'True':
        stream = file(file_path, 'w')
        yaml.safe_dump(actual_response, stream)
        return json.loads(actual_response['body'])


@pytest.fixture
def dynamo_db_session():
    session =  getattr(dynamo_db, 'session') or None
    if session:
        return session
    else:
        session = boto_session.get_session()
        session.events = session.get_component('event_emitter')
        dynamo_db.session = session
        return session
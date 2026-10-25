"""Route checks using an in-memory MongoDB; never load .env or contact Atlas."""

import importlib

import sys

from datetime import datetime, timedelta

from pathlib import Path

from unittest.mock import patch


import mongomock

import pytest

from bson import ObjectId

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

with patch('pymongo.MongoClient', mongomock.MongoClient), patch('dotenv.load_dotenv'), patch.dict(
    'os.environ', {'SECRET_KEY': 'test-only-secret', 'MONGO_URI': 'mongodb://localhost', 'MONGO_DBNAME': 'test_byteme'}
):
    module = importlib.import_module('app')

module.app.config.update(TESTING=True)

OWNER = ObjectId('111111111111111111111111')

OTHER = ObjectId('222222222222222222222222')

ITEM = ObjectId('aaaaaaaaaaaaaaaaaaaaaaaa')

@pytest.fixture
def client():
    module.items.delete_many({})
    module.users.delete_many({})
    module.users.insert_many([{'_id': u, 'email': f'{u}@nyu.edu', 'password_hash': 'unused'} for u in [OWNER, OTHER]])
    module.items.insert_one(dict(_id=ITEM, owner_id=str(OWNER), type='lost', status='open',
        title='Original keys', description='Silver keys', category='Keys', building='Bobst Library',
        date=datetime(2026, 10, 20), contact='owner@nyu.edu', created_at=datetime(2026, 10, 20)))
    return module.app.test_client()

def login(client, user=OWNER):
    with client.session_transaction() as session:
        session['_user_id'] = str(user)
        session['_fresh'] = True


def matches(n):
    module.items.insert_many([dict(type='found', status='open', category='Keys', building='Bobst Library',
        title=f'Match {i:02}', created_at=datetime(2026,10,20)+timedelta(minutes=i)) for i in range(n)])

def test_claimed_hides_matches(client):
    matches(2)
    module.items.update_one({'_id': ITEM}, {'$set': {'status': 'claimed'}})
    for path in [f'/items/{ITEM}', f'/items/{ITEM}/matches']:
        response = client.get(path)
        assert b'already been claimed' in response.data
        assert b'Match 01' not in response.data

def test_preview_five_newest_and_view_more(client):
    matches(7)
    response = client.get(f'/items/{ITEM}')
    assert response.status_code == 200
    assert b'Match 06' in response.data and b'Match 02' in response.data
    assert b'Match 01' not in response.data
    assert b'View more matches' in response.data
    assert response.data.index(b'Match 06') < response.data.index(b'Match 02')

def test_no_view_more_for_five(client):
    matches(5)
    assert b'View more matches' not in client.get(f'/items/{ITEM}').data

def test_matches_paginate_and_filter(client):
    matches(12)
    module.items.insert_many([dict(type=t, status=s, category=c, building=b, title='Excluded', created_at=datetime.now())
        for t,s,c,b in [('lost','open','Keys','Bobst Library'),('found','claimed','Keys','Bobst Library'),
                        ('found','open','Other','Bobst Library'),('found','open','Keys','Other')]])
    first=client.get(f'/items/{ITEM}/matches')
    second=client.get(f'/items/{ITEM}/matches?page=2')
    assert b'Match 11' in first.data and b'Match 01' not in first.data and b'Next' in first.data
    assert b'Match 01' in second.data and b'Match 00' in second.data and b'Next' not in second.data
    assert b'Excluded' not in first.data + second.data

@pytest.mark.parametrize('page', ['0','-1','foo','10001'])
def test_invalid_page(client,page):
    assert client.get(f'/items/{ITEM}/matches?page={page}').status_code == 400

@pytest.mark.parametrize('value', ['bad','ffffffffffffffffffffffff'])
def test_invalid_item(client,value):
    assert client.get(f'/items/{value}').status_code == 404

def test_delete_get_and_cancel_preserve_item(client):
    login(client)
    response=client.get(f'/items/{ITEM}/delete?return_to=/search%3Fq%3Dkeys')
    assert response.status_code == 200
    assert b'Cancel' in response.data and b'csrf_token' in response.data
    assert 'deleted_at' not in module.items.find_one({'_id':ITEM})

def test_owner_buttons_hidden_for_guests(client):
    response=client.get(f'/items/{ITEM}')
    assert b'Delete post' not in response.data and b'Mark as claimed' not in response.data

def test_missing_match_fields(client):
    module.items.update_one({'_id':ITEM},{'$unset':{'category':''}})
    assert b'No possible matches yet' in client.get(f'/items/{ITEM}').data

@pytest.mark.parametrize('bad_token', ['', 'wrong', '\u2603'])
def test_delete_rejects_invalid_csrf(client,bad_token):
    login(client)
    # The confirmation page generates the token; viewing details need not create one.
    client.get(f'/items/{ITEM}/delete')
    response=client.post(f'/items/{ITEM}/delete',data={'csrf_token':bad_token})
    assert response.status_code==400
    assert module.items.find_one({'_id':ITEM}) is not None


def test_valid_delete(client):
    login(client)
    response=client.get(f'/items/{ITEM}/delete')
    assert b'csrf_token' in response.data
    with client.session_transaction() as session:
        csrf=session['csrf_token']
    response=client.post(f'/items/{ITEM}/delete',data={'csrf_token':csrf},follow_redirects=True)
    assert response.status_code==200 and b'Post deleted successfully.' in response.data
    assert module.items.find_one({'_id':ITEM}) is None
    assert client.get(f'/items/{ITEM}').status_code==404


def test_nonowner_cannot_delete(client):
    login(client,OTHER)
    assert client.get(f'/items/{ITEM}/delete').status_code==403
    assert client.post(f'/items/{ITEM}/delete').status_code==403
    assert module.items.find_one({'_id':ITEM}) is not None


def test_guest_cannot_delete(client):
    response=client.post(f'/items/{ITEM}/delete')
    assert response.status_code==302 and '/login' in response.location
    assert module.items.find_one({'_id':ITEM}) is not None


def test_reverse_matching_direction(client):
    module.items.update_one({'_id':ITEM},{'$set':{'type':'found'}})
    module.items.insert_one(dict(type='lost',status='open',category='Keys',building='Bobst Library',title='Lost match',created_at=datetime.now()))
    assert b'Lost match' in client.get(f'/items/{ITEM}').data

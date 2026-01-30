import asyncio
import pytest
from Client import Client


@pytest.fixture
def client():
    cl = Client()
    cl.connect()
    return cl



def test_set_get_delete(client):
    #SET
    client.set('key1', 'value1')

    #GET
    result =  client.get('key1')
    assert result == 'value1'


    #DELEYE
    client.delete('key1')
    result = client.get('key1')
    assert result == None


def test_mset_mget(client):
    #MSET
    client.mset('key1', 'value1','key2', 'value2','key3', 'value3')

    #MGET
    result =   client.mget('key1','key2','key3')

    assert result == ['value1','value2', 'value3']

def test_flush(client):
    #MSET
    client.mset('key1', 'value1','key2', 'value2','key3', 'value3')

    #FLUSH
    result =   client.flush()

    assert result == 3


    
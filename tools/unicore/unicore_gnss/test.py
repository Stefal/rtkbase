#! /usr/bin/env python3
from . unicore_cmd import UnicoGnss

def test_checksum():
    c = object.__new__(UnicoGnss)
    assert c._xor8_checksum('VERSIONA') == '1B'

def test_expected_res():
    c = object.__new__(UnicoGnss)
    c.debug = False
    assert c._expected_res_for('VERSIONA') == '$command,VERSIONA,response: OK*45'
    assert c._expected_res_for('FRESET') == '$command,FRESET,response: OK*4D'

def test_cmd_with_checksum():
    c = object.__new__(UnicoGnss)
    assert c._cmd_with_checksum('VERSIONA') == '$VERSIONA*1B'     


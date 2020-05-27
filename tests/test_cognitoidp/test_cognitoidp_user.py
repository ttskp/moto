from __future__ import unicode_literals

import json
import os
import random
import uuid

import boto3

# noinspection PyUnresolvedReferences
import sure  # noqa
from botocore.exceptions import ClientError
from jose import jws
from nose.tools import assert_raises

from moto import mock_cognitoidp
from moto.core import ACCOUNT_ID

from tests.test_cognitoidp.test_cognitoidp import authentication_flow


@mock_cognitoidp
def test_delete_user():
    conn = boto3.client("cognito-idp", "us-west-2")
    outputs = authentication_flow(conn)

    conn.delete_user(
        AccessToken=outputs["access_token"]
    )

    caught = False
    try:
        conn.admin_get_user(UserPoolId=outputs["user_pool_id"], Username=outputs["username"])
    except conn.exceptions.UserNotFoundException:
        caught = True

    caught.should.be.true


@mock_cognitoidp
def test_update_user_attributes():
    conn = boto3.client("cognito-idp", "us-west-2")

    outputs = authentication_flow(conn, user_attributes=[
        {"Name": "family_name", "Value": "Doe"},
        {"Name": "given_name", "Value": "John"},
    ])

    conn.update_user_attributes(
        AccessToken=outputs["access_token"],
        UserAttributes=[
            {"Name": "family_name", "Value": "Doe"},
            {"Name": "given_name", "Value": "Jane"},
        ],
    )

    user = conn.admin_get_user(UserPoolId=outputs["user_pool_id"], Username=outputs["username"])
    attributes = user["UserAttributes"]
    attributes.should.be.a(list)
    for attr in attributes:
        val = attr["Value"]
        if attr["Name"] == "family_name":
            val.should.equal("Doe")
        elif attr["Name"] == "given_name":
            val.should.equal("Jane")


@mock_cognitoidp
def test_delete_user_attributes():
    conn = boto3.client("cognito-idp", "us-west-2")

    outputs = authentication_flow(conn, user_attributes=[
        {"Name": "family_name", "Value": "Doe"},
        {"Name": "given_name", "Value": "John"},
        {"Name": "custom:company", "Value": "John Doe Inc."}
    ])

    conn.delete_user_attributes(
        AccessToken=outputs["access_token"],
        UserAttributeNames=["custom:company"]
    )

    user = conn.admin_get_user(UserPoolId=outputs["user_pool_id"], Username=outputs["username"])
    attributes = user["UserAttributes"]
    attributes.should.be.a(list)
    attributes_dict = {attr["Name"]: attr["Value"] for attr in attributes}

    assert "custom:company" not in attributes_dict
    assert "family_name" in attributes_dict
    assert "given_name" in attributes_dict

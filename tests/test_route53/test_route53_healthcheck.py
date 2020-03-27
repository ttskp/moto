from __future__ import unicode_literals

import boto3
import sure  # noqa

from moto import mock_route53


class Tests:

    conn = None
    checks = None

    @mock_route53
    def test_create_health_check(self):

        health_check_config = {
            "Type": "HTTP",
            "IPAddress": "10.0.0.25",
            "FullyQualifiedDomainName": "example.com",
            "Port": 80,
            "ResourcePath": "/",
            "SearchString": "a good response",
            "RequestInterval": 10,
            "FailureThreshold": 2,
        }

        self.given_connection()
        self.when_health_check_is_created_with(health_check_config)
        self.then_checks_should_be(health_check_config)

    @mock_route53
    def test_create_health_check_with_domain_name(self):

        health_check_config = {
            "Type": "HTTPS",
            "FullyQualifiedDomainName": "example.com",
            "Port": 443,
            "ResourcePath": "/search?q=term&format=json",
        }

        self.given_connection()
        self.when_health_check_is_created_with(health_check_config)
        self.then_checks_should_be({
            **health_check_config,
            "RequestInterval": 30,
            "FailureThreshold": 3,
        })

    @mock_route53
    def test_update_health_check(self):

        health_check_config = {
            "Type": "HTTPS",
            "FullyQualifiedDomainName": "example.com",
            "Port": 443,
            "ResourcePath": "/search?q=cloudformation&format=json",
        }

        self.given_connection()
        self.given_health_check(health_check_config)

        self.conn.update_health_check(
            HealthCheckId="",
            ResourcePath="/search?q=moto&format=json"
        )

        self.then_checks_should_be({
            **health_check_config,
            "ResourcePath": "/search?q=moto&format=json",
            "RequestInterval": 30,
            "FailureThreshold": 3,
        })


    @mock_route53
    def test_delete_health_check(self):

        health_check_config = {
            "Type": "HTTP",
            "IPAddress": "10.0.0.25",
            "Port": 80,
            "ResourcePath": "/"
        }

        self.given_connection()
        self.when_health_check_is_created_with(health_check_config)
        self.then_number_of_checks_should_be(1)

        self.when_health_check_is_deleted(self.checks[0]["Id"])
        self.then_number_of_checks_should_be(0)

    def given_connection(self):
        self.conn = boto3.client("route53", region_name="us-east-1")

    def given_health_check(self, health_check_config):
        self.checks = [self._create_health_check(health_check_config)]

    def when_health_check_is_created_with(self, health_check_config):
        self._create_health_check(health_check_config)

    def _create_health_check(self, health_check_config):
        return self.conn.create_health_check(
            CallerReference="caller",
            HealthCheckConfig=health_check_config
        )

    def when_health_check_is_deleted(self, health_check_id):
        self.conn.delete_health_check(HealthCheckId=health_check_id)

    def then_checks_should_be(self, expected_checks):
        self.checks = self.conn.list_health_checks()["HealthChecks"]
        list(self.checks).should.have.length_of(1)
        self.checks[0]["HealthCheckConfig"].should.equal(expected_checks)

    def then_number_of_checks_should_be(self, number):
        self.checks = self.conn.list_health_checks()["HealthChecks"]
        list(self.checks).should.have.length_of(number)

#!/usr/bin/env python3

import aws_cdk as cdk
import os

from kus_kus_stack.kus_kus_stack_stack import KusKusStackStack

app = cdk.App()
KusKusStackStack(app, "KusKusStackStack",
                 # If you don't specify 'env', this stack will be environment-agnostic.
                 # Account/Region-dependent features and context lookups will not work,
                 # but a single synthesized template can be deployed anywhere.
                 synthesizer=cdk.DefaultStackSynthesizer(qualifier="hb12tty"),
                 # Uncomment the next line to specialize this stack for the AWS Account
                 # and Region that are implied by the current CLI configuration.

                 env=cdk.Environment(account=os.getenv('CDK_DEPLOY_ACCOUNT'),
                                     region=os.getenv('CDK_DEPLOY_REGION')),

                 # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
                 )

app.synth()

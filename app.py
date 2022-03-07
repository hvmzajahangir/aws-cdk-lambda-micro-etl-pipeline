#!/usr/bin/env python3
import os

import aws_cdk as cdk

from etl_pipeline.stack import EtlPipelineStack


app = cdk.App()
EtlPipelineStack(app, "EtlPipelineStack")

app.synth()

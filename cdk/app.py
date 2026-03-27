#!/usr/bin/env python3
"""CDK app entry point for Human Design infrastructure."""

import os
import aws_cdk as cdk
from transcribe_stack import TranscribeStack
from transcription_api_stack import TranscriptionApiStack
from human_design_stack import HumanDesignStack

app = cdk.App()

# Human Design web app stack
hd_stack = HumanDesignStack(
    app,
    "HumanDesignStack",
    description="Human Design web application infrastructure",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

# Transcription Batch stack
transcribe_stack = TranscribeStack(
    app,
    "RaTranscribeStack",
    description="AWS Batch infrastructure for Ra Uru Hu lecture transcription",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

# Transcription API stack (depends on TranscribeStack and HumanDesignStack)
TranscriptionApiStack(
    app,
    "TranscriptionApiStack",
    description="FastAPI Lambda + API Gateway for transcription service",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()

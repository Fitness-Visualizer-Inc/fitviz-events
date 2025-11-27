"""Configuration for AWS SNS event publisher."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SNSPublisherConfig:
    """Configuration for SNSEventPublisher.

    Attributes:
        topic_arn: SNS topic ARN (e.g., "arn:aws:sns:us-east-2:123456789:domain-events")
        aws_region: AWS region for SNS service
        aws_access_key_id: AWS access key ID (optional, uses boto3 defaults if not provided)
        aws_secret_access_key: AWS secret access key (optional, uses boto3 defaults if not provided)
        use_localstack: Whether to use LocalStack for local development
        localstack_endpoint: LocalStack endpoint URL
        retry_attempts: Number of retry attempts for failed publishes
        retry_delay: Delay in seconds between retry attempts
        enable_validation: Whether to validate events using Pydantic schemas
    """

    topic_arn: str
    aws_region: str = "us-east-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    use_localstack: bool = False
    localstack_endpoint: Optional[str] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_validation: bool = True

    def to_boto3_config(self) -> dict:
        """Convert config to boto3 client kwargs.

        Returns:
            Dictionary of boto3 client configuration parameters
        """
        config = {"region_name": self.aws_region}

        if self.use_localstack and self.localstack_endpoint:
            config["endpoint_url"] = self.localstack_endpoint

        if self.aws_access_key_id:
            config["aws_access_key_id"] = self.aws_access_key_id

        if self.aws_secret_access_key:
            config["aws_secret_access_key"] = self.aws_secret_access_key

        return config

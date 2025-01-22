"""
Mock AWS Lambda Context

This module provides a mock implementation of the AWS Lambda context object
for local testing and development.
"""

class MockContext:
    """
    Mock AWS Lambda Context object that mimics the behavior and attributes
    of the real Lambda context.

    Attributes:
        function_name (str): Name of the Lambda function
        function_version (str): Version of the Lambda function
        memory_limit_in_mb (int): Memory limit in MB
        invoked_function_arn (str): ARN of the invoked function
        aws_request_id (str): Request ID for the current invocation
        log_group_name (str): CloudWatch Logs group name
        log_stream_name (str): CloudWatch Logs stream name
        identity (dict): Cognito identity information
        client_context (dict): Mobile client information
    """

    def __init__(
        self,
        function_name: str = "test-function",
        memory_limit: int = 128,
        remaining_time: int = 1000
    ):
        """
        Initialize mock context with default or custom values.

        Args:
            function_name (str): Name of the Lambda function
            memory_limit (int): Memory limit in MB
            remaining_time (int): Remaining execution time in milliseconds
        """
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = memory_limit
        self.invoked_function_arn = f"arn:aws:lambda:us-east-1:123456789012:function:{function_name}"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
        self.log_group_name = f"/aws/lambda/{function_name}"
        self.log_stream_name = "2024/01/22/[$LATEST]58419525dade4d17a495dceeeed44708"
        self._remaining_time_in_millis = remaining_time
        
        # Mobile SDK context information
        self.identity = None
        self.client_context = None

    def get_remaining_time_in_millis(self) -> int:
        """
        Returns the remaining execution time in milliseconds.

        Returns:
            int: Remaining time in milliseconds
        """
        return self._remaining_time_in_millis

    def set_remaining_time_in_millis(self, time: int) -> None:
        """
        Sets the remaining execution time for testing timeouts.

        Args:
            time (int): Time in milliseconds to set
        """
        self._remaining_time_in_millis = time

    @staticmethod
    def create_with_values(
        function_name: str = "test-function",
        memory_limit: int = 128,
        remaining_time: int = 1000,
        request_id: str = None,
        function_arn: str = None
    ) -> 'MockContext':
        """
        Creates a context with custom values for specific test scenarios.

        Args:
            function_name (str): Name of the Lambda function
            memory_limit (int): Memory limit in MB
            remaining_time (int): Remaining execution time in milliseconds
            request_id (str): Custom request ID
            function_arn (str): Custom function ARN

        Returns:
            MockContext: Configured context object
        """
        context = MockContext(function_name, memory_limit, remaining_time)
        
        if request_id:
            context.aws_request_id = request_id
            
        if function_arn:
            context.invoked_function_arn = function_arn
            
        return context

    def __str__(self) -> str:
        """
        Returns a string representation of the context.

        Returns:
            str: Context information
        """
        return (
            f"LambdaContext(function_name='{self.function_name}', "
            f"function_version='{self.function_version}', "
            f"memory_limit={self.memory_limit_in_mb}MB, "
            f"request_id='{self.aws_request_id}')"
        )

class CognitoIdentity:
    """
    Mock Cognito identity information for testing authentication scenarios.
    """

    def __init__(
        self,
        cognito_identity_id: str = "test-identity-id",
        cognito_identity_pool_id: str = "test-identity-pool-id"
    ):
        """
        Initialize Cognito identity information.

        Args:
            cognito_identity_id (str): Cognito identity ID
            cognito_identity_pool_id (str): Cognito identity pool ID
        """
        self.cognito_identity_id = cognito_identity_id
        self.cognito_identity_pool_id = cognito_identity_pool_id

class ClientContext:
    """
    Mock client context for testing mobile SDK integrations.
    """

    def __init__(
        self,
        client: dict = None,
        custom: dict = None,
        env: dict = None
    ):
        """
        Initialize client context information.

        Args:
            client (dict): Client information
            custom (dict): Custom values
            env (dict): Environment information
        """
        self.client = client or {
            "installation_id": "test-installation-id",
            "app_title": "test-app",
            "app_version_name": "1.0.0",
            "app_version_code": "1",
            "app_package_name": "com.test.app"
        }
        self.custom = custom or {}
        self.env = env or {}

def create_test_context(
    function_name: str = "test-function",
    with_cognito: bool = False,
    with_client_context: bool = False
) -> MockContext:
    """
    Creates a fully configured test context with optional Cognito and client information.

    Args:
        function_name (str): Name of the Lambda function
        with_cognito (bool): Whether to include Cognito identity
        with_client_context (bool): Whether to include client context

    Returns:
        MockContext: Configured context object
    """
    context = MockContext(function_name)
    
    if with_cognito:
        context.identity = CognitoIdentity()
        
    if with_client_context:
        context.client_context = ClientContext()
        
    return context

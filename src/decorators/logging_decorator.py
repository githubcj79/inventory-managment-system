"""
Logging decorator module using AWS Lambda Powertools.
"""

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from functools import wraps
from typing import Any, Callable, Dict

# Initialize logger - this can be imported and used across your application
logger = Logger(service="inventory-management")

def log_request(func: Callable) -> Callable:
    """
    Decorator to add structured logging for Lambda function requests.
    """
    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
        try:
            logger.append_keys(
                path=event.get('path', ''),
                method=event.get('httpMethod', ''),
                query_parameters=event.get('queryStringParameters'),
                path_parameters=event.get('pathParameters')
            )
            
            response = func(event, context)
            
            logger.info("Request completed successfully")
            return response
            
        except Exception:
            logger.exception("Request failed")
            return {
                "statusCode": 500,
                "body": '{"message": "Internal server error"}'
            }
            
    return wrapper

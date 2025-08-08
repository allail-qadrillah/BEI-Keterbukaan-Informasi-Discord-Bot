"""
AWS Lambda function entry point for IDX Discord Bot
"""
import asyncio
import json
import logging
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import main

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Response with status and results
    """
    try:
        logger.info("Lambda function started")
        
        # Run the async main function
        results = asyncio.run(main())
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'IDX Discord Bot executed successfully',
                'results': results
            })
        }
        
        logger.info(f"Lambda function completed successfully: {results}")
        return response
        
    except Exception as e:
        logger.error(f"Lambda function failed: {str(e)}")
        
        response = {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'IDX Discord Bot execution failed',
                'error': str(e)
            })
        }
        
        return response

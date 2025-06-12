#!/usr/bin/env python3

import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DatabaseError
from backend.config import Config

logger = logging.getLogger(__name__)

def wait_for_database(max_retries=30, initial_delay=1, max_delay=10):
    """
    Wait for database to be ready with exponential backoff retry logic.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (float): Initial delay between retries in seconds
        max_delay (float): Maximum delay between retries in seconds
    
    Returns:
        bool: True if database is ready, False if max retries exceeded
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            # Create a temporary engine to test connection
            engine = create_engine(
                Config.SQLALCHEMY_DATABASE_URI,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    'connect_timeout': 5,
                    'autocommit': True
                }
            )
            
            # Test the connection
            with engine.connect() as connection:
                # Test basic connectivity
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                
                # Test authentication by checking user permissions
                result = connection.execute(text("SELECT USER(), CONNECTION_ID()"))
                user_info = result.fetchone()
                logger.info(f"Database connection successful: {user_info[0]} (Connection ID: {user_info[1]})")
                
            engine.dispose()
            logger.info(f"Database ready after {attempt + 1} attempts")
            return True
            
        except (OperationalError, DatabaseError) as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            if attempt == max_retries - 1:
                logger.error(f"Database connection failed after {max_retries} attempts. Last error: {error_msg}")
                return False
            
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {error_msg}")
            logger.info(f"Retrying in {delay:.1f} seconds...")
            
            time.sleep(delay)
            
            # Exponential backoff with jitter
            delay = min(delay * 1.5, max_delay)
            
        except Exception as e:
            logger.error(f"Unexpected error during database connection attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep(delay)
            delay = min(delay * 1.5, max_delay)
    
    return False

def test_database_readiness():
    """
    Test if database is ready for application use.
    
    Returns:
        tuple: (is_ready: bool, error_message: str)
    """
    try:
        engine = create_engine(
            Config.SQLALCHEMY_DATABASE_URI,
            pool_pre_ping=True,
            connect_args={'connect_timeout': 5}
        )
        
        with engine.connect() as connection:
            # Test basic queries
            connection.execute(text("SELECT 1"))
            
            # Test if we can access information_schema (indicates proper permissions)
            connection.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"))
            
        engine.dispose()
        return True, None
        
    except Exception as e:
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        return False, error_msg 
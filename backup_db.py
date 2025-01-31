#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_database():
    try:
        # Get the current date for the backup file name
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define paths
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'instance', 'recipe_app.db')
        backup_dir = os.path.join(os.path.expanduser('~'), 'backups')
        backup_path = os.path.join(backup_dir, f'recipe_app_{date_str}.db')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Keep only the last 30 backups
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('recipe_app_')])
        if len(backups) > 30:
            for old_backup in backups[:-30]:
                os.remove(os.path.join(backup_dir, old_backup))
        
        logger.info(f'Database backup created successfully: {backup_path}')
        logger.info(f'Total backups: {len(backups)}')
        
    except Exception as e:
        logger.error(f'Backup failed: {str(e)}')
        raise


if __name__ == '__main__':
    backup_database()

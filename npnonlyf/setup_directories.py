"""
Utility script to manage data directories and ensure consistency between root and module data paths.
"""

import os
import logging
import shutil
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('directory_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define directory structure
ROOT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
MODULE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

DATA_SUBDIRS = ['pdfs', 'output', 'embeddings']

def setup_directories(use_symlinks=False, force_root=False):
    """
    Set up the directory structure, ensuring consistency between root and module data paths.
    
    Args:
        use_symlinks: If True, use symbolic links instead of copying files
        force_root: If True, use root data directory as the main one and link/copy to module dir
    """
    logger.info("Setting up data directories...")
    
    # Determine primary data directory
    primary_dir = ROOT_DATA_DIR if force_root else MODULE_DATA_DIR
    secondary_dir = MODULE_DATA_DIR if force_root else ROOT_DATA_DIR
    
    logger.info(f"Using {primary_dir} as primary data directory")
    
    # Create primary data directory and subdirectories
    os.makedirs(primary_dir, exist_ok=True)
    for subdir in DATA_SUBDIRS:
        os.makedirs(os.path.join(primary_dir, subdir), exist_ok=True)
    
    # Handle secondary data directory
    if os.path.exists(secondary_dir):
        logger.info(f"Secondary data directory {secondary_dir} exists")
        
        # Create symbolic links or copy files from secondary to primary
        for subdir in DATA_SUBDIRS:
            secondary_subdir = os.path.join(secondary_dir, subdir)
            primary_subdir = os.path.join(primary_dir, subdir)
            
            if os.path.exists(secondary_subdir):
                logger.info(f"Processing {secondary_subdir}")
                
                # Get all files in the secondary subdir
                for file in os.listdir(secondary_subdir):
                    src_file = os.path.join(secondary_subdir, file)
                    dst_file = os.path.join(primary_subdir, file)
                    
                    if os.path.isfile(src_file) and not os.path.exists(dst_file):
                        if use_symlinks:
                            # Create symbolic link
                            try:
                                os.symlink(src_file, dst_file)
                                logger.info(f"Created symlink: {dst_file} -> {src_file}")
                            except Exception as e:
                                logger.error(f"Failed to create symlink: {e}")
                                # Fall back to copy
                                shutil.copy2(src_file, dst_file)
                                logger.info(f"Copied file: {src_file} -> {dst_file}")
                        else:
                            # Copy the file
                            shutil.copy2(src_file, dst_file)
                            logger.info(f"Copied file: {src_file} -> {dst_file}")
    else:
        logger.info(f"Creating secondary data directory {secondary_dir}")
        os.makedirs(secondary_dir, exist_ok=True)
    
    # Now create symlinks or directories from primary to secondary for consistency
    for subdir in DATA_SUBDIRS:
        primary_subdir = os.path.join(primary_dir, subdir)
        secondary_subdir = os.path.join(secondary_dir, subdir)
        
        if not os.path.exists(secondary_subdir):
            if use_symlinks:
                # Create symbolic link to the directory
                try:
                    os.symlink(primary_subdir, secondary_subdir)
                    logger.info(f"Created symlink: {secondary_subdir} -> {primary_subdir}")
                except Exception as e:
                    logger.error(f"Failed to create symlink: {e}")
                    # Fall back to directory creation
                    os.makedirs(secondary_subdir, exist_ok=True)
                    logger.info(f"Created directory: {secondary_subdir}")
            else:
                # Create directory
                os.makedirs(secondary_subdir, exist_ok=True)
                logger.info(f"Created directory: {secondary_subdir}")
    
    logger.info("Directory setup complete")
    
    # Return the paths for reference
    return {
        'primary_data_dir': primary_dir,
        'secondary_data_dir': secondary_dir,
        'pdfs_dir': os.path.join(primary_dir, 'pdfs'),
        'output_dir': os.path.join(primary_dir, 'output'),
        'embeddings_dir': os.path.join(primary_dir, 'embeddings')
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Set up data directories for the application')
    parser.add_argument('--symlinks', action='store_true', help='Use symbolic links instead of copying files')
    parser.add_argument('--force-root', action='store_true', help='Force using root data directory as primary')
    
    args = parser.parse_args()
    
    paths = setup_directories(use_symlinks=args.symlinks, force_root=args.force_root)
    
    print("\nDirectory setup complete!")
    print("Data directories:")
    for name, path in paths.items():
        print(f"- {name}: {path}")

if __name__ == "__main__":
    main()

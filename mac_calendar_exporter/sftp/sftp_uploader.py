#!/usr/bin/env python3
"""
SFTP Upload Module.

This module handles uploading files to an SFTP server using paramiko.
"""

import logging
import os
from typing import Dict, Optional, Tuple, Union

import paramiko

logger = logging.getLogger(__name__)


class SFTPUploader:
    """Upload files to an SFTP server."""

    def __init__(
        self,
        hostname: str,
        port: int = 22,
        username: str = None,
        password: str = None,
        key_file: str = None,
        key_passphrase: str = None,
        timeout: int = 30,
    ):
        """
        Initialize the SFTP uploader.
        
        Args:
            hostname: SFTP server hostname
            port: SFTP server port
            username: Username for authentication
            password: Password for password authentication
            key_file: Path to SSH private key for key-based authentication
            key_passphrase: Passphrase for encrypted SSH private key
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.key_passphrase = key_passphrase
        self.timeout = timeout
        self._transport = None
        self._sftp = None

    def connect(self) -> bool:
        """
        Connect to the SFTP server.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            transport = paramiko.Transport((self.hostname, self.port))
            transport.connect(
                username=self.username,
                password=self.password,
            )
            
            # If key file is provided, try key-based authentication
            if self.key_file and os.path.isfile(self.key_file):
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(
                        self.key_file, password=self.key_passphrase
                    )
                    transport.auth_publickey(self.username, private_key)
                except Exception as e:
                    logger.error(f"Key-based authentication failed: {e}")
                    # Fall back to password auth if already provided
                    if not self.password:
                        raise

            self._transport = transport
            self._sftp = paramiko.SFTPClient.from_transport(transport)
            
            logger.info(f"Successfully connected to SFTP server {self.hostname}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SFTP server {self.hostname}: {e}")
            return False

    def disconnect(self) -> None:
        """Close the SFTP connection."""
        if self._sftp:
            self._sftp.close()
            self._sftp = None
            
        if self._transport:
            self._transport.close()
            self._transport = None
            
        logger.info("Disconnected from SFTP server")

    def upload_file(
        self, 
        local_file: str, 
        remote_path: str, 
        create_dirs: bool = True
    ) -> bool:
        """
        Upload a file to the SFTP server.
        
        Args:
            local_file: Path to the local file to upload
            remote_path: Path on the SFTP server to upload the file to
            create_dirs: If True, create remote directories if they don't exist
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not self._sftp:
            if not self.connect():
                return False
                
        try:
            # Check if local file exists
            if not os.path.isfile(local_file):
                logger.error(f"Local file does not exist: {local_file}")
                return False

            # Create remote directories if needed
            if create_dirs:
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    try:
                        self._create_remote_directory(remote_dir)
                    except Exception as e:
                        logger.error(f"Failed to create remote directory {remote_dir}: {e}")
                        return False
            
            # Upload the file
            self._sftp.put(local_file, remote_path)
            logger.info(f"Successfully uploaded {local_file} to {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file {local_file} to {remote_path}: {e}")
            return False
        finally:
            # Keep the connection open for potential future uploads
            pass
            
    def _create_remote_directory(self, directory: str) -> None:
        """
        Create a directory on the SFTP server, including any parent directories.
        
        Args:
            directory: Path to create on the SFTP server
        """
        if not directory:
            return
            
        # Strip trailing slash
        directory = directory.rstrip('/')
        
        try:
            self._sftp.stat(directory)
            # Directory exists
            return
        except IOError:
            # Directory doesn't exist, create parent directory first
            parent = os.path.dirname(directory)
            if parent and parent != directory:
                self._create_remote_directory(parent)
                
            # Create the directory
            self._sftp.mkdir(directory)
            logger.debug(f"Created remote directory: {directory}")


if __name__ == "__main__":
    # Simple test function when run directly
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
        tmp.write(b"This is a test file for SFTP upload")
    
    # Use environment variables for connection details (for security)
    hostname = os.environ.get('SFTP_HOST', 'example.com')
    username = os.environ.get('SFTP_USER', 'user')
    password = os.environ.get('SFTP_PASS', 'password')
    
    # Initialize uploader
    uploader = SFTPUploader(hostname, username=username, password=password)
    
    # Upload the test file
    remote_path = '/upload/test.txt'
    result = uploader.upload_file(tmp.name, remote_path)
    
    # Cleanup
    uploader.disconnect()
    os.unlink(tmp.name)
    
    print(f"Upload result: {'Success' if result else 'Failed'}")

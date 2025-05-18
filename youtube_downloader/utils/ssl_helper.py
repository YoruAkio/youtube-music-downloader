"""
SSL certificate handling for the YouTube Music Downloader.

This module provides functions to ensure SSL certificates 
work correctly when the application is frozen with PyInstaller.
"""

import os
import ssl
import sys
import certifi

def fix_ssl_certificates():
    """Fix SSL certificate verification for compiled executables.
    
    This function ensures that SSL certificates are properly configured
    when the application is frozen with PyInstaller.
    """
    try:
        # Check if we're in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # We are running in a PyInstaller bundle
            cert_path = certifi.where()
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            
            # Create a default SSL context with the certifi certificates
            ssl_context = ssl.create_default_context(cafile=cert_path)
            ssl._create_default_https_context = lambda: ssl_context
            
            print("SSL certificates configured for compiled executable")
            return True
    except Exception as e:
        print(f"Warning: Could not configure SSL certificates: {str(e)}")
    
    return False 
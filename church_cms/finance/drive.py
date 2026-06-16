"""
finance/drive.py

Helpers for loading and saving Google Drive OAuth credentials
from the database (DriveCredential model) instead of the session.

This means tokens survive logout, session clears, and server restarts.
"""

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def get_credentials(church):
    """
    Load stored credentials for a church from the DB.
    Automatically refreshes the access token if it has expired.
    Returns a Credentials object, or None if not connected.
    """
    from .models import DriveCredential

    try:
        record = DriveCredential.objects.get(church=church)
    except DriveCredential.DoesNotExist:
        return None

    creds = Credentials(
        token         = record.token,
        refresh_token = record.refresh_token,
        token_uri     = record.token_uri,
        client_id     = record.client_id,
        client_secret = record.client_secret,
        scopes        = record.scopes,
    )

    # If the access token is expired, refresh it and save the new token
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        record.token = creds.token
        record.save(update_fields=['token', 'updated_at'])

    return creds


def save_credentials(church, creds):
    """
    Save (or update) OAuth credentials for a church in the DB.
    Called after a successful OAuth callback and after each Drive operation
    so the refreshed access token is always persisted.
    """
    from .models import DriveCredential

    DriveCredential.objects.update_or_create(
        church=church,
        defaults={
            'token':         creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri':     creds.token_uri,
            'client_id':     creds.client_id,
            'client_secret': creds.client_secret,
            'scopes':        list(creds.scopes) if creds.scopes else [],
        },
    )


def delete_credentials(church):
    """Remove stored credentials — used when the admin disconnects Drive."""
    from .models import DriveCredential
    DriveCredential.objects.filter(church=church).delete()


def is_connected(church):
    """Quick check — does this church have credentials stored?"""
    from .models import DriveCredential
    return DriveCredential.objects.filter(church=church).exists()

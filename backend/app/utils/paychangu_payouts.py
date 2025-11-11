"""
PayChangu Payouts Integration
Handles bank transfers and mobile money payouts via PayChangu API
"""

import requests
from flask import current_app
from typing import Dict, Any


def initiate_bank_payout(
    amount: float,
    bank_uuid: str,
    account_name: str,
    account_number: str,
    charge_id: str
) -> Dict[str, Any]:
    """
    Initiate a bank transfer payout via PayChangu.
    
    Args:
        amount: Payout amount in MWK
        bank_uuid: Bank UUID from PayChangu banks list
        account_name: Recipient account name
        account_number: Recipient account number
        charge_id: Unique charge ID for tracking
    
    Returns:
        dict: PayChangu API response
    """
    api_key = current_app.config.get('PAYCHANGU_API_KEY')
    base_url = current_app.config.get('PAYCHANGU_BASE_URL', 'https://api.paychangu.com')
    
    if not api_key:
        raise ValueError("PayChangu API key not configured")
    
    url = f"{base_url}/direct-charge/payouts/initialize"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'payout_method': 'bank_transfer',
        'bank_uuid': bank_uuid,
        'amount': str(int(amount)),  # Convert to string as per API docs
        'charge_id': charge_id,
        'bank_account_name': account_name,
        'bank_account_number': account_number
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"PayChangu payout error: {str(e)}")
        
        # Try to extract error details from response
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get('message', str(e))
            except:
                error_detail = e.response.text or str(e)
        
        return {
            'status': 'error',
            'message': f'Failed to initiate payout: {error_detail}'
        }


def initiate_mobile_money_payout(
    amount: float,
    mobile_number: str,
    bank_uuid: str,  # Airtel Money or TNM Mpamba UUID
    charge_id: str,
    account_name: str = None
) -> Dict[str, Any]:
    """
    Initiate a mobile money payout via PayChangu.
    
    Args:
        amount: Payout amount in MWK
        mobile_number: Recipient mobile money number
        bank_uuid: Bank UUID for Airtel Money or TNM Mpamba
        charge_id: Unique charge ID for tracking
        account_name: Optional account holder name
    
    Returns:
        dict: PayChangu API response
    """
    api_key = current_app.config.get('PAYCHANGU_API_KEY')
    base_url = current_app.config.get('PAYCHANGU_BASE_URL', 'https://api.paychangu.com')
    
    if not api_key:
        raise ValueError("PayChangu API key not configured")
    
    url = f"{base_url}/direct-charge/payouts/initialize"
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'payout_method': 'bank_transfer',  # Same endpoint for mobile money
        'bank_uuid': bank_uuid,
        'amount': str(int(amount)),
        'charge_id': charge_id,
        'bank_account_number': mobile_number  # Mobile number goes here
    }
    
    if account_name:
        payload['bank_account_name'] = account_name
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"PayChangu mobile money payout error: {str(e)}")
        
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get('message', str(e))
            except:
                error_detail = e.response.text or str(e)
        
        return {
            'status': 'error',
            'message': f'Failed to initiate mobile money payout: {error_detail}'
        }


def verify_payout_status(ref_id: str) -> Dict[str, Any]:
    """
    Verify payout status using PayChangu reference ID.
    
    Args:
        ref_id: PayChangu reference ID (ref_id from initial response)
    
    Returns:
        dict: PayChangu API response with transaction status
    """
    api_key = current_app.config.get('PAYCHANGU_API_KEY')
    base_url = current_app.config.get('PAYCHANGU_BASE_URL', 'https://api.paychangu.com')
    
    if not api_key:
        raise ValueError("PayChangu API key not configured")
    
    # Endpoint for verifying payout status
    url = f"{base_url}/verify-payment/{ref_id}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"PayChangu verification error: {str(e)}")
        
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get('message', str(e))
            except:
                error_detail = e.response.text or str(e)
        
        return {
            'status': 'error',
            'message': f'Failed to verify payout: {error_detail}'
        }


def get_available_banks(currency: str = 'MWK') -> Dict[str, Any]:
    """
    Get list of available banks for payouts from PayChangu.
    This includes both banks and mobile money providers.
    
    Args:
        currency: Currency code (default: 'MWK' for Malawi Kwacha)
    
    Returns:
        dict: List of banks with their UUIDs
    """
    api_key = current_app.config.get('PAYCHANGU_API_KEY')
    base_url = current_app.config.get('PAYCHANGU_BASE_URL', 'https://api.paychangu.com')
    
    if not api_key:
        raise ValueError("PayChangu API key not configured")
    
    # Correct endpoint for getting supported banks
    url = f"{base_url}/direct-charge/payouts/supported-banks"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    params = {
        'currency': currency
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"PayChangu banks list error: {str(e)}")
        
        # Try to extract error details from response
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get('message', str(e))
            except:
                error_detail = e.response.text or str(e)
        
        return {
            'status': 'error',
            'message': f'Failed to fetch banks list: {error_detail}'
        }
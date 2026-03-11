from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from schemas.schemas import BankingAccountCreate, BankingAccountOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter()


@router.get("/", response_model=List[BankingAccountOut])
def list_accounts(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """
    List all banking accounts for current user.
    
    Returns empty array if user has no accounts.
    """
    user_id = current_user['user_id']
    result = supabase.table('banking_accounts').select('*').eq('user_id', user_id).execute()
    return result.data or []


@router.post("/", response_model=BankingAccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    body: BankingAccountCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Create a new banking account.
    
    Account types: savings, current, fixed_deposit, recurring_deposit
    """
    user_id = current_user['user_id']
    
    new_account = supabase.table('banking_accounts').insert({
        "user_id": user_id,
        "account_type": body.account_type,
        "account_name": body.account_name,
        "institution": body.institution,
        "account_number": body.account_number,
        "current_balance": body.current_balance,
        "currency": body.currency,
        "is_primary": body.is_primary
    }).execute()
    
    if not new_account.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )
    
    return new_account.data[0]


@router.put("/{account_id}", response_model=BankingAccountOut)
def update_account(
    account_id: str,
    updates: dict,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Update a banking account.
    
    Only the account owner can update their accounts.
    """
    user_id = current_user['user_id']
    
    # Verify ownership before update
    existing = supabase.table('banking_accounts')\
        .select('*')\
        .eq('account_id', account_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update account
    result = supabase.table('banking_accounts')\
        .update(updates)\
        .eq('account_id', account_id)\
        .execute()
    
    return result.data[0]


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Delete a banking account.
    
    Only the account owner can delete their accounts.
    Returns 204 No Content on success.
    """
    user_id = current_user['user_id']
    
    # Delete with ownership check
    result = supabase.table('banking_accounts')\
        .delete()\
        .eq('account_id', account_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return None
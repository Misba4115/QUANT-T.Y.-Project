"""
Chat Router — POST /chat
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from uuid import uuid4
import os

from schemas.schemas import ChatRequest, ChatResponse
from services.auth_service import get_current_user
from services.llm_service import generate_chat_response
from db.supabase_client import supabase

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Chat with AI assistant using user's financial context.
    """
    user_id = current_user['user_id']
    
    # Create or get conversation
    if body.conversation_id:
        conv_id = body.conversation_id
    else:
        new_conv = supabase.table('chat_conversations').insert({
            "user_id": user_id,
            "conversation_title": body.message[:50]
        }).execute()
        conv_id = new_conv.data[0]['conversation_id']
    
    # Store user message
    supabase.table('chat_messages').insert({
        "conversation_id": conv_id,
        "role": "user",
        "content": body.message
    }).execute()
    
    # Fetch user's financial context
    user_context = get_user_financial_context(user_id)
    
    # Get conversation history (last 10 messages)
    history = supabase.table('chat_messages')\
        .select('*')\
        .eq('conversation_id', conv_id)\
        .order('created_at')\
        .limit(10)\
        .execute()
    
    # Build messages for AI
    messages = [
        {
            "role": "system",
            "content": f"""You are QUANT, a friendly AI financial advisor for Indian retail investors. 

User Profile:
- Name: {current_user.get('name', 'Friend')}
- Monthly Income: ₹{current_user.get('monthly_income', 0):,.0f}
- Monthly Expenses: ₹{current_user.get('monthly_expenses', 0):,.0f}
- Risk Profile: {current_user.get('risk_profile', 'Not set')}
- Primary Goal: {current_user.get('primary_goal', 'Not set')}

{user_context}

RESPONSE GUIDELINES:
1. Keep responses SHORT (3-5 sentences, max 100 words)
2. Use **Markdown formatting** for better readability:
   - Use **bold** for key terms (SIP, RD, tax saving, etc.)
   - Use bullet points (*) for lists/options
   - Use line breaks for clarity
   - Highlight numbers with **bold** (₹30,000, 80C limit, etc.)
3. Be CONVERSATIONAL and friendly
4. REFERENCE their actual data
5. ASK one clarifying question at the end
6. Use Indian context (₹, NSE/BSE, 80C, etc.)

FORMAT EXAMPLE:
"That's great! I see you have **₹2.99L** in savings. For your goal, I'd suggest:

* **SIP in Index Funds** - Low cost, diversified
* **Debt Funds** - Safer for short-term goals

Do you have an emergency fund set aside?"

ALWAYS use this formatting style for readability."""
        }
    ]
    
    # Add conversation history (exclude the message we just added)
    for msg in history.data[:-1]:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": body.message
    })
    
    # Generate response via selected LLM provider
    try:
        reply = generate_chat_response(messages)
    except Exception as e:
        print(f"LLM service error: {e}")
        reply = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    # Store assistant message
    supabase.table('chat_messages').insert({
        "conversation_id": conv_id,
        "role": "assistant",
        "content": reply
    }).execute()
    
    return ChatResponse(
        reply=reply,
        conversation_id=conv_id
    )


def get_user_financial_context(user_id: str) -> str:
    """Fetch user's financial data to provide context to AI."""
    
    # Get accounts
    accounts = supabase.table('banking_accounts')\
        .select('account_name, account_type, current_balance')\
        .eq('user_id', user_id)\
        .execute()
    
    # Get equity holdings
    equity = supabase.table('equity_holdings')\
        .select('equity_name, quantity, current_value')\
        .eq('user_id', user_id)\
        .execute()
    
    # Get mutual funds
    mf = supabase.table('mutual_fund_holdings')\
        .select('mf_name, units, current_value')\
        .eq('user_id', user_id)\
        .execute()
    
    # Get goals
    goals = supabase.table('goals')\
        .select('goal_name, target_amount, current_saved, target_date')\
        .eq('user_id', user_id)\
        .execute()
    
    # Format context
    context = []
    
    if accounts.data:
        total_balance = sum(acc['current_balance'] for acc in accounts.data)
        context.append(f"Banking Accounts (Total: ₹{total_balance:,.2f}):")
        for acc in accounts.data:
            context.append(f"  - {acc['account_name']} ({acc['account_type']}): ₹{acc['current_balance']:,.2f}")
    
    if equity.data:
        total_equity = sum(stock.get('current_value', 0) for stock in equity.data)
        context.append(f"\nEquity Holdings (Total: ₹{total_equity:,.2f}):")
        for stock in equity.data:
            context.append(f"  - {stock['equity_name']}: {stock['quantity']} shares")
    
    if mf.data:
        total_mf = sum(fund.get('current_value', 0) for fund in mf.data)
        context.append(f"\nMutual Fund Holdings (Total: ₹{total_mf:,.2f}):")
        for fund in mf.data:
            context.append(f"  - {fund['mf_name']}: {fund['units']} units")
    
    if goals.data:
        context.append("\nFinancial Goals:")
        for goal in goals.data:
            progress = (goal['current_saved'] / goal['target_amount'] * 100) if goal.get('target_amount') else 0
            context.append(f"  - {goal['goal_name']}: ₹{goal['current_saved']:,.2f} / ₹{goal.get('target_amount', 0):,.2f} ({progress:.1f}% complete)")
    
    return "\n".join(context) if context else "No financial data recorded yet. Encourage the user to add their accounts, holdings, and goals for personalized advice."


@router.get("/conversations")
def list_conversations(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """List all chat conversations for the user."""
    user_id = current_user['user_id']
    
    result = supabase.table('chat_conversations')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('updated_at', desc=True)\
        .execute()
    
    return result.data or []


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """Fetch message history for a conversation."""
    user_id = current_user['user_id']
    
    # Verify ownership
    conv = supabase.table('chat_conversations')\
        .select('*')\
        .eq('conversation_id', conversation_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not conv.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = supabase.table('chat_messages')\
        .select('*')\
        .eq('conversation_id', conversation_id)\
        .order('created_at')\
        .execute()
    
    return messages.data or []
# QUANT Backend Implementation Plan (Updated)
**Date:** March 11, 2026  
**Status:** Authentication Complete, CRUD Routes In Progress  
**Priority:** Build out remaining CRUD endpoints to connect frontend

---

## 📊 Current Status Overview

### ✅ Completed Components

#### 1. Authentication System (100% Complete)
- **Technology:** Supabase Python Client (synchronous)
- **Status:** Fully functional and tested
- **Endpoints:**
  - `POST /auth/register` - User registration with JWT token
  - `POST /auth/login` - User login with JWT token
  - `GET /auth/me` - Get current user profile
- **Features:**
  - Password hashing with bcrypt
  - JWT token generation and validation
  - Protected routes with bearer token authentication
  - User session management

#### 2. Database Configuration (100% Complete)
- **Database:** PostgreSQL on Supabase
- **Connection Method:** Supabase Python Client (`supabase-py`)
- **Authentication:** Service role key (full database access)
- **Environment Variables:** Properly configured and loading
- **Schema:** All tables created and matching Pydantic models

#### 3. Project Structure (100% Complete)
- FastAPI application configured
- CORS middleware enabled
- Router organization established
- Pydantic schemas aligned with database
- Environment variable management working

---

## 🎯 Implementation Phases

### **PHASE 1: User Profile Management** (START HERE)
**Priority:** Critical - Frontend depends on this  
**Estimated Time:** 1-2 hours  
**Status:** Not Started

#### Objectives
Create `/user/profile` endpoints that the frontend expects for user management.

#### Tasks

##### 1.1 Create User Profile Router
**File:** `backend/routers/user.py` (NEW)

```python
"""
User Profile Router — GET /user/profile, PUT /user/profile
Frontend expects these endpoints for user management.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from schemas.schemas import UserOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter(prefix="/user", tags=["User"])


class ProfileUpdate(BaseModel):
    """Schema for profile update requests."""
    name: str | None = None
    phone: str | None = None
    age: int | None = None
    monthly_income: float | None = None
    monthly_expenses: float | None = None
    primary_goal: str | None = None
    risk_profile: str | None = None


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """
    Get current user profile.
    
    This is an alias of /auth/me for frontend compatibility.
    The frontend calls /user/profile instead of /auth/me.
    """
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    updates: ProfileUpdate,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Update user profile.
    
    Allows updating: name, phone, age, monthly_income, 
    monthly_expenses, primary_goal, risk_profile
    """
    user_id = current_user['user_id']
    
    # Only include non-None fields in update
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update in Supabase
    result = supabase.table('users').update(update_data).eq('user_id', user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    
    return result.data[0]
```

##### 1.2 Register User Router in Main App
**File:** `backend/main.py` (MODIFY)

Add this import:
```python
from routers import auth, user, banking, holdings, transactions, goals, dashboard, chat
```

Add this line after auth router:
```python
app.include_router(user.router)  # Adds /user/profile routes
```

##### 1.3 Testing Checklist
- [ ] Server starts without errors
- [ ] `GET /user/profile` returns current user (with Bearer token)
- [ ] `PUT /user/profile` updates name successfully
- [ ] `PUT /user/profile` updates risk_profile successfully
- [ ] Unauthorized requests (no token) return 401
- [ ] Swagger UI shows both endpoints under "User" tag

---

### **PHASE 2: Banking Accounts CRUD**
**Priority:** High - Core financial feature  
**Estimated Time:** 2-3 hours  
**Status:** Stubbed (501 responses)

#### Objectives
Implement full CRUD for banking accounts (savings, current, FD, RD accounts).

#### Tasks

##### 2.1 Implement Banking Router
**File:** `backend/routers/banking.py` (MODIFY)

Replace existing stub code with:

```python
"""
Banking Accounts Router
Manage user's banking accounts (savings, current, fixed deposits, etc.)
"""
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
```

##### 2.2 Testing Checklist
- [ ] `GET /banking-accounts/` returns empty array for new user
- [ ] `POST /banking-accounts/` creates savings account
- [ ] `POST /banking-accounts/` creates fixed deposit account
- [ ] `GET /banking-accounts/` returns created accounts
- [ ] `PUT /banking-accounts/{id}` updates balance
- [ ] `DELETE /banking-accounts/{id}` removes account
- [ ] Cannot delete another user's account (403/404)
- [ ] Cannot update another user's account (403/404)

---

### **PHASE 3: Goals CRUD**
**Priority:** High - User engagement feature  
**Estimated Time:** 2 hours  
**Status:** Stubbed (501 responses)

#### Objectives
Implement financial goals management (house, retirement, education, etc.).

#### Tasks

##### 3.1 Implement Goals Router
**File:** `backend/routers/goals.py` (MODIFY)

```python
"""
Goals Router
Manage user's financial goals (house, retirement, education, emergency fund, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from schemas.schemas import GoalCreate, GoalOut
from services.auth_service import get_current_user
from db.supabase_client import supabase

router = APIRouter()


@router.get("/", response_model=List[GoalOut])
def list_goals(current_user: Dict[Any, Any] = Depends(get_current_user)):
    """
    List all goals for current user.
    
    Returns empty array if user has no goals.
    """
    user_id = current_user['user_id']
    result = supabase.table('goals').select('*').eq('user_id', user_id).execute()
    return result.data or []


@router.post("/", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: GoalCreate,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Create a new financial goal.
    
    Goal types: house, retirement, education, emergency, wealth, custom
    """
    user_id = current_user['user_id']
    
    new_goal = supabase.table('goals').insert({
        "user_id": user_id,
        "goal_name": body.goal_name,
        "goal_type": body.goal_type,
        "target_amount": body.target_amount,
        "current_saved": body.current_saved,
        "target_date": str(body.target_date) if body.target_date else None
    }).execute()
    
    if not new_goal.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )
    
    return new_goal.data[0]


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: str,
    updates: dict,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Update a goal.
    
    Can update: goal_name, target_amount, current_saved, target_date
    """
    user_id = current_user['user_id']
    
    result = supabase.table('goals')\
        .update(updates)\
        .eq('goal_id', goal_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return result.data[0]


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: Dict[Any, Any] = Depends(get_current_user)
):
    """
    Delete a goal.
    
    Only the goal owner can delete their goals.
    """
    user_id = current_user['user_id']
    
    result = supabase.table('goals')\
        .delete()\
        .eq('goal_id', goal_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return None
```

##### 3.2 Testing Checklist
- [ ] `GET /goals/` returns empty array for new user
- [ ] `POST /goals/` creates retirement goal
- [ ] `POST /goals/` creates house purchase goal
- [ ] `GET /goals/` returns created goals
- [ ] `PUT /goals/{id}` updates target_amount
- [ ] `PUT /goals/{id}` updates current_saved
- [ ] `DELETE /goals/{id}` removes goal
- [ ] Cannot access another user's goals

---

### **PHASE 4: Holdings CRUD**
**Priority:** Medium - Investment tracking  
**Estimated Time:** 4-5 hours  
**Status:** Stubbed (501 responses)

#### Objectives
Implement CRUD for all 4 asset types: Equity, Mutual Funds, ETFs, Crypto.

#### Tasks

##### 4.1 Implement Equity Holdings
**File:** `backend/routers/holdings.py` (MODIFY)

Pattern for all 4 asset types:
- `GET /holdings/equity` - List user's equity holdings
- `POST /holdings/equity` - Add new equity holding
- `DELETE /holdings/equity/{id}` - Remove equity holding

Tables to implement:
- `equity_holdings` (equity_holding_id)
- `mutual_fund_holdings` (mf_holding_id)
- `etf_holdings` (etf_holding_id)
- `crypto_holdings` (crypto_holding_id)

##### 4.2 CSV Upload Stubs
For now, implement CSV endpoints as **parse-only** (no database insertion):
- `POST /holdings/equity/upload-csv` - Parse and return preview
- `POST /holdings/mf/upload-cas` - Parse and return preview

Full import implementation can be done later.

##### 4.3 Testing Checklist
- [ ] Create equity holding for HDFCBANK
- [ ] Create mutual fund holding for SBI Bluechip
- [ ] Create ETF holding for NIFTYBEES
- [ ] Create crypto holding for BTC
- [ ] List holdings returns all assets
- [ ] Delete holdings work correctly
- [ ] CSV upload returns parsed data (no insert)

---

### **PHASE 5: Transactions Management**
**Priority:** Medium - Transaction tracking  
**Estimated Time:** 3 hours  
**Status:** Stubbed (501 responses)

#### Objectives
Implement transaction tracking for bank transactions (credit/debit).

#### Tasks

##### 5.1 Implement Bank Transactions
**File:** `backend/routers/transactions.py` (MODIFY)

```python
@router.get("/bank", response_model=List[BankTransactionOut])
def list_bank_transactions(current_user: Dict = Depends(get_current_user)):
    """List all bank transactions for user."""
    user_id = current_user['user_id']
    result = supabase.table('bank_transactions')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('tx_date', desc=True)\
        .execute()
    return result.data or []


@router.post("/bank", response_model=BankTransactionOut, status_code=201)
def create_bank_transaction(
    body: BankTransactionCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Record a new bank transaction."""
    # Implementation similar to other CRUD endpoints
    pass


@router.delete("/bank/{tx_id}", status_code=204)
def delete_bank_transaction(
    tx_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a bank transaction."""
    # Implementation with ownership check
    pass
```

##### 5.2 Handle Unsupported Asset Types
For equity/mf/etf/crypto transactions, return 400 error:
```python
@router.get("/{asset_type}")
def get_transactions(asset_type: str):
    if asset_type not in ["bank"]:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction tracking for {asset_type} not yet implemented"
        )
```

##### 5.3 Testing Checklist
- [ ] Create debit transaction (Food)
- [ ] Create credit transaction (Salary)
- [ ] List transactions ordered by date
- [ ] Delete transaction
- [ ] Unsupported asset types return 400

---

### **PHASE 6: Dashboard (Without AI)**
**Priority:** Medium - User overview  
**Estimated Time:** 3-4 hours  
**Status:** Stubbed (501 responses)

#### Objectives
Create a working dashboard that computes real data from database (no AI agents yet).

#### Tasks

##### 6.1 Implement Dashboard Generation
**File:** `backend/routers/dashboard.py` (MODIFY)

```python
@router.post("/generate", response_model=DashboardRunOut)
def generate_dashboard(
    body: DashboardGenerateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate dashboard with real data from database.
    
    Computes:
    - net_worth (sum of all accounts + holdings)
    - asset_allocation (percentage breakdown)
    - top_holdings (top 5 by value)
    - cashflow (income vs expenses)
    """
    user_id = current_user['user_id']
    
    # Fetch all user data
    accounts = supabase.table('banking_accounts').select('*').eq('user_id', user_id).execute()
    equity = supabase.table('equity_holdings').select('*').eq('user_id', user_id).execute()
    mf = supabase.table('mutual_fund_holdings').select('*').eq('user_id', user_id).execute()
    goals = supabase.table('goals').select('*').eq('user_id', user_id).execute()
    
    # Compute metrics
    total_cash = sum(acc['current_balance'] for acc in accounts.data or [])
    total_equity = sum(h['current_value'] or 0 for h in equity.data or [])
    total_mf = sum(h['current_value'] or 0 for h in mf.data or [])
    
    net_worth = total_cash + total_equity + total_mf
    
    dashboard_data = {
        "net_worth": net_worth,
        "asset_allocation": {
            "cash": total_cash,
            "equity": total_equity,
            "mutual_funds": total_mf
        },
        "top_holdings": [],  # TODO: Sort and get top 5
        "goals_progress": goals.data or []
    }
    
    return {
        "run_id": str(uuid.uuid4()),
        "status": "completed",
        "result": dashboard_data
    }
```

##### 6.2 Configuration Endpoints
```python
@router.get("/config")
def get_dashboard_config(current_user: Dict = Depends(get_current_user)):
    """Get user's dashboard widget preferences."""
    # Return default or user-saved config
    pass

@router.put("/config")
def update_dashboard_config(
    body: dict,
    current_user: Dict = Depends(get_current_user)
):
    """Update dashboard widget preferences."""
    pass
```

##### 6.3 Testing Checklist
- [ ] Dashboard generates with no holdings (all zeros)
- [ ] Dashboard shows correct net worth with accounts
- [ ] Dashboard shows asset allocation correctly
- [ ] Dashboard config can be saved and retrieved

---

### **PHASE 7: Chat System (Basic)**
**Priority:** Low - Advanced feature  
**Estimated Time:** 6-8 hours  
**Status:** Stubbed (501 responses)

#### Prerequisites
- [ ] Qdrant running locally: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] OpenAI API key in `.env`
- [ ] Test documents in Qdrant for RAG

#### Objectives
Implement basic chat without full RAG pipeline initially.

#### Phase 7A: Simple Chat (No RAG)
**File:** `backend/routers/chat.py` (MODIFY)

```python
@router.post("/", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Simple chat endpoint (no RAG for now).
    
    Just echoes back user message for testing.
    Later: Integrate with LangGraph + Qdrant.
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
    
    # Simple response (placeholder for AI)
    reply = f"I received your message: {body.message}"
    
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
```

#### Phase 7B: RAG Integration (Later)
After basic chat works, integrate:
1. Qdrant for document search
2. OpenAI for response generation
3. LangGraph for orchestration
4. Embeddings for semantic search

---

## 🗓️ Recommended Timeline

### Week 1: Core CRUD
- **Day 1:** User Profile (Phase 1)
- **Day 2:** Banking Accounts (Phase 2)
- **Day 3:** Goals (Phase 3)
- **Day 4:** Testing & Bug Fixes
- **Day 5:** Frontend Integration Testing

### Week 2: Extended Features
- **Day 1-2:** Holdings (Phase 4)
- **Day 3:** Transactions (Phase 5)
- **Day 4:** Dashboard (Phase 6)
- **Day 5:** Testing & Documentation

### Week 3: Advanced Features (Optional)
- **Day 1-3:** Chat System (Phase 7)
- **Day 4:** Qdrant + RAG Setup
- **Day 5:** Final Testing & Demo Prep

---

## 📝 Testing Strategy

### Unit Testing (Per Endpoint)
For each endpoint, test:
1. ✅ Success case (200/201 response)
2. ✅ Authentication required (401 without token)
3. ✅ Ownership validation (404 for other user's data)
4. ✅ Input validation (422 for invalid data)
5. ✅ Error handling (500 for database errors)

### Integration Testing
1. Create user → Add account → Add goal → Generate dashboard
2. Create holdings → Update prices → Check dashboard values
3. Full user journey from registration to dashboard view

### Manual Testing Checklist
- [ ] All endpoints appear in Swagger UI
- [ ] Swagger UI "Try it out" works for each endpoint
- [ ] Frontend can connect and display data
- [ ] No CORS errors in browser console
- [ ] Token authentication works across all routes

---

## 🚨 Known Issues & Workarounds

### Issue 1: Frontend expects /user/profile
**Solution:** Phase 1 creates this endpoint as alias to /auth/me

### Issue 2: Async SQLAlchemy complications
**Solution:** Using Supabase client instead (synchronous, simpler)

### Issue 3: Qdrant not installed
**Workaround:** Skip chat features until Qdrant is set up

### Issue 4: OpenAI API costs
**Workaround:** Use simple responses first, add AI later

---

## 🔧 Environment Setup

### Required .env Variables
```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI (Optional - for Phase 7)
OPENAI_API_KEY=sk-...

# Vector DB (Optional - for Phase 7)
QDRANT_URL=http://localhost:6333
```

### Dependencies Check
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installations
python -c "from supabase import create_client; print('✅ Supabase OK')"
python -c "from fastapi import FastAPI; print('✅ FastAPI OK')"
python -c "from jose import jwt; print('✅ JWT OK')"
```

---

## 📚 Resources & Documentation

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Database Schema
- Location: `backend/schema.sql`
- Tables: 15 total (users, holdings, transactions, goals, etc.)

### Code Style
- Follow existing patterns in `auth_service.py`
- Use Supabase client for all database operations
- Return proper HTTP status codes (200, 201, 204, 404, 500)
- Include docstrings for all endpoints

---

## ✅ Success Criteria

### Phase 1-3 Complete
- [ ] User can register and login
- [ ] User can view/update profile
- [ ] User can manage banking accounts
- [ ] User can create and track goals
- [ ] Frontend displays all data correctly

### Phase 4-6 Complete
- [ ] User can add investment holdings
- [ ] User can track transactions
- [ ] Dashboard shows accurate net worth
- [ ] Dashboard shows asset allocation

### Phase 7 Complete (Stretch Goal)
- [ ] User can chat with AI assistant
- [ ] Chat provides relevant financial advice
- [ ] Chat references user's actual data

---

## 🎯 Next Immediate Action

**START HERE:**

1. Create `backend/routers/user.py` with the code from Phase 1
2. Update `backend/main.py` to include the user router
3. Start server: `uvicorn main:app --reload`
4. Test in Swagger: `http://localhost:8000/docs`
5. Verify `GET /user/profile` returns your user data

**After user profile works, move to Phase 2 (Banking).**

---

## 📞 Support & Questions

If you encounter issues:
1. Check server logs in terminal
2. Verify .env variables are loaded
3. Test endpoint in Swagger UI first
4. Check Supabase dashboard for data
5. Review this document for solutions

---

**Document Version:** 2.0  
**Last Updated:** March 11, 2026  
**Next Review:** After Phase 3 completion

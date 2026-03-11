# API Endpoint Verification Report

## Summary
**Status**: ⚠️ **ISSUES FOUND** - Not all Frontend API calls match Backend endpoints

---

## Frontend API Definitions (`frontend/lib/api.ts`)

### ✅ Auth API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/auth/register` | POST | authApi.register() | ✅ Exists | ✓ |
| `/auth/login` | POST | authApi.login() | ✅ Exists | ✓ |
| `/auth/me` | GET | userApi.getProfile() | ✅ Exists | ✓ |

### ✅ User API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/user/profile` | GET | userApi.getProfile() | ✅ Exists (alias: /auth/me) | ✓ |
| `/user/profile` | PUT | userApi.updateProfile() | ✅ Exists | ✓ |

### ✅ Banking API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/banking-accounts/` | GET | bankingApi.getBankAccounts() | ✅ Exists | ✓ |
| `/banking-accounts/` | POST | bankingApi.addBankAccount() | ✅ Exists | ✓ |

### ✅ Holdings API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/holdings/equity` | GET | equityApi.getEquityHoldings() | ✅ Exists | ✓ |
| `/holdings/equity` | POST | equityApi.createEquityHolding() | ✅ Exists | ✓ |
| `/holdings/equity/{id}` | DELETE | equityApi.deleteEquityHolding() | ✅ Exists | ✓ |
| `/holdings/equity/upload-csv` | POST | equityApi.uploadEquityCSV() | ✅ Exists | ✓ |
| `/holdings/mf` | GET | mutualFundApi.getMutualFundHoldings() | ✅ Exists | ✓ |
| `/holdings/mf` | POST | mutualFundApi.createMutualFundHolding() | ✅ Exists | ✓ |
| `/holdings/mf/{id}` | DELETE | mutualFundApi.deleteMutualFundHolding() | ✅ Exists | ✓ |
| `/holdings/mf/upload-cas` | POST | mutualFundApi.uploadCASFile() | ✅ Exists | ✓ |
| `/holdings/etf` | GET | etfApi.getETFHoldings() | ✅ Exists | ✓ |
| `/holdings/etf` | POST | etfApi.createETFHolding() | ✅ Exists | ✓ |
| `/holdings/etf/{id}` | DELETE | etfApi.deleteETFHolding() | ✅ Exists | ✓ |
| `/holdings/crypto` | GET | cryptoApi.getCryptoHoldings() | ✅ Exists | ✓ |
| `/holdings/crypto` | POST | cryptoApi.createCryptoHolding() | ✅ Exists | ✓ |
| `/holdings/crypto/{id}` | DELETE | cryptoApi.deleteCryptoHolding() | ✅ Exists | ✓ |

### ✅ Transactions API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/transactions/bank` | GET | transactionsApi.getBankTransactions() | ✅ Exists | ✓ |
| `/transactions/bank` | POST | transactionsApi.createBankTransaction() | ✅ Exists | ✓ |
| `/transactions/bank/{id}` | DELETE | transactionsApi.deleteBankTransaction() | ✅ Exists | ✓ |

### ✅ Goals API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/goals/` | GET | goalsApi.getGoals() | ✅ Exists | ✓ |
| `/goals/` | POST | goalsApi.createGoal() | ✅ Exists | ✓ |
| `/goals/{id}` | PUT | goalsApi.updateGoal() | ✅ Exists | ✓ |
| `/goals/{id}` | DELETE | goalsApi.deleteGoal() | ✅ Exists | ✓ |

### ⚠️ Dashboard API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/dashboard/generate` | POST | dashboardApi.generateDashboard() | ❌ **Not Implemented** | ✗ |
| `/dashboard/result/{run_id}` | GET | dashboardApi.getDashboardResult() | ❌ **Not Implemented** | ✗ |

### ⚠️ Chat API
| Endpoint | Method | Frontend | Backend | Status |
|----------|--------|----------|---------|--------|
| `/chat/` | POST | ❌ **Not in lib/api.ts** | ❌ **Not Implemented** | ✗ |
| `/chat/conversations` | GET | ❌ **Not in lib/api.ts** | ❌ **Not Implemented** | ✗ |
| `/chat/conversations/{id}/messages` | GET | ❌ **Not in lib/api.ts** | ❌ **Not Implemented** | ✗ |

---

## **CRITICAL ISSUES FOUND** 🚨

### Issue #1: Incorrect API Reference in Frontend
**File**: [frontend/app/input-data/page.tsx](frontend/app/input-data/page.tsx#L41)
**Line**: 41

**Problem**: 
```typescript
const res = await financialApi.getBankAccounts();
// ...
await financialApi.addBankAccount({...})
```

The code references `financialApi` which **does NOT exist** in [frontend/lib/api.ts](frontend/lib/api.ts).

**Resolution**: Change to use the correct API:
```typescript
const res = await bankingApi.getBankAccounts();
// ...
await bankingApi.addBankAccount({...})
```

---

### Issue #2: Not Implemented Endpoints
Backend endpoints exist but return 501 (Not Implemented):

1. **Dashboard Generation**
   - [backend/routers/dashboard.py](backend/routers/dashboard.py#L13-L23)
   - Status: Returns `HTTPException(status_code=501)`
   - Frontend still calls it via [dashboardApi.generateDashboard()](frontend/lib/api.ts#L157)

2. **Chat Endpoints** 
   - [backend/routers/chat.py](backend/routers/chat.py)
   - All endpoints return 501
   - Frontend chatbot doesn't call API yet (placeholder mode)

3. **Dashboard Config**
   - `/dashboard/config` endpoints not exposed in frontend API

---

### Issue #3: Transactions for Non-Bank Assets
**Status**: Expected limitation (documented)
- Endpoints for equity, MF, ETF, crypto transactions return 400 Bad Request
- This is intentional per [backend/routers/transactions.py](backend/routers/transactions.py#L77-L100)
- Only `/transactions/bank` is fully implemented

---

## Wiring Status Summary

| Category | Status | Notes |
|----------|--------|-------|
| Auth | ✅ Fully Wired | All endpoints implemented |
| User Profile | ✅ Fully Wired | All endpoints implemented |
| Banking | ✅ Fully Wired | All endpoints implemented |
| Holdings | ✅ Fully Wired | All endpoints implemented |
| Transactions | ✅ Partially Wired | Only bank transactions; others 400 Bad Request (intentional) |
| Goals | ✅ Fully Wired | All endpoints implemented |
| Dashboard | ⚠️ Not Implemented | Returns 501; needs agent implementation |
| Chat | ⚠️ Not Implemented | Returns 501; frontend doesn't call it yet |

---

## Recommendations

### Priority 1 (Critical - Breaks Functionality)
1. **Fix `financialApi` reference in input-data/page.tsx**
   - Change `financialApi` → `bankingApi`
   - This will cause runtime errors if input-data page is accessed

### Priority 2 (Medium - Incomplete Features)
1. Implement `/dashboard/generate` and `/dashboard/result/{run_id}` endpoints
2. Implement `/chat/*` endpoints with RAG system
3. Add `/dashboard/config` endpoints for widget preferences

### Priority 3 (Low - Non-Critical)
1. Document the intentional 400 responses for non-bank transactions
2. Consider exposing transaction tracking for other asset types in future

---

## Backend Router Configuration
**File**: [backend/main.py](backend/main.py#L25-L32)

```python
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(banking.router, prefix="/api/banking-accounts", tags=["Banking"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(user.router, prefix="/api")  # /user endpoints
```

✅ All routers are registered and CORS is configured correctly for `localhost:3000`.

---

## Axios Configuration
**File**: [frontend/lib/axios.ts](frontend/lib/axios.ts)
**Base URL**: Should point to `http://localhost:8000/api` or your backend server
✅ Token is automatically added to all requests via interceptor

---

Generated: 2025-03-12

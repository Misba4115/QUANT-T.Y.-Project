import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from main import app
from db.supabase_client import supabase
import uuid
import traceback

client = TestClient(app)

# Register dummy
email = f'test_{uuid.uuid4().hex[:8]}@example.com'
res = client.post('/auth/register', json={
    'name': 'Err Test', 'email': email, 'password': 'Sec123!Password',
    'age': 20, 'monthly_income': 1000, 'monthly_expenses': 500, 'primary_goal': 'wealth'
})
token = res.json()['access_token']

try:
    # Make transaction request
    body = {'tx_date': '2024-01-15', 'description': 'Food', 'amount': 450.0, 'tx_type': 'debit', 'category': 'Food'}
    print('SENDING:', body)
    resp = client.post('/transactions/bank', headers={'Authorization': f'Bearer {token}'}, json=body)
    print('STATUS:', resp.status_code)
    print('BODY:', resp.text)
except Exception as e:
    traceback.print_exc()

# Cleanup
supabase.table('users').delete().eq('email', email).execute()
print("Done")

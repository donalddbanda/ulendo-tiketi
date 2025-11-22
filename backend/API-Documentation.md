# Ulendo Tiketi API documentation

## Authorization

*POST /api/auth/register*
#### Register a new user
### Request body:
```json
{
    "name": "John Doe",
    "email": "johndoe@example.com", // optional
    "phone_number": "0912345678",
    "password": "pass1234"
}
```
### Response body:
```json
{
    "message": "account registered",
    "user":{ 
        "id": 1,
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "phone": "0912345678",
        "role": "passenger"
    }
}
```

*POST /api/auth/login*
#### Login user
### Request body:
```json
{
    // pass email or phone or phone_number
    "email": "user@email.com",
    "phone": "0912345678",
    "phone_number": "0912345678",
    "password": "pass1234"
}
```
### Response body:
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "full_name": "John Doe",
        "email": "user@email.com",
        "phone": "0912345678",
        "role": "passenger"
    }
}
```

*POST /api/auth/logout*
#### Logout user

*GET /api/auth/whoami*
#### Return information about the currently authenticated user.
### Response body:
```json
{
    "user": {
        "id": 1,
        "full_name": "John Doe",
        "email": "user@email.com",
        "phone": "0912345678",
        "role": "passenger"
    }
}
```

*POST /api/auth/request/password-reset/*
#### Request a password reset code
### Request body:
```json
{
    "email": "user@email.com"
}
```

*POST /api/auth/reset-password*
#### Reset password using code
### Request body:
```json
{
    "code": "123456",
    "new_password": "newpass123",
    "confirm_new_password": "newpass123"
}
```

## Users

*POST /api/users/create*
#### Create a user (Admin only)
### Request body:
```json
{
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone_number": "0999999999",
    "role": "passenger", // passenger, admin, company_owner, branch_manager, etc.
    "password": "password123",
    "company_id": 1, // optional
    "branch_id": 1 // optional
}
```

*GET /api/users/get/<id>*
#### Get specific user details (Admin only)

*GET /api/users/me*
#### Get current user details (Passenger only)

*GET /api/users/list*
#### List users (Admin only)
### Query Params:
- `role`: Filter by role
- `q`: Search query

*PUT /api/users/update/<id>*
#### Update user info
### Request body:
```json
{
    "name": "New Name",
    "email": "new@email.com",
    "phone_number": "0888888888",
    "password": "newpassword"
}
```

## Companies

*POST /api/companies/register*
#### Register a new bus company (Admin only)
### Request body:
```json
{
    "company": {
        "name": "ABC Bus Company",
        "description": "Premium bus services",
        "email": "contact@abc.com",
        "phone_numbers": ["0999123456"]
    },
    "owner": {
        "full_name": "John Doe",
        "email": "john@abc.com",
        "phone_number": "0991234567",
        "password": "password123"
    },
    "bank_account": {
        "bank_name": "National Bank",
        "account_number": "1234567890",
        "account_name": "ABC Bus Company"
    },
    "create_default_branch": true, // optional
    "default_branch_name": "Main Branch"
}
```

*GET /api/companies/get*
#### Get all registered bus companies

*GET /api/companies/pending*
#### Get pending company registrations (Admin only)

*GET /api/companies/<id>*
#### View a specific bus company

*POST /api/companies/review/<id>/<action>*
#### Approve or reject company registration (Admin only)
- `action`: 'approve' or 'reject'

*PUT /api/companies/update/<id>*
#### Update company info (Owner or Admin)

*POST /api/companies/deactivate/<id>*
#### Deactivate a company (Admin only)

*POST /api/companies/activate/<id>*
#### Activate a company (Admin only)

## Buses

*POST /api/buses/add*
#### Add a bus
### Request body:
```json
{
    "bus_number": "BS 1234",
    "seating_capacity": 60,
    "branch_id": 1
}
```

*GET /api/buses/get-buses*
#### Get all buses from registered companies

*GET /api/buses/company*
#### Get buses for current user's company
### Query Params:
- `company_id`: (Admin only)

*GET /api/buses/<id>*
#### Get a specific bus

*PUT /api/buses/<id>/update*
#### Update bus details

*DELETE /api/buses/<id>/delete*
#### Delete a bus

## Routes

*POST /api/routes/create*
#### Create a route (Admin only)
### Request body:
```json
{
    "origin": "Blantyre",
    "destination": "Lilongwe",
    "distance": 300 // optional
}
```

*GET /api/routes/get*
#### Get all routes

## Schedules

*POST /api/schedules/create*
#### Create a schedule
### Request body:
```json
{
    "bus_id": 1,
    "route_id": 1,
    "departure_time": "2024-03-15T06:00:00Z",
    "arrival_time": "2024-03-15T10:30:00Z",
    "price": 15000,
    "available_seats": 45
}
```

*GET /api/schedules/get*
#### Get all available schedules
### Query Params:
- `from_date`: YYYY-MM-DD
- `to_date`: YYYY-MM-DD
- `route_id`: Filter by route

*GET /api/schedules/<id>*
#### Get a specific schedule

*GET /api/schedules/company/schedules*
#### Get schedules for company buses
### Query Params:
- `from_date`
- `to_date`
- `branch_id`

*PUT /api/schedules/<id>/update*
#### Update an existing schedule

*POST /api/schedules/<id>/cancel*
#### Cancel a schedule

## Bookings

*POST /api/bookings/book*
#### Book a seat
### Request body:
```json
{
    "schedule_id": 1,
    "seat_number": 5
}
```

*POST /api/bookings/cleanup-abandoned*
#### Cleanup abandoned bookings (Admin only)

*POST /api/bookings/cancel/<id>*
#### Cancel a booking

*GET /api/bookings/get*
#### Get all user bookings

*GET /api/bookings/get/<id>*
#### Get a specific booking

*GET /api/bookings/qr-code/<id>*
#### Download QR code image

*GET /api/bookings/qr-code-data/<id>*
#### Get QR code data

*POST /api/bookings/scan-qr*
#### Scan QR code (Conductor)
### Request body:
```json
{
    "qr_data": "QR_CODE_STRING"
}
```

*POST /api/bookings/scan-reference*
#### Verify booking by reference

*GET /api/bookings/qr-status/<id>*
#### Check QR status

## Search

*GET /api/search/schedules*
#### Search for schedules
### Query Params:
- `origin`
- `destination`
- `date`
- `min_price`
- `max_price`
- `company_id`

*GET /api/search/routes*
#### Search for routes

*GET /api/search/companies*
#### Search for companies

## Payments

*POST /api/payments/callback*
#### Handle payment callback

*GET /api/payments/failed*
#### Handle failed payment

*GET /api/payments/verify/<tx_ref>*
#### Verify payment status

*POST /api/payments/webhook*
#### Handle PayChangu webhook

## Payouts

*POST /api/payouts/request*
#### Request payout
### Request body:
```json
{
    "amount": 50000,
    "company_id": 1 // optional for owner
}
```

*GET /api/payouts/list*
#### List payouts

*GET /api/payouts/<id>*
#### Get payout details

*POST /api/payouts/process/<id>*
#### Process payout (Admin only)
### Request body:
```json
{
    "action": "approve", // or "reject"
    "notes": "Approved"
}
```

*POST /api/payouts/cancel/<id>*
#### Cancel payout request

*GET /api/payouts/balance*
#### Get company balance

*POST /api/payouts/webhook*
#### Payout webhook

## Banks

*GET /api/banks/available*
#### Get available banks

*POST /api/banks/account/update*
#### Update bank account details

*GET /api/banks/account*
#### Get bank account details

*DELETE /api/banks/account/delete*
#### Delete bank account details

## Branches

*POST /api/branches/create*
#### Create a branch
### Request body:
```json
{
    "name": "Branch Name",
    "company_id": 1,
    "manager_id": 5 // optional
}
```

*GET /api/branches/list*
#### List branches

*GET /api/branches/<id>*
#### Get branch details

*PUT /api/branches/<id>/update*
#### Update branch info

*DELETE /api/branches/<id>/delete*
#### Delete branch

*GET /api/branches/<id>/employees*
#### Get branch employees

*GET /api/branches/<id>/buses*
#### Get branch buses

*GET /api/branches/<id>/statistics*
#### Get branch statistics

## Dashboard

*GET /api/dashboard/admin*
#### Admin dashboard stats

*GET /api/dashboard/company*
#### Company dashboard stats

*GET /api/dashboard/branch/<id>*
#### Branch dashboard stats

*GET /api/dashboard/conductor/<id>*
#### Conductor dashboard stats

*GET /api/dashboard/passenger*
#### Passenger dashboard stats

## Employees

*POST /api/employees/invite*
#### Invite employee
### Request body:
```json
{
    "email": "emp@example.com",
    "phone_number": "0999999999",
    "full_name": "Employee Name",
    "role": "conductor",
    "branch_id": 1
}
```

*POST /api/employees/accept-invitation*
#### Accept invitation
### Request body:
```json
{
    "invitation_code": "CODE",
    "password": "pass",
    "confirm_password": "pass"
}
```

*GET /api/employees/invitations*
#### List invitations

*DELETE /api/employees/invitations/<id>/cancel*
#### Cancel invitation

*GET /api/employees/list*
#### List employees

*GET /api/employees/<id>*
#### Get employee details

*PUT /api/employees/<id>/update*
#### Update employee info

*DELETE /api/employees/<id>/remove*
#### Remove employee

*POST /api/employees/<id>/assign-bus*
#### Assign bus to conductor

*POST /api/employees/<id>/unassign-bus*
#### Unassign bus from conductor
# Ulendo Tiketi API documentation

## Authorization
*POST /api/auth/register*
#### Register a new user
### Request body:
```
{
    "name": "John Doe",
    "email": "johndoe@example.com", [optional]
    "phone_number": "0912345678,
    "password": "pass1234"
}
```

### Response body:
```
json
"message": "account registered",
"user":{ 
    "id": user.id,
    "full_name": user.name,
    "email": user.email,
    "phone": user.phone_number,
    "role": user.role
}
```

*POST /api/auth/login*
#### Login user
### Request body:
```
{
    <!-- pass email or phone or phone_number -->
    "email": "user@email.com",
    "phone": "0912345678",
    "phone_number": "0912345678",
    "password": "pass1234"
}
```

### Response body:
```
json
{
    "message": "Login successful",
    "user": {
        "id": user.id,
        "full_name": user.name,
        "email": user.email,
        "phone": user.phone_number,
        "role": user.role
    }
}
```

*POST /api/auth/logout*
#### Logout out user
### No request and response bodies

*GET /api/auth/whoami*
#### REturn information about the currently authenticated user.
### Response body:
```
{
    'user': {
        'id': user.id,
        'full_name': user.name,
        'email': user.email,
        'phone': user.phone_number,
        'role': user.role
    }
}
```
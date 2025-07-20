# Credits API Documentation

## Base URL
`https://dbmr3la6d3.execute-api.us-east-1.amazonaws.com`

## Authentication
All endpoints require a JWT Bearer token from Cognito User Pool `us-east-1_q9cVE7WTT`

## User Endpoints

### Get Balance
```
GET /credits/balance
Authorization: Bearer <token>
```

Response:
```json
{
  "userId": "user-id",
  "credits": 100
}
```

### Consume Credits
```
POST /credits/consume
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 1
}
```

Response (200 OK):
```json
{
  "userId": "user-id",
  "deducted": 1,
  "newBalance": 99
}
```

Response (402 Payment Required):
```json
{
  "error": "Insufficient credits"
}
```

## Admin Endpoints (Restricted Access)

### Get User Credits
```
GET /credits/admin?userId=<user-id>
Authorization: Bearer <admin-token>
```

Response:
```json
{
  "userId": "user-id",
  "credits": 100,
  "email": "user@example.com",
  "lastUpdated": "2025-07-20T18:00:00Z"
}
```

### Set User Credits
```
PUT /credits/admin
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "userId": "user-id",
  "credits": 100
}
```

Response:
```json
{
  "userId": "user-id",
  "credits": 100,
  "updatedBy": "admin-user-id",
  "timestamp": "2025-07-20T18:00:00Z"
}
```

## Integration with Video Generation

The frontend automatically:
1. Checks if user has at least 1 credit before allowing video generation
2. Calls `/credits/consume` to deduct 1 credit
3. Only proceeds with video generation if credit deduction succeeds
4. Updates the displayed balance immediately
5. Refreshes balance from server if video generation fails

## Admin Access

Currently restricted to specific user IDs:
- f4c8e4a8-3081-70cd-43f9-ea8a7b407430 (todd.deshane@gmail.com)
- 04d8c4d8-20f1-7000-5cf5-90247ec54b3a (todd@theintersecto.com)

To add more admins, update the `ADMIN_USER_IDS` list in `credits-admin-lambda.py`
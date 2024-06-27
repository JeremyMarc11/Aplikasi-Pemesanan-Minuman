import requests

# Set the endpoint URL
url = "https://payment-service-sbx.pakar-digital.com/api/payment/create-order"

# Set the headers
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YXBpLXNtYXJ0bGluay1zYnhAcGV0cmEuYWMuaWQ6ZEhvRjBTMzJ2MFpCbVd2'
}

# Set the payload data
data = {
    "order_id": "67460824716035",
    "amount": 10000,
    "description": "test create api di sandbox",
    "customer": {
        "name": "John",
        "email": "john.doe@gmail.com",
        "phone": "089798798686"
    },
    "item": [
        {
            "name": "Pulsa 1k",
            "amount": 5000,
            "qty": 1
        },
        {
            "name": "Softcase",
            "amount": 5000,
            "qty": 1
        }
    ],
    "channel": [
        "WALLET_QRIS"
    ],
    "type": "payment-page",
    "payment_mode": "CLOSE",
    "expired_time": "",
    "callback_url": "https://7b84-203-189-122-12.ngrok-free.app/callback",  # Append '/callback' for the callback endpoint
    "success_redirect_url": "-",  # Append '/success' for success redirection
    "failed_redirect_url": "-"  # Append '/failed' for failed redirection
}

# Make the POST request
try:
    response = requests.post(url, headers=headers, json=data)

    # Print the response
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

except requests.exceptions.RequestException as e:
    print("Error making request:", e)

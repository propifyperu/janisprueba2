import requests
r = requests.get('http://127.0.0.1:8000/users/login/', allow_redirects=True)
print('status:', r.status_code)
print('final url:', r.url)
print('len body:', len(r.text))
print(r.text[:800])

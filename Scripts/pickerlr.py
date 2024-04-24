

import pickle

SERVICE_ACCOUNT_FILE = "./flutterchatapp-60a2a-53b5f344f20c.json"

with open(SERVICE_ACCOUNT_FILE, "r") as f:
    google_token = f.read()

file_path = "./Credentials/google-token.pkl"

# Write the variable to the pickle file
with open(file_path, "wb") as f:
    pickle.dump(google_token, f)

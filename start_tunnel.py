from pyngrok import ngrok
import time

# Start a tunnel to the locally running app on port 8000
public_url = ngrok.connect(8000, "http")
print("ngrok public URL:", public_url.public_url)
print("Tunnel details:", public_url)

# Keep the tunnel open
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    ngrok.disconnect(public_url.public_url)
    print("Tunnel closed")

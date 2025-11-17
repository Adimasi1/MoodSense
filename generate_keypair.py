"""Generate X25519 keypair for Cloud Run encryption endpoints."""
from nacl.public import PrivateKey
from base64 import b64encode

# Generate new X25519 keypair
server_private_key = PrivateKey.generate()
server_public_key = server_private_key.public_key

private_key = b64encode(bytes(server_private_key)).decode('ascii')
public_key = b64encode(bytes(server_public_key)).decode('ascii')

print("=" * 70)
print(" MoodSense Encryption Keypair")
print("=" * 70)
print()
print("PRIVATE KEY (keep secret, add to Cloud Run env vars):")
print(f"  {private_key}")
print()
print("PUBLIC KEY (share with clients):")
print(f"  {public_key}")
print()
print("=" * 70)
print("Next steps:")
print("1. Copy the PRIVATE KEY above")
print("2. Go to Cloud Run console → moodsense service")
print("3. Click 'EDIT & DEPLOY NEW REVISION'")
print("4. Container → Variables & Secrets → ADD VARIABLE")
print("5. Name: SERVER_PRIVATE_KEY")
print("6. Value: paste the private key")
print("7. Click DEPLOY")
print("=" * 70)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet
import os

app = FastAPI(title="ZeroVault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Welcome to ZeroVault!"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Generate an encryption key
    key = Fernet.generate_key()
    cipher = Fernet(key)

    # Read the uploaded file
    file_data = await file.read()

    # Encrypt the file
    encrypted_data = cipher.encrypt(file_data)

    # Save the encrypted file
    encrypted_filename = file.filename + ".encrypted"
    file_path = os.path.join(UPLOAD_FOLDER, encrypted_filename)

    with open(file_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)

    return {
        "message": "File encrypted and uploaded successfully!",
        "filename": encrypted_filename,
        "encryption_key": key.decode()
    }

@app.post("/decrypt")
async def decrypt_file(filename: str, encryption_key: str):

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Encrypted file not found"
        )

    try:
        # Read the encrypted file
        with open(file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        # Create the cipher using the key
        cipher = Fernet(encryption_key.encode())

        # Decrypt the file
        decrypted_data = cipher.decrypt(encrypted_data)

        # Remove .encrypted from the filename
        original_filename = filename.replace(".encrypted", "")

        # Send the decrypted file back
        return Response(
            content=decrypted_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{original_filename}"'
            }
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid encryption key or corrupted file"
        )

@app.post("/store-encrypted")
async def store_encrypted_file(file: UploadFile = File(...)):

    try:
        # Keep only the filename, not any folder path
        safe_filename = os.path.basename(file.filename)

        # Read the already-encrypted file
        encrypted_data = await file.read()

        # Save the encrypted file directly
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        with open(file_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

        return {
            "message": "Encrypted file stored successfully!",
            "filename": safe_filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store encrypted file: {str(e)}"
        )

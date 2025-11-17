# Instructions for Running the Backend Locally

Great! The database services (PostgreSQL and ChromaDB) are now running.

Now, let's set up and run the backend locally:

**1. Create a .env file:**
   Create a new file named `.env` in the root directory of your project (the same directory as `docker-compose.yml`).

**2. Populate the .env file:**
   Add the following content to your newly created `.env` file. Make sure to replace `your-secret-key-change-in-production-use-long-random-string` with a strong, random string. You can also add your API keys for LLM providers if you plan to use them.

   ```
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform
   DB_ECHO=False

   # Security
   SECRET_KEY=your-secret-key-change-in-production-use-long-random-string
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7

   # LLM Providers (Configure as needed)
   # OPENAI_API_KEY=sk-...
   # GOOGLE_API_KEY=...
   # ANTHROPIC_API_KEY=...
   # OLLAMA_BASE_URL=http://localhost:11434

   # Vector Store
   CHROMA_PERSIST_DIR=./data/chroma

   # Application Settings
   ENVIRONMENT=development
   LOG_LEVEL=INFO

   # Frontend URL (for CORS)
   FRONTEND_URL=http://localhost:3000

   # File Upload
   MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
   UPLOAD_DIR=./uploads
   ```

**3. Navigate to the backend directory:**
   ```bash
   cd backend
   ```

**4. Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

**5. Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

**6. Run the backend:**
   ```bash
   uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
   ```

Please follow these steps and let me know if you encounter any issues. Once the backend is running, we can then address the frontend.

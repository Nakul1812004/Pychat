## Installation Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Pychat.git
cd Pychat
```

---

### 2. Create Virtual Environment

```bash
python -m venv _venv
```

Activate virtual environment:

#### Windows

```bash
_venv\Scripts\activate
```

#### Linux/Mac

```bash
source _venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Create `.env` File in Main Folder

Create `.env` file and add:

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=chat_app
JWT_SECRET=supersecretkey
GROK_API_KEY=your_grok_api_key
```

---

### 5. Create `.env` File Inside `backend` Folder

Create another `.env` file inside `backend/` and add:

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=chat_app
JWT_SECRET=supersecretkey
GROK_API_KEY=your_grok_api_key
```

---

### 6. Run Backend Server

```bash
uvicorn backend.main:app --reload
```

---

### 7. Run Application

```bash
python app.py
```

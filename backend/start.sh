#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting carduitive3 backend...${NC}"

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python3 init_db.py

# Start the FastAPI server
echo -e "${GREEN}Starting FastAPI server on http://localhost:8000${NC}"
echo -e "${GREEN}API docs available at http://localhost:8000/docs${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

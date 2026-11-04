# Hostel React Project

A full-stack hostel management application with a React frontend and Django REST API backend.

## Overview

This project is organized into two main parts:

- `frontend/` — React + Vite application for the user interface
- `backend/` — Django-based backend with API endpoints and business logic

The application is designed to manage hostel-related workflows such as student records, academic information, complaints, feedback, and administrative tasks.

## Tech Stack

- Frontend: React, Vite, React Router, Axios
- Backend: Python, Django, Django REST Framework
- Styling: CSS / HTML
- Environment configuration: `.env` files

## Project Structure

```text
hostel_react_project/
├── backend/
│   ├── academics/
│   ├── accounts/
│   ├── api/
│   ├── clerks/
│   ├── complaints/
│   ├── core/
│   ├── feedbacks/
│   ├── hostel_management_system/
│   ├── students/
│   ├── manage.py
│   ├── requirements.txt
│   └── README_SETUP_FIRST.md
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── README_SETUP_FIRST.md
├── .gitignore
└── README.md
```

## Features

- Student management
- Hostel complaint handling
- Academic management modules
- Feedback and clerk/admin workflows
- REST API backend for frontend integration
- React-based UI with routing

## Prerequisites

Before running the project, make sure you have:

- Node.js 18+ and npm
- Python 3.10+ (or the version used by the project)
- A virtual environment tool such as `venv`

## Getting Started

### 1. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend expects an API base URL in the `.env` file, for example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

If the backend includes an example environment file, copy it before running the application:

```bash
cp .env.example .env
```

## Running the app

- Start the backend server on port `8000`
- Start the frontend development server with Vite
- Open the frontend URL shown in the terminal (typically `http://localhost:5173`)

## Notes

This repository contains a backend that appears to be in a React-conversion phase, along with the corresponding frontend setup. The backend and frontend are intended to work together through the configured API URL.

## Useful references

- `backend/README_SETUP_FIRST.md`
- `frontend/README_SETUP_FIRST.md`

## License

This project does not currently include a license file in the repository root. If you plan to publish or distribute it, consider adding one.

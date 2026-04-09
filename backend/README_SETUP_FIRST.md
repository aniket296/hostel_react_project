# Beginner setup notes for current backend build

This backend is the current React-conversion backend build.

What it is now:
- Original Django apps preserved
- Added DRF API app
- JWT auth starter added
- Suitable as the backend side for the matching frontend ZIP

What it is not yet:
- Not a guaranteed 100% page-for-page React replacement of every original Django template workflow yet

Run order later:
1. Create virtual environment
2. Install requirements.txt
3. Fill .env from .env.example
4. Run migrations
5. Start Django server on port 8000

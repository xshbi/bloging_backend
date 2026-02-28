# Bloger - Backend API

Welcome to the backend repository of the **Bloger** platform. This project is built using Django and the Django REST Framework (DRF) to serve as the content management backbone for a fullstack blogging application.

## 🏗 System Architecture

This repository contains the backend component of a decoupled Client-Server architecture. It communicates with the frontend via a RESTful API.

- **Framework:** Django 6 & Django REST Framework (DRF)
- **Database:** MySQL
- **Authentication:** JWT (JSON Web Tokens) with seamless OAuth2 integrations

This separation of concerns allows the backend to scale independently and easily support other clients (like mobile apps) in the future.

---

## ⚙️ Basic CRUD App Architecture

The core of the application revolves around the standard Create, Read, Update, and Delete (CRUD) operations for several key entities:

1. **Users:** Custom user model handling extended profiles and avatars.
2. **Posts (Blogs):** The core content type. Users can draft, publish, edit, and delete their articles.
3. **Comments:** Readers can interact with posts by leaving comments.
4. **Reactions/Likes:** A system to track user engagement (e.g., claps/likes) on individual posts.
5. **Notifications:** System for alerting users of interactions on their content.

**How it works structurally:**

- `models.py`: Defines the database schema for the entities above.
- `serializers.py`: DRF's mechanism to convert complex database models into JSON format for the frontend, and strongly validate incoming JSON payloads before saving them.
- `views.py` / `viewsets.py`: Handle the HTTP requests (`GET`, `POST`, `PUT`, `DELETE`). We utilize DRF's `ModelViewSet` to automatically generate standardized CRUD logic.
- `urls.py`: Maps API routes to their corresponding ViewSets using a router.

---

## 🔐 Understanding Authentication & OAuth

Security and user identity are handled using a robust combination of **dj-rest-auth**, **django-allauth**, and **rest_framework_simplejwt**.

### The Flow

1. **Standard Registration & Login:**
   Users can register and log in via standard Email/Password methods. The backend verifies the credentials and returns an **Access Token** (short-lived, 60 minutes) and a **Refresh Token** (long-lived, 7 days).

2. **OAuth (Google & GitHub):**
   - We utilize `django-allauth` to map third-party Social Applications.
   - When a user clicks "Continue with Google" on the frontend, it redirects them to the provider's authorization page.
   - After user consent, the provider redirects back to a backend callback URL with an authorization code.
   - The backend validates this code, creates or retrieves the corresponding user securely in the database, and issues stateless JWT tokens back to the client. *Note: Local development requires updating `YOUR_GOOGLE_CLIENT_ID` in `setup_oauth.py`/`settings.py`.*

3. **API Authorization:**
   For protected CRUD operations (e.g., writing a post or deleting a comment), incoming requests must carry the JWT Access Token in the HTTP header (`Authorization: Bearer <token>`). This ensures strict ownership rules are enforced at the view level.

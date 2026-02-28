# Bloger - Backend API

Welcome to the backend repository of the **Bloger** platform. This project is built using Django and the Django REST Framework (DRF) to serve as the robust, scalable backbone for a fullstack blogging application.

---

## 🏗 System Architecture

This repository operates on a decoupled Client-Server architecture, communicating with the Vue 3 frontend strictly via a RESTful API.

- **Framework:** Django 6 & Django REST Framework (DRF)
- **Database:** MySQL
- **Authentication:** JWT (JSON Web Tokens) with seamless OAuth2 integrations

This clear separation of concerns ensures the backend can scale independently and theoretically support limitless client types (such as future mobile applications).

---

## 🚀 Key Learnings & Takeaways

Building this application from scratch was a deep dive into backend engineering. Here is how building this architecture shaped my understanding of Django and backend development:

### 1. Structuring Apps in Django

Instead of putting all models and views into a single, monolithic file, this project taught me the importance of decomposing a standard Django project into isolated, reusable **Apps**.

- `users/`: Handles custom models, profiles, and authentication logic.
- `blog/`: Manages the core article content and drafting.
- `comments/`: A dedicated app handling threaded user interactions.
- `reactions/`: Tracks user engagement (likes/claps) efficiently.
- `notifications/`: An independent system that alerts users to interactions on their content.

This modular structure keeps the codebase clean, prevents models from becoming convoluted, and ensures that features do not inappropriately overlap.

### 2. Mastering DRF Serializers

Implementing this system solidified my understanding of Django REST Framework (DRF) and the crucial role that **Serializers** play acting as the middleman between the web and the database:

- **Data Conversion:** They take complex database QuerySets and convert them into Python datatypes that can quickly be rendered into JSON.
- **Strict Validation:** They act as gatekeepers, validating incoming POST/PUT payloads against model constraints before ever attempting to write to the database.
- **Customization:** I learned how to utilize `ModelSerializer` for rapid CRUD development, while digging deeper to override methods like `create()`, `update()`, and `to_representation()` for custom data manipulation (like formatting nested JSON).

### 3. Integrating MySQL with Django

Working on this project required moving away from Django's default, file-based SQLite database and hooking up a robust, production-ready relational database: **MySQL**.

- I learned how to connect Django to the local MySQL server by properly configuring the `DATABASES` dictionary in `settings.py` and utilizing `mysqlclient`.
- I gained hands-on experience cleanly managing migrations across half a dozen inter-connected apps without losing data integrity.
- I saw firsthand how Django's ORM abstracts away complex raw SQL queries while allowing relationships (Foreign Keys, Many-to-Many fields) to automatically mirror in MySQL tables.

---

## ⚙️ Basic CRUD App Architecture

The core functionality revolves around Create, Read, Update, and Delete (CRUD) operations for the apps listed above.

**How the data flows structurally:**

1. **`models.py`:** Defines the strict database schema.
2. **`serializers.py`:** Parses, validates, and serializes the data to JSON.
3. **`views.py` / `viewsets.py`:** The brains of the operation routing HTTP requests (`GET`, `POST`, `PUT`, `DELETE`). We utilize DRF's built-in `ModelViewSet` to automatically generate standardized CRUD logic.
4. **`urls.py`:** Utilizes DRF Routers to automatically map clean URL endpoints to the ViewSets.

---

## 🔐 Understanding Authentication & OAuth

Security and user identity are handled using a robust combination of **dj-rest-auth**, **django-allauth**, and **rest_framework_simplejwt**.

### The Flow

1. **Standard Registration & Login:**
   Users can register and log in via standard Email/Password methods. The backend securely verifies the credentials and returns an **Access Token** (short-lived, 60 minutes) and a **Refresh Token** (long-lived, 7 days).

2. **OAuth (Google & GitHub):**
   - We utilize `django-allauth` to map third-party Social Applications to the platform.
   - When a user clicks "Continue with Google" on the frontend, it redirects them to the provider's authorization page.
   - After user consent, the provider redirects back to a backend callback URL with an authorization code.
   - The backend silently validates this code, creates or retrieves the corresponding user securely in the MySQL database, and issues stateless JWT tokens back to the client. *(Note: Local development requires updating `YOUR_GOOGLE_CLIENT_ID` in `setup_oauth.py` or `.env`.)*

3. **API Authorization:**
   For protected actions (e.g., writing a post or deleting a comment), incoming requests must carry the JWT Access Token in the HTTP header (`Authorization: Bearer <token>`). The backend decodes this token instantly to strictly enforce ownership and prevent unauthorized actions.

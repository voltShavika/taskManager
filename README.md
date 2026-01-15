# Task Management System API

A RESTful API for a comprehensive task management system built with FastAPI, PostgreSQL, and JWT authentication.

## 🎯 Project Overview

This system enables teams to collaborate on tasks with hierarchical subtasks, role-based access control, and bulk operations for efficient task management.

## 🏗️ System Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens (2-hour expiry)
- **Caching**: In-memory caching (no Redis)
- **Validation**: Pydantic models
- **Migrations**: Alembic

### Core Features
- ✅ Task CRUD operations with hierarchical subtasks
- ✅ JWT-based authentication with role-based access control
- ✅ Team collaboration with user assignments
- ✅ Bulk task operations for efficiency
- ✅ Performance optimized with indexing and caching
- ✅ Comprehensive API documentation with FastAPI

## 📊 Database Schema

### Core Entities

#### Users
- id (UUID, Primary Key)
- email (Unique)
- username (Unique)
- password_hash
- role (ADMIN, MANAGER, USER, VIEWER)
- created_at, updated_at

#### Teams
- id (UUID, Primary Key)
- name
- description
- created_by (User ID)
- created_at

#### TeamMembers (Junction Table)
- id (UUID, Primary Key)
- team_id (Foreign Key → Teams)
- user_id (Foreign Key → Users)
- role (admin, lead, member, viewer)
- joined_at
- is_active

#### Tasks
- id (UUID, Primary Key)
- title
- description
- status (TODO, IN_PROGRESS, REVIEW, DONE, BLOCKED)
- priority (LOW, MEDIUM, HIGH, CRITICAL)
- due_date
- parent_task_id (Self-referencing for subtasks)
- team_id (Foreign Key → Teams)
- created_by (Foreign Key → Users)
- created_at, updated_at

#### TaskAssignments (Junction Table)
- id (UUID, Primary Key)
- task_id (Foreign Key → Tasks)
- user_id (Foreign Key → Users)
- assigned_at
- role (assignee, reviewer, observer)

## 🔐 Authentication & Authorization

### Global Roles
- **ADMIN**: Full system access, user management
- **MANAGER**: Create teams, manage team members
- **USER**: Standard task operations within teams
- **VIEWER**: Read-only access to assigned tasks

### JWT Configuration
- **Token Type**: JWT access tokens
- **Expiry**: 2 hours
- **Storage**: In-memory token blacklist for logout
- **Security**: bcrypt password hashing

### Access Control Rules
- Users can only access tasks from teams they belong to
- Role-based permissions for CRUD operations
- Task assignments independent of team membership

## 🚀 API Endpoints

### Authentication
```
POST /auth/login          # User login
POST /auth/logout         # User logout (blacklist token)
POST /auth/register       # User registration
GET  /auth/me            # Get current user info
```

### User Management
```
GET    /users            # List users (admin only)
POST   /users            # Create user (admin only)
GET    /users/{id}       # Get user details
PUT    /users/{id}       # Update user (admin/self)
DELETE /users/{id}       # Delete user (admin only)
```

### Team Management
```
GET    /teams            # List user's teams
POST   /teams            # Create team (manager+)
GET    /teams/{id}       # Get team details
PUT    /teams/{id}       # Update team (team admin)
DELETE /teams/{id}       # Delete team (team admin)

GET    /teams/{id}/members     # List team members
POST   /teams/{id}/members     # Add team member
DELETE /teams/{id}/members/{user_id}  # Remove member
```

### Task Management
```
GET    /tasks            # List tasks with filtering
POST   /tasks            # Create task
GET    /tasks/{id}       # Get task details
PUT    /tasks/{id}       # Update task
DELETE /tasks/{id}       # Delete task

GET    /tasks/{id}/subtasks    # List subtasks
POST   /tasks/{id}/subtasks    # Create subtask

POST   /tasks/bulk-update      # Bulk update tasks
POST   /tasks/bulk-assign      # Bulk assign tasks
```

### Task Assignments
```
GET    /tasks/{id}/assignments    # List task assignees
POST   /tasks/{id}/assignments    # Assign user to task
DELETE /tasks/{id}/assignments/{user_id}  # Remove assignment
```

## ⚡ Performance Optimizations

### Database Indexing
- Composite index on (team_id, status, due_date)
- Index on task assignments (user_id, task_id)
- Partial index on active team memberships

### Caching Strategy
- In-memory user session cache
- LRU cache for permission lookups
- Query result caching for team memberships

### Query Optimization
- Eager loading for related entities
- Pagination for list endpoints
- Database connection pooling
- Async operations throughout

## 🔄 Bulk Operations

### Bulk Update Tasks
- Accept array of task updates
- Validate all updates before applying
- Atomic transaction handling
- Return success/failure status per task

### Implementation Features
- Input validation for all updates
- Permission checking per task
- Optimized single query updates
- Detailed error reporting

## 📝 Development Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- pip/poetry for dependency management

### Environment Variables
```
DATABASE_URL=postgresql://user:pass@localhost/taskdb
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=2
```

### Getting Started
```bash
# Clone and setup
git clone <repository>
cd task-management-api

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

## 📚 API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- Database transaction testing
- Authentication flow testing
- Bulk operation testing

---

*This project implements a scalable, secure, and performant task management system with comprehensive team collaboration features.*

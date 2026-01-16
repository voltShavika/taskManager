# Task Mangaer


## API Endpoints

### Authentication
- `POST /auth/register` - Register new user with email and password
- `POST /auth/login` - Login user and get JWT token
- `GET /auth/me` - Get current user information

### Team Management
- `POST /teams/` - Create new team
- `GET /teams/` - List teams user belongs to
- `GET /teams/{id}` - Get team details
- `PUT /teams/{id}` - Update team information
- `DELETE /teams/{id}` - Delete team
- `POST /teams/{id}/members` - Add member to team
- `GET /teams/{id}/members` - List team members
- `DELETE /teams/{id}/members/{user_id}` - Remove team member

### Task Management
- `POST /tasks/` - Create new task with title, description, priority
- `GET /tasks/` - List tasks with pagination and filtering
- `POST /tasks/search` - Advanced search with multiple criteria and AND/OR logic
- `GET /tasks/{id}` - Get task details with assignments and subtasks
- `PUT /tasks/{id}` - Update task status, priority, or other fields
- `DELETE /tasks/{id}` - Delete task (creator only)
- `POST /tasks/{id}/subtasks` - Create subtask under parent task

### Task Assignments
- `POST /tasks/{id}/assignments` - Assign user to task
- `GET /tasks/{id}/assignments` - List task assignments
- `DELETE /tasks/{id}/assignments/{user_id}` - Remove user assignment

### Task Dependencies
- `POST /tasks/{id}/dependencies` - Create dependency between tasks
- `GET /tasks/{id}/dependencies` - List task dependencies
- `GET /tasks/{id}/blocking` - Get tasks blocked by this task
- `GET /tasks/{id}/status` - Check if task is blocked
- `DELETE /tasks/{id}/dependencies/{dependency_id}` - Remove dependency

### Tag Management
- `POST /tags/` - Create tag for team
- `GET /tags/` - List team tags
- `GET /tags/{id}` - Get tag details
- `PUT /tags/{id}` - Update tag
- `DELETE /tags/{id}` - Delete tag

### User Management
- `GET /users/` - List users with pagination
- `GET /users/{id}` - Get user profile
- `PUT /users/{id}` - Update user profile

## Key Features

### Advanced Task Filtering
The filtering system allows users to find tasks quickly using multiple criteria like status, priority, assignees, due dates, and text search. We can combine filters with AND/OR logic for complex queries. This is crucial for large teams managing hundreds of tasks - without proper filtering, users would spend too much time searching for relevant work items. The system supports both simple URL parameters and advanced JSON-based filtering for maximum flexibility.

### Task Dependencies
The dependency system lets us create relationships where one task must be completed before another can start (like "Task 2 is blocked on Task 1"). The system automatically prevents circular dependencies and updates task statuses in real-time. When a dependency is completed, blocked tasks automatically become available to work on. This is essential for project management because it enforces proper workflow sequencing and helps teams understand which tasks are actually ready to be worked on versus which ones are waiting for prerequisites.
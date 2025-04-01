# **📝 Personal Assistant API**  

### **A Smart Task Management API**  

Personal Assistant is a **task management API** built using **Django and REST API framework**. It allows users to **schedule tasks** and receive **email/SMS notifications** before deadlines.  

## **📌 Features**  

✅ **Task Management** – Add, update, delete, and retrieve tasks.  
✅ **Scheduled Notifications** – Get reminders via **email/SMS** before deadlines.  
✅ **Custom Notification Timing** – Set reminders at user-defined times.  
✅ **Automated Notifications** – Powered by **Celery** for background task processing.  
✅ **User Authentication** – Secure login using **JWT tokens** and **OAuth**.  
✅ **Google Calendar Sync** – Add tasks to **Google Calendar**.  
✅ **Task Recommendations** – Get AI-based task recommendations.  
✅ **Payment Integration** – Secure payments for premium features.  
✅ **RESTful API** – Fully functional API for seamless integration.  

## **🔧 Tech Stack**  

- **Backend:** Django, Django REST Framework (DRF)  
- **Database:** MySQL  
- **Messaging Services:** Twilio  
- **Task Queue:** Celery with Redis  
- **Authentication:** JWT Tokens, OAuth  
- **Google Calendar API** – Sync tasks with Google Calendar  

## **🚀 API Endpoints**  

### 🔐 **Authentication & User Management**  
| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| POST   | `/register/`           | Register a new user         |
| POST   | `/login/`              | Login and get JWT token     |
| POST   | `/logout/`             | Logout and revoke token     |
| POST   | `/refresh/`            | Refresh JWT token           |
| PUT    | `/update/<int:pk>/`    | Update user details         |
| DELETE | `/delete/<int:pk>/`    | Delete user account         |
| GET    | `/profile/`            | View or update profile      |

### 📌 **Task Management**  
| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| GET    | `/tasks/`              | Retrieve all tasks          |
| POST   | `/tasks/create/`       | Create a new task           |
| GET    | `/tasks/<int:pk>/`     | Retrieve a specific task    |
| PUT    | `/tasks/<int:pk>/edit/`| Update a task               |
| DELETE | `/tasks/<int:pk>/delete/` | Delete a task         |
| GET    | `/tasks/category/`     | Retrieve tasks by category  |
| GET    | `/tasks/query/`        | Query tasks based on filters |
| GET    | `/tasks/recommendations/` | Get task recommendations |

### 📞 **Notifications & Phone Updates**  
| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| PUT    | `/update-phone/`       | Update user phone number    |

### 🌍 **OAuth & Google Calendar Integration**  
| Method | Endpoint                          | Description                  |
|--------|-----------------------------------|------------------------------|
| GET    | `/oauth2callback/`               | Google OAuth login callback |
| POST   | `/googlecalendar/<int:id>/add/`  | Sync task with Google Calendar |

### 💰 **Payment Integration**  
| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| POST   | `/create-payment/`     | Initiate a payment          |
| GET    | `/payment-success/`    | Handle successful payment   |
| GET    | `/payment-cancel/`     | Handle payment cancellation |

## **🔐 Authentication**  
- **JWT Token Authentication** – Secure login and authentication.  
- **OAuth Authentication** – Google login integration.  

## **⚡ Automated Notifications with Celery**  
- **Celery** is used to handle background task processing.  
- Notifications are **automatically scheduled and sent** without delaying the API response.  
- **Redis** is used as a message broker to manage task execution.  

---

Let me know if you need any changes! 🚀😊

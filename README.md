# 💡 ClearMind AI
### Understand Anything. Know What to Do Next.

ClearMind AI is an AI-powered application designed to simplify complex information and help users understand documents and confusing text through clear, structured, and easy-to-understand explanations.

It combines **Prompt Engineering** and **Retrieval-Augmented Generation (RAG)** with the **Google Gemini API** to provide context-aware responses based on user-provided information.

## ✨ Features

- **User Authentication:** Secure user registration and login.
- **AI Chat Interface:** An interactive chat interface inspired by modern AI assistants.
- **RAG-Based Question Answering:** Retrieve relevant information from uploaded documents to generate context-aware answers.
- **Prompt Engineering:** Uses structured prompts to generate meaningful and easy-to-understand responses.
- **Google Gemini Integration:** Uses Gemini API for AI-powered responses.
- **Chat History:** Access previous conversations.
- **Document Upload:** Upload documents and ask questions about their content.
- **Theme Customization:** Personalize the interface.
- **Logout:** Securely end your session.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web application framework |
| HTML | Frontend structure |
| CSS | Interface styling |
| JavaScript | Frontend interactions |
| Google Gemini API | AI response generation |
| Retrieval-Augmented Generation (RAG) | Context-based information retrieval |
| Git & GitHub | Version control |

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the project directory

```bash
cd ClearMindAI
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the root directory.

Add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace `your_gemini_api_key` with your actual API key.

**Important:** Never upload your `.env` file or API keys to GitHub.

### 7. Run the application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 📂 Project Structure

```text
ClearMindAI/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
│
├── backend/
│   ├── ...
│
├── static/
│   ├── css/
│   ├── js/
│
├── templates/
│   ├── ...
│
├── uploads/
│
└── README.md
```

*Note: The structure above is a general overview. Update it according to your actual project files.*

## 🔄 How It Works

1. The user registers or logs into ClearMind AI.
2. The user uploads a document or enters confusing text.
3. The application processes the provided information.
4. RAG retrieves relevant context when answering document-based questions.
5. Prompt Engineering structures the instructions for the AI.
6. Google Gemini generates a context-aware response.
7. The user receives a simplified explanation through the chat interface.

## 🎯 Project Objective

The main objective of ClearMind AI is to make complex information easier to understand by combining AI-powered explanations, document retrieval and effective prompt engineering in one interactive platform.

## 🚀 Future Enhancements

- Support for more document formats.
- Improved conversational memory.
- Better document retrieval accuracy.
- Multilingual AI responses.
- Enhanced user experience and interface.
- Export conversations and AI-generated explanations.

## 👩‍💻 Author

**Developed as an AI-based academic project.**

---

⭐ If you find this project interesting, consider giving the repository a star!S
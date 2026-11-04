
// =====================================
// CLEARMIND AI - CHAT FUNCTIONALITY
// =====================================

let currentConversationId = null;
let uploadedFiles = [];

// =====================================
// 1. LOAD PAGE
// =====================================

document.addEventListener("DOMContentLoaded", () => {
    loadTheme();
    loadChatHistory();

    const input = document.getElementById("userInput");

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    document.getElementById("pdfInput").addEventListener("change", handlePDFUpload);
});


// =====================================
// 2. THEME SWITCHING
// =====================================

function loadTheme() {
    const savedTheme = localStorage.getItem("clearmind-theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
    }
}

function toggleTheme() {
    document.body.classList.toggle("light-theme");

    const theme = document.body.classList.contains("light-theme")
        ? "light"
        : "dark";

    localStorage.setItem("clearmind-theme", theme);
}


// =====================================
// 3. SIDEBAR
// =====================================

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
}


// =====================================
// 4. DISPLAY MESSAGES
// =====================================

function addMessage(role, content) {
    const messages = document.getElementById("messages");

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    // Display plain text safely.
    bubble.textContent = content;

    row.appendChild(bubble);
    messages.appendChild(row);

    document.getElementById("welcomeScreen").style.display = "none";

    const chatArea = document.getElementById("chatArea");
    chatArea.scrollTop = chatArea.scrollHeight;
}


// =====================================
// 5. NEW CHAT
// =====================================

function createNewChat() {
    currentConversationId = null;

    document.getElementById("messages").innerHTML = "";
    document.getElementById("welcomeScreen").style.display = "block";

    uploadedFiles = [];
    document.getElementById("uploadInfo").textContent = "";
    document.getElementById("pdfInput").value = "";
    document.getElementById("userInput").value = "";

    document.querySelectorAll(".history-item").forEach(item => {
        item.classList.remove("active");
    });
}


// =====================================
// 6. SUGGESTION BUTTONS
// =====================================

function useSuggestion(text) {
    document.getElementById("userInput").value = text;
    sendMessage();
}


// =====================================
// 7. SEND MESSAGE TO GEMINI
// =====================================

async function sendMessage() {
    const input = document.getElementById("userInput");
    const question = input.value.trim();

    if (!question) {
        return;
    }

    input.value = "";

    addMessage("user", question);

    const sendButton = document.getElementById("sendBtn");
    sendButton.disabled = true;
    sendButton.textContent = "...";

    const loadingMessage = document.createElement("div");
    loadingMessage.className = "message-row assistant";
    loadingMessage.innerHTML =
        '<div class="message-bubble">ClearMind is thinking...</div>';

    document.getElementById("messages").appendChild(loadingMessage);

    try {
        const response = await fetch("/api/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                conversation_id: currentConversationId,
                level: document.getElementById("level").value,
                language: document.getElementById("language").value
            })
        });

        const data = await response.json();

        loadingMessage.remove();

        if (!response.ok) {
            throw new Error(data.error || data.message || "Unable to get a response.");
        }

        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
        }

        addMessage("assistant", data.answer || "No answer received.");

        if (data.sources && data.sources.length > 0) {
            addMessage("assistant", "Sources: " + data.sources.join(", "));
        }

        loadChatHistory();

    } catch (error) {
        loadingMessage.remove();
        addMessage("assistant", "Error: " + error.message);
        console.error(error);

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "➤";
    }
}


// =====================================
// 8. UPLOAD PDF FILES
// =====================================

async function handlePDFUpload(event) {
    const files = Array.from(event.target.files);

    if (files.length === 0) {
        return;
    }

    const formData = new FormData();

    files.forEach(file => {
        formData.append("files", file);
    });

    const uploadInfo = document.getElementById("uploadInfo");
    uploadInfo.textContent = "Uploading and processing PDFs...";

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || "PDF upload failed.");
        }

        uploadedFiles = files;

        uploadInfo.textContent =
            "✓ " + files.map(file => file.name).join(", ");

        addMessage(
            "assistant",
            data.message || "Your PDFs have been processed successfully. You can now ask questions about them."
        );

    } catch (error) {
        uploadInfo.textContent = "Upload failed: " + error.message;
        console.error(error);
    }

    event.target.value = "";
}


// =====================================
// 9. LOAD CHAT HISTORY
// =====================================

async function loadChatHistory() {
    const history = document.getElementById("chatHistory");

    try {
        const response = await fetch("/api/conversations");

        if (!response.ok) {
            throw new Error("Could not load chat history.");
        }

        const data = await response.json();

        const conversations = Array.isArray(data)
            ? data
            : (data.conversations || []);

        history.innerHTML = "";

        conversations.forEach(conversation => {
            const item = document.createElement("div");
            item.className = "history-item";

            if (String(conversation.id) === String(currentConversationId)) {
                item.classList.add("active");
            }

            const title = document.createElement("span");
            title.textContent = conversation.title || "New Chat";
            title.onclick = () => openConversation(conversation.id);

            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-chat";
            deleteButton.textContent = "×";
            deleteButton.title = "Delete conversation";
            deleteButton.onclick = (event) => {
                event.stopPropagation();
                deleteConversation(conversation.id);
            };

            item.appendChild(title);
            item.appendChild(deleteButton);
            history.appendChild(item);
        });

    } catch (error) {
        console.error("Chat history error:", error);
    }
}


// =====================================
// 10. OPEN PREVIOUS CONVERSATION
// =====================================

async function openConversation(conversationId) {
    try {
        const response = await fetch(`/api/conversations/${conversationId}`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to open conversation.");
        }

        currentConversationId = conversationId;

        document.getElementById("messages").innerHTML = "";
        document.getElementById("welcomeScreen").style.display = "none";

        const conversation = data.conversation || data;
        const messages = data.messages || conversation.messages || [];

        messages.forEach(message => {
            addMessage(message.role, message.content);
        });

        loadChatHistory();

    } catch (error) {
        alert(error.message);
        console.error(error);
    }
}


// =====================================
// 11. DELETE CONVERSATION
// =====================================

async function deleteConversation(conversationId) {
    if (!confirm("Are you sure you want to delete this conversation?")) {
        return;
    }

    try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to delete conversation.");
        }

        if (String(currentConversationId) === String(conversationId)) {
            createNewChat();
        }

        loadChatHistory();

    } catch (error) {
        alert(error.message);
        console.error(error);
    }
}
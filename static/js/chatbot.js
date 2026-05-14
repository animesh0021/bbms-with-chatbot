// static/js/chatbot.js
// Handles frontend interactions for the AI chatbot widget.

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const toggleBtn = document.getElementById('chatbot-toggle');
    const container = document.getElementById('chatbot-container');
    const messagesDiv = document.getElementById('chatbot-messages');
    const inputField = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send');
    const closeBtn = document.getElementById('chatbot-close'); // optional close button inside widget

    // If essential elements are missing, abort
    if (!toggleBtn || !container || !messagesDiv || !inputField || !sendBtn) {
        console.warn('Chatbot elements not found. Chatbot disabled.');
        return;
    }

    // Create loading spinner element (hidden by default)
    const loadingSpinner = document.createElement('div');
    loadingSpinner.id = 'chatbot-loading';
    loadingSpinner.className = 'chatbot-message bot-message loading';
    loadingSpinner.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Thinking...';
    loadingSpinner.style.display = 'none';

    // Variables
    let isOpen = false;
    let sessionActive = false;

    // ------------------------------------------------------------------
    // Helper: scroll messages to bottom
    // ------------------------------------------------------------------
    function scrollToBottom() {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // ------------------------------------------------------------------
    // Helper: add a message to the chat
    // ------------------------------------------------------------------
    function addMessage(text, sender = 'user') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        scrollToBottom();
    }

    // ------------------------------------------------------------------
    // Show/hide loading indicator
    // ------------------------------------------------------------------
    function showLoading() {
        if (!document.getElementById('chatbot-loading')) {
            messagesDiv.appendChild(loadingSpinner);
        }
        loadingSpinner.style.display = 'block';
        scrollToBottom();
    }

    function hideLoading() {
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    // ------------------------------------------------------------------
    // Send user message to server
    // ------------------------------------------------------------------
    async function sendMessage(message) {
        // Don't send empty messages
        if (!message.trim()) return;

        // Disable input and send button while waiting
        inputField.disabled = true;
        sendBtn.disabled = true;

        // Show user message
        addMessage(message, 'user');

        // Clear input field
        inputField.value = '';

        // Show loading indicator
        showLoading();

        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            hideLoading();

            if (!response.ok) {
                if (response.status === 401) {
                    addMessage('You need to be logged in to use the chatbot. Please log in and try again.', 'bot');
                } else {
                    throw new Error(`Server error: ${response.status}`);
                }
                return;
            }

            const data = await response.json();
            if (data.reply) {
                addMessage(data.reply, 'bot');
            } else {
                addMessage('Sorry, I received an unexpected response.', 'bot');
            }
        } catch (error) {
            hideLoading();
            console.error('Chatbot error:', error);
            addMessage('Sorry, I am having trouble connecting right now. Please try again later.', 'bot');
        } finally {
            // Re-enable input and send button
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    // ------------------------------------------------------------------
    // Toggle chat window
    // ------------------------------------------------------------------
    function toggleChat(open) {
        if (open === undefined) {
            isOpen = !isOpen;
        } else {
            isOpen = open;
        }

        if (isOpen) {
            container.classList.add('open');
            toggleBtn.classList.add('hidden');  // optional: hide toggle button when open
            inputField.focus();

            // Optional: send a welcome message if this is the first open of the session
            if (!sessionActive) {
                sessionActive = true;
                // You could call a welcome endpoint or just add a default message
                addMessage('Hello! I am your Blood Bank assistant. Ask me about donor eligibility, blood compatibility, inventory status, or how to request blood.', 'bot');
            }
        } else {
            container.classList.remove('open');
            toggleBtn.classList.remove('hidden');
        }
    }

    // ------------------------------------------------------------------
    // Event listeners
    // ------------------------------------------------------------------
    toggleBtn.addEventListener('click', () => toggleChat(true));

    if (closeBtn) {
        closeBtn.addEventListener('click', () => toggleChat(false));
    }

    sendBtn.addEventListener('click', () => {
        const message = inputField.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const message = inputField.value.trim();
            if (message) {
                sendMessage(message);
            }
        }
    });

    // Optional: click outside to close? Not recommended for floating widget.
    // But you can add if you want.

    // Initialize: ensure container is hidden, toggle button visible
    toggleChat(false);
});

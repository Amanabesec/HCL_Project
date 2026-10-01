document.addEventListener('DOMContentLoaded', () => {
    const chatBody = document.getElementById('chat-body');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const typingIndicator = document.getElementById('typing-indicator');

    const API_URL = 'http://localhost:5000/api/chat';

    const suggestions = [
        'How to register for courses?',
        'Library hours?',
        'Scholarship info',
        'Reset my password',
        'Career counseling'
    ];

    // Initialize chat
    initChat();

    function initChat() {
        const welcomeMessage = "Hello! I'm UniBot, your AI campus assistant. Ask me anything about courses, schedules, facilities, financial aid, and more! 🎓";
        addBotMessage(welcomeMessage);
        addSuggestions();
    }

    // Format current time
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Add user message to UI
    function addUserMessage(text) {
        const msgHTML = `
            <div class="message-wrapper user">
                <div class="avatar user-avatar"><i class="fas fa-user"></i></div>
                <div class="message-content">
                    <div class="bubble">${escapeHTML(text)}</div>
                    <div class="message-meta">${getCurrentTime()}</div>
                </div>
            </div>
        `;
        chatBody.insertAdjacentHTML('beforeend', msgHTML);
        scrollToBottom();
    }

    // Add bot message to UI
    function addBotMessage(text, intent = null, isError = false) {
        const bubbleClass = isError ? 'bubble error-bubble' : 'bubble';
        
        let metaHTML = `<div class="message-meta">`;
        if (intent) {
            metaHTML += `<span class="intent-badge">${escapeHTML(intent)}</span>`;
        }
        metaHTML += `<span>${getCurrentTime()}</span></div>`;

        const msgHTML = `
            <div class="message-wrapper bot">
                <div class="avatar bot-avatar"><i class="fas fa-robot"></i></div>
                <div class="message-content">
                    <div class="${bubbleClass}">${text}</div>
                    ${metaHTML}
                </div>
            </div>
        `;
        chatBody.insertAdjacentHTML('beforeend', msgHTML);
        scrollToBottom();
    }

    // Add suggestion chips
    function addSuggestions() {
        const container = document.createElement('div');
        container.className = 'suggestions-container';
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.onclick = () => {
                container.remove();
                handleSend(suggestion);
            };
            container.appendChild(chip);
        });

        chatBody.appendChild(container);
        scrollToBottom();
    }

    // Scroll to the latest message
    function scrollToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Escape HTML to prevent XSS
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // Show/hide typing indicator
    function showTypingIndicator() {
        typingIndicator.style.display = 'flex';
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }

    // Handle sending message
    async function handleSend(textOverride = null) {
        const text = textOverride || chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        addUserMessage(text);
        
        // Remove suggestions if they exist
        const suggestionsContainer = document.querySelector('.suggestions-container');
        if (suggestionsContainer) {
            suggestionsContainer.remove();
        }

        showTypingIndicator();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            hideTypingIndicator();
            
            // Format response (convert newlines to <br> for HTML)
            const formattedResponse = escapeHTML(data.response).replace(/\n/g, '<br>');
            
            addBotMessage(formattedResponse, data.intent);
            
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addBotMessage("Sorry, I'm having trouble connecting to the server. Please try again later.", null, true);
        }
    }

    // Event listeners
    sendBtn.addEventListener('click', () => handleSend());
    
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });
});

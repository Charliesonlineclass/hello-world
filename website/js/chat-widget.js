/**
 * SCORPION AI - Chat Widget
 * HERMES AI Assistant for Public Website
 */

class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.messageCount = 0;
        this.sessionId = this.generateSessionId();
        this.conversationHistory = [];
        this.leadCaptured = false;
        this.apiEndpoint = '/api/chat/public';

        this.init();
    }

    generateSessionId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    init() {
        this.chatToggle = document.getElementById('chat-toggle');
        this.chatWindow = document.getElementById('chat-window');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.chatSend = document.getElementById('chat-send');
        this.chatIcon = document.getElementById('chat-icon');
        this.closeIcon = document.getElementById('close-icon');

        if (!this.chatToggle) return;

        this.bindEvents();
        this.loadChatHistory();
    }

    bindEvents() {
        // Toggle chat window
        this.chatToggle.addEventListener('click', () => this.toggle());

        // Send message on button click
        this.chatSend.addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.chatWindow.classList.remove('hidden');
        this.chatIcon.classList.add('hidden');
        this.closeIcon.classList.remove('hidden');
        this.chatInput.focus();

        // Scroll to bottom of messages
        this.scrollToBottom();
    }

    close() {
        this.isOpen = false;
        this.chatWindow.classList.add('hidden');
        this.chatIcon.classList.remove('hidden');
        this.closeIcon.classList.add('hidden');
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        // Clear input
        this.chatInput.value = '';

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageCount++;

        // Show typing indicator
        this.showTyping();

        try {
            // Check if we should capture lead
            if (this.messageCount === 3 && !this.leadCaptured) {
                this.hideTyping();
                this.showLeadCapture();
                return;
            }

            // Send to API
            const response = await this.callAPI(message);
            this.hideTyping();
            this.addMessage(response, 'bot');

        } catch (error) {
            this.hideTyping();
            // Fallback response if API fails
            const fallbackResponse = this.getFallbackResponse(message);
            this.addMessage(fallbackResponse, 'bot');
        }

        this.saveChatHistory();
    }

    async callAPI(message) {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    history: this.conversationHistory.slice(-10)
                })
            });

            if (!response.ok) {
                throw new Error('API error');
            }

            const data = await response.json();
            return data.response;

        } catch (error) {
            console.log('Chat API unavailable, using fallback');
            throw error;
        }
    }

    getFallbackResponse(message) {
        const lowerMessage = message.toLowerCase();

        // FAQ-based responses
        const responses = {
            'pricing': "We offer three tiers: Starter ($100/mo), Pro ($200/mo), and Empire ($500/mo). All plans include our rent-to-own model - after 12 months, you own your AI system! Would you like to learn more about a specific tier?",

            'price': "We offer three tiers: Starter ($100/mo), Pro ($200/mo), and Empire ($500/mo). All plans include our rent-to-own model - after 12 months, you own your AI system! Would you like to learn more about a specific tier?",

            'cost': "We offer three tiers: Starter ($100/mo), Pro ($200/mo), and Empire ($500/mo). All plans include our rent-to-own model - after 12 months, you own your AI system! Would you like to learn more about a specific tier?",

            'service': "We offer AI Virtual Assistants, Website Development, Business Automation, and Training & Consulting. What area interests you most?",

            'hello': "Hello! I'm HERMES, your AI assistant. I can help you learn about our AI automation services, pricing, or answer any questions you have about SCORPION AI. What would you like to know?",

            'hi': "Hi there! I'm HERMES, your AI assistant. I can help you learn about our AI automation services, pricing, or answer any questions. How can I assist you today?",

            'help': "I'm here to help! I can tell you about our services (AI assistants, web development, automation, training), our pricing and rent-to-own model, or connect you with our team. What interests you?",

            'contact': "You can reach us through our contact form at /contact.html, via WhatsApp, or email us at info@ometeolt.com. Would you like me to help you with anything else first?",

            'demo': "Great! I'd love to show you what we can do. Please visit our contact page or share your email, and our team will schedule a personalized demo for you.",

            'own': "With our rent-to-own model, each monthly payment builds equity toward ownership. After 12 months, you fully own your AI system - no more payments ever! Your data and trained model are completely yours.",

            'rent': "With our rent-to-own model, each monthly payment builds equity toward ownership. After 12 months, you fully own your AI system - no more payments ever! Your data and trained model are completely yours.",

            'español': "¡Sí, hablamos español! Puedo ayudarte en español o inglés. ¿En qué te puedo asistir hoy?",

            'spanish': "Yes, I speak Spanish! Sí, hablo español. ¿En qué te puedo ayudar?"
        };

        // Check for keyword matches
        for (const [keyword, response] of Object.entries(responses)) {
            if (lowerMessage.includes(keyword)) {
                return response;
            }
        }

        // Default response
        return "I'd be happy to help you with that! Could you tell me more about what you're looking for? I can assist with information about our AI services, pricing, or help you connect with our team.";
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

        const bubble = document.createElement('div');
        bubble.className = `rounded-2xl px-4 py-2 max-w-[85%] ${
            sender === 'user'
                ? 'bg-gradient-to-r from-yellow-500 to-cyan-500 text-slate-900 rounded-br-none'
                : 'bg-slate-800 rounded-bl-none'
        }`;

        const content = document.createElement('p');
        content.className = 'text-sm';
        content.textContent = text;

        bubble.appendChild(content);
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);

        // Store in history
        this.conversationHistory.push({ role: sender, content: text });

        this.scrollToBottom();
    }

    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex justify-start';
        typingDiv.innerHTML = `
            <div class="bg-slate-800 rounded-2xl rounded-bl-none px-4 py-3">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) {
            typing.remove();
        }
    }

    showLeadCapture() {
        const captureDiv = document.createElement('div');
        captureDiv.id = 'lead-capture';
        captureDiv.className = 'flex justify-start';
        captureDiv.innerHTML = `
            <div class="bg-slate-800 rounded-2xl rounded-bl-none p-4 max-w-[90%]">
                <p class="text-sm mb-3">I'm enjoying our conversation! To provide you with better assistance, could you share your contact info?</p>
                <form id="chat-lead-form" class="space-y-2">
                    <input type="text" name="name" placeholder="Your name" class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500">
                    <input type="email" name="email" placeholder="Your email" class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500">
                    <div class="flex gap-2">
                        <button type="submit" class="flex-1 bg-gradient-to-r from-yellow-500 to-cyan-500 text-slate-900 rounded-lg py-2 text-sm font-semibold hover:opacity-90 transition">Submit</button>
                        <button type="button" id="skip-capture" class="px-4 text-gray-400 text-sm hover:text-white transition">Skip</button>
                    </div>
                </form>
            </div>
        `;
        this.chatMessages.appendChild(captureDiv);
        this.scrollToBottom();

        // Handle form submission
        document.getElementById('chat-lead-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const name = formData.get('name');
            const email = formData.get('email');

            if (name && email) {
                await this.captureLead(name, email);
            }
            this.leadCaptured = true;
            captureDiv.remove();
            this.addMessage("Thanks! We'll be in touch. Now, how else can I help you?", 'bot');
        });

        // Handle skip
        document.getElementById('skip-capture').addEventListener('click', () => {
            this.leadCaptured = true;
            captureDiv.remove();
            this.addMessage("No problem! How can I continue helping you?", 'bot');
        });
    }

    async captureLead(name, email) {
        try {
            await fetch('/api/leads/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    email,
                    source: 'chat_widget',
                    session_id: this.sessionId,
                    conversation: this.conversationHistory
                })
            });
        } catch (error) {
            console.log('Lead capture API unavailable');
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    saveChatHistory() {
        try {
            sessionStorage.setItem('chat_history', JSON.stringify({
                sessionId: this.sessionId,
                messages: this.conversationHistory,
                messageCount: this.messageCount,
                leadCaptured: this.leadCaptured
            }));
        } catch (e) {
            // Storage not available
        }
    }

    loadChatHistory() {
        try {
            const saved = sessionStorage.getItem('chat_history');
            if (saved) {
                const data = JSON.parse(saved);
                this.sessionId = data.sessionId;
                this.messageCount = data.messageCount || 0;
                this.leadCaptured = data.leadCaptured || false;

                // Restore messages
                if (data.messages && data.messages.length > 0) {
                    // Clear default welcome message
                    this.chatMessages.innerHTML = '';

                    data.messages.forEach(msg => {
                        this.addMessage(msg.content, msg.role);
                    });
                    this.conversationHistory = data.messages;
                }
            }
        } catch (e) {
            // Storage not available or corrupted
        }
    }

    clearHistory() {
        sessionStorage.removeItem('chat_history');
        this.conversationHistory = [];
        this.messageCount = 0;
        this.leadCaptured = false;
        this.sessionId = this.generateSessionId();

        // Reset chat to initial state
        this.chatMessages.innerHTML = `
            <div class="flex">
                <div class="bg-slate-800 rounded-2xl rounded-bl-none px-4 py-2 max-w-[85%]">
                    <p class="text-sm">Hello! I'm HERMES, your AI assistant. How can I help you today with AI automation solutions?</p>
                </div>
            </div>
        `;
    }
}

// Initialize chat widget when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatWidget = new ChatWidget();
});

// Export for external use
window.ChatWidget = ChatWidget;

console.log('🦂 SCORPION AI Chat Widget loaded');

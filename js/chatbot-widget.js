/**
 * Evliya AI - Tarihi Yarimada GraphRAG Chatbot Widget
 * Ottoman-themed design for Tarihi Yarimada CBS Platform
 *
 * Kullanim:
 *   <script src="js/chatbot-widget.js"></script>
 *   <script>
 *     TarihiYarimadaChatbot.init({ apiUrl: 'http://localhost:8001' });
 *   </script>
 */

(function() {
    'use strict';

    const DEFAULT_CONFIG = {
        apiUrl: 'http://localhost:8002',
        position: 'bottom-right',
        primaryColor: '#6b1c23',      // Osmanli Bordosu
        accentColor: '#d4a844',       // Altin
        title: 'Evliya AI',
        subtitle: 'Tarihi Yarımada Rehberi',
        placeholder: 'Tarihi Yarımada hakkında sorun...',
        welcomeMessage: 'Hoşgeldiniz! Ben Evliya, İstanbul Tarihi Yarımada rehberiniz. Size camiler, saraylar, surlar ve diğer tarihi yapılar hakkında bilgi verebilirim.\n\nÖrnek: "Ayasofya\'yı kim yaptırdı?"'
    };

    let config = {};
    let isOpen = false;
    let isLoading = false;
    let widgetContainer = null;

    // Ottoman-themed CSS Styles
    const styles = `
        /* Widget Container */
        .tyc-widget-container {
            position: fixed;
            z-index: 9000;
            font-family: 'Raleway', 'Segoe UI', sans-serif;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.4s ease, visibility 0.4s ease, right 0.3s ease;
        }
        .tyc-widget-container.visible {
            opacity: 1;
            visibility: visible;
        }
        .tyc-widget-container.bottom-right {
            bottom: 48px;
            right: 20px;
        }
        .tyc-widget-container.bottom-right.panel-open {
            right: 390px;
        }
        .tyc-widget-container.bottom-left {
            bottom: 48px;
            left: 20px;
        }

        /* Toggle Button - Ottoman Style (matching site buttons) */
        .tyc-toggle-btn {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            border: 1px solid var(--tyc-accent);
            background: var(--tyc-primary);
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        .tyc-toggle-btn:hover {
            transform: translateY(-2px);
            background: var(--tyc-primary-light);
            box-shadow: 0 6px 24px rgba(0,0,0,0.5);
        }
        .tyc-toggle-btn svg {
            width: 26px;
            height: 26px;
            fill: var(--tyc-accent);
        }
        .tyc-toggle-btn:hover svg {
            fill: var(--tyc-accent-light);
        }

        /* Chat Window - Ottoman Palace Style */
        .tyc-chat-window {
            position: absolute;
            bottom: 66px;
            right: 0;
            width: 360px;
            height: 480px;
            background: linear-gradient(180deg, #2a1215 0%, #1a0a0c 100%);
            border-radius: 16px;
            border: 1px solid rgba(212, 168, 68, 0.3);
            box-shadow: 0 12px 40px rgba(0,0,0,0.6), 0 0 30px rgba(212, 168, 68, 0.1);
            display: none;
            flex-direction: column;
            overflow: hidden;
            transform: translateY(10px) scale(0.95);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .tyc-chat-window.open {
            display: flex;
            transform: translateY(0) scale(1);
            opacity: 1;
        }

        /* Header - Saray Basligi */
        .tyc-header {
            padding: 16px 20px;
            background: linear-gradient(135deg, var(--tyc-primary) 0%, var(--tyc-primary-dark) 100%);
            border-bottom: 1px solid rgba(212, 168, 68, 0.3);
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
        }
        .tyc-header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 20px;
            right: 20px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(212, 168, 68, 0.5), transparent);
        }
        .tyc-header-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--tyc-accent) 0%, var(--tyc-accent-dark) 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .tyc-header-icon svg {
            width: 22px;
            height: 22px;
            fill: #1a0a0c;
        }
        .tyc-header-text {
            flex: 1;
        }
        .tyc-header-text h3 {
            margin: 0;
            font-family: 'Cinzel', Georgia, serif;
            font-size: 16px;
            font-weight: 600;
            color: var(--tyc-accent);
            letter-spacing: 0.5px;
        }
        .tyc-header-text span {
            font-size: 11px;
            color: rgba(245, 239, 230, 0.6);
            letter-spacing: 0.3px;
        }
        .tyc-close-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            color: rgba(245, 239, 230, 0.7);
            cursor: pointer;
            padding: 8px;
            border-radius: 8px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .tyc-close-btn:hover {
            background: rgba(255,255,255,0.15);
            color: #f5efe6;
        }

        /* Messages Area */
        .tyc-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: linear-gradient(180deg, rgba(42, 18, 21, 0.5) 0%, transparent 100%);
        }
        .tyc-messages::-webkit-scrollbar {
            width: 6px;
        }
        .tyc-messages::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
            border-radius: 3px;
        }
        .tyc-messages::-webkit-scrollbar-thumb {
            background: rgba(212, 168, 68, 0.3);
            border-radius: 3px;
        }
        .tyc-messages::-webkit-scrollbar-thumb:hover {
            background: rgba(212, 168, 68, 0.5);
        }

        /* Message Bubbles */
        .tyc-message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.6;
            animation: tyc-fadeIn 0.3s ease;
        }
        @keyframes tyc-fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .tyc-message.bot {
            background: rgba(74, 34, 40, 0.8);
            color: #f5efe6;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid rgba(212, 168, 68, 0.15);
        }
        .tyc-message.user {
            background: linear-gradient(135deg, var(--tyc-primary) 0%, var(--tyc-primary-dark) 100%);
            color: #f5efe6;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
            border: 1px solid rgba(212, 168, 68, 0.2);
        }
        .tyc-message.error {
            background: rgba(244, 67, 54, 0.2);
            color: #ff8a80;
            border: 1px solid rgba(244, 67, 54, 0.3);
        }

        /* Typing Indicator */
        .tyc-typing {
            display: flex;
            gap: 5px;
            padding: 14px 18px;
            background: rgba(74, 34, 40, 0.8);
            border-radius: 12px;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid rgba(212, 168, 68, 0.15);
        }
        .tyc-typing span {
            width: 8px;
            height: 8px;
            background: var(--tyc-accent);
            border-radius: 50%;
            animation: tyc-bounce 1.4s infinite ease-in-out;
        }
        .tyc-typing span:nth-child(1) { animation-delay: -0.32s; }
        .tyc-typing span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes tyc-bounce {
            0%, 80%, 100% { transform: scale(0.5); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* Input Area */
        .tyc-input-area {
            padding: 14px 16px;
            background: rgba(26, 10, 12, 0.9);
            border-top: 1px solid rgba(212, 168, 68, 0.2);
            display: flex;
            gap: 10px;
        }
        .tyc-input {
            flex: 1;
            padding: 12px 16px;
            background: rgba(74, 34, 40, 0.6);
            border: 1px solid rgba(212, 168, 68, 0.2);
            border-radius: 12px;
            font-size: 13px;
            font-family: inherit;
            color: #f5efe6;
            outline: none;
            transition: all 0.2s ease;
        }
        .tyc-input::placeholder {
            color: rgba(245, 239, 230, 0.4);
        }
        .tyc-input:focus {
            border-color: rgba(212, 168, 68, 0.5);
            background: rgba(74, 34, 40, 0.8);
        }
        .tyc-send-btn {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            border: 1px solid rgba(212, 168, 68, 0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            background: linear-gradient(135deg, var(--tyc-primary) 0%, var(--tyc-primary-dark) 100%);
        }
        .tyc-send-btn:hover:not(:disabled) {
            background: linear-gradient(135deg, var(--tyc-primary-light) 0%, var(--tyc-primary) 100%);
            border-color: rgba(212, 168, 68, 0.5);
        }
        .tyc-send-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        .tyc-send-btn svg {
            width: 20px;
            height: 20px;
            fill: var(--tyc-accent);
        }

        /* CSS Variables */
        .tyc-widget-container {
            --tyc-primary: #6b1c23;
            --tyc-primary-dark: #3d0f14;
            --tyc-primary-light: #8b2c35;
            --tyc-accent: #d4a844;
            --tyc-accent-light: #e8c96a;
            --tyc-accent-dark: #b8922e;
        }
    `;

    // HTML Template
    function createWidget() {
        const container = document.createElement('div');
        container.className = `tyc-widget-container ${config.position}`;
        container.id = 'evliya-chatbot';

        // Override CSS variables if custom colors provided
        if (config.primaryColor !== DEFAULT_CONFIG.primaryColor) {
            container.style.setProperty('--tyc-primary', config.primaryColor);
        }
        if (config.accentColor !== DEFAULT_CONFIG.accentColor) {
            container.style.setProperty('--tyc-accent', config.accentColor);
        }

        container.innerHTML = `
            <div class="tyc-chat-window">
                <div class="tyc-header">
                    <div class="tyc-header-icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                        </svg>
                    </div>
                    <div class="tyc-header-text">
                        <h3>${config.title}</h3>
                        <span>${config.subtitle}</span>
                    </div>
                    <button class="tyc-close-btn" aria-label="Kapat">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>
                <div class="tyc-messages"></div>
                <div class="tyc-input-area">
                    <input type="text" class="tyc-input" placeholder="${config.placeholder}">
                    <button class="tyc-send-btn" aria-label="Gonder">
                        <svg viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
            <button class="tyc-toggle-btn" aria-label="Evliya AI ile sohbet">
                <svg viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
            </button>
        `;
        return container;
    }

    // Add styles
    function injectStyles() {
        const styleEl = document.createElement('style');
        styleEl.id = 'tyc-styles';
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
    }

    // Check if loading screen is visible
    function isLoadingScreenVisible() {
        const loadingScreen = document.querySelector('.loading-screen');
        if (!loadingScreen) return false;
        const style = window.getComputedStyle(loadingScreen);
        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    }

    // Show widget when loading screen is gone
    function showWidgetWhenReady() {
        if (!widgetContainer) return;

        if (!isLoadingScreenVisible()) {
            widgetContainer.classList.add('visible');
        } else {
            // Check again after a short delay
            setTimeout(showWidgetWhenReady, 200);
        }
    }

    // API call
    async function sendQuery(query) {
        const response = await fetch(`${config.apiUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error('API hatasi');
        }

        return response.json();
    }

    // Add message to chat
    function addMessage(text, type) {
        const messagesEl = document.querySelector('.tyc-messages');
        if (!messagesEl) return;

        const msgEl = document.createElement('div');
        msgEl.className = `tyc-message ${type}`;
        msgEl.textContent = text;
        messagesEl.appendChild(msgEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // Show/hide typing indicator
    function setTyping(show) {
        const messagesEl = document.querySelector('.tyc-messages');
        if (!messagesEl) return;

        const existing = messagesEl.querySelector('.tyc-typing');

        if (show && !existing) {
            const typingEl = document.createElement('div');
            typingEl.className = 'tyc-typing';
            typingEl.innerHTML = '<span></span><span></span><span></span>';
            messagesEl.appendChild(typingEl);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        } else if (!show && existing) {
            existing.remove();
        }
    }

    // Handle send
    async function handleSend() {
        const inputEl = document.querySelector('.tyc-input');
        if (!inputEl) return;

        const query = inputEl.value.trim();

        if (!query || isLoading) return;

        inputEl.value = '';
        addMessage(query, 'user');

        isLoading = true;
        setTyping(true);
        const sendBtn = document.querySelector('.tyc-send-btn');
        if (sendBtn) sendBtn.disabled = true;

        try {
            const result = await sendQuery(query);
            setTyping(false);
            addMessage(result.response, 'bot');
        } catch (error) {
            setTyping(false);
            addMessage('Baglanti kurulamadi. Lutfen API sunucusunun calistigindan emin olun.', 'error');
        } finally {
            isLoading = false;
            if (sendBtn) sendBtn.disabled = false;
        }
    }

    // Toggle chat window
    function toggleChat() {
        isOpen = !isOpen;
        const windowEl = document.querySelector('.tyc-chat-window');
        if (!windowEl) return;

        if (isOpen) {
            windowEl.style.display = 'flex';
            // Trigger reflow for animation
            windowEl.offsetHeight;
            windowEl.classList.add('open');
            const inputEl = document.querySelector('.tyc-input');
            if (inputEl) inputEl.focus();
        } else {
            windowEl.classList.remove('open');
            setTimeout(() => {
                if (!isOpen) windowEl.style.display = 'none';
            }, 300);
        }
    }

    // Initialize
    function init(userConfig = {}) {
        config = { ...DEFAULT_CONFIG, ...userConfig };

        injectStyles();
        widgetContainer = createWidget();
        document.body.appendChild(widgetContainer);

        // Show widget after loading screen disappears
        if (document.readyState === 'complete') {
            showWidgetWhenReady();
        } else {
            window.addEventListener('load', () => {
                setTimeout(showWidgetWhenReady, 500);
            });
        }

        // Add welcome message after widget is visible
        const checkAndAddWelcome = () => {
            if (widgetContainer.classList.contains('visible')) {
                setTimeout(() => {
                    addMessage(config.welcomeMessage, 'bot');
                }, 300);
            } else {
                setTimeout(checkAndAddWelcome, 200);
            }
        };
        checkAndAddWelcome();

        // Event listeners
        document.querySelector('.tyc-toggle-btn').addEventListener('click', toggleChat);
        document.querySelector('.tyc-close-btn').addEventListener('click', toggleChat);
        document.querySelector('.tyc-send-btn').addEventListener('click', handleSend);
        document.querySelector('.tyc-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSend();
        });

        // Watch for asset panel open/close to shift chatbot position
        const assetPanel = document.getElementById('asset-panel');
        if (assetPanel) {
            const panelObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.attributeName === 'class') {
                        const isPanelOpen = assetPanel.classList.contains('open');
                        if (isPanelOpen) {
                            widgetContainer.classList.add('panel-open');
                        } else {
                            widgetContainer.classList.remove('panel-open');
                        }
                    }
                });
            });
            panelObserver.observe(assetPanel, { attributes: true });
        }
    }

    // Expose API
    window.TarihiYarimadaChatbot = {
        init,
        show: () => widgetContainer?.classList.add('visible'),
        hide: () => widgetContainer?.classList.remove('visible'),
        toggle: toggleChat
    };
})();

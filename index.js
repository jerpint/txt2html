// We need to create a new iframe on every update, so that the JS state does not stick around. Example of a problem that would cause: When defining a variable in the top scope with "let", the second update fails.
function update()
{
    if (document.querySelector('#layout').value === 'edit only') return;
    let newIframe = document.createElement('iframe');
    document.body.replaceChild(
        newIframe,
        document.querySelector('#resulframe'),
    );
    newIframe.id='resulframe';
    let outty = newIframe.contentWindow.document;
    outty.open();
    let inny=document.getElementById("data");
    outty.write(inny.value);
    outty.close();
};

function realtime()
{
    if (!document.querySelector("#realtime").checked) return;
    update();
}

function updateLayout() {
    let layout = document.querySelector('#layout').value;
    if (layout === 'horizontal') {
        document.body.classList.add("horizontal");
    } else {
        document.body.classList.remove("horizontal");
    }
}

let dataArea = document.getElementById("data");
dataArea.onkeyup = realtime;

update();

function toggleChat() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.style.display = chatContainer.style.display === 'none' ? 'block' : 'none';
}

// Add conversation history array at the top level
let conversationHistory = [];

function sendMessage() {
    const input = document.getElementById('chat-input');
    const messagesDiv = document.getElementById('chat-messages');
    const message = input.value.trim();
    const currentHtml = document.getElementById('data').value;

    if (!message) return;

    // Add user message to chat UI
    messagesDiv.innerHTML += `<p><strong>You:</strong> ${message}</p>`;

    // Add only user message to history
    conversationHistory.push({
        role: "user",
        content: message
    });

    // Clear the editor content before sending new message
    document.getElementById('data').value = '';
    update();

    // Send message, HTML, and history to server if connection is open
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = JSON.stringify({
            message: message,
            html: currentHtml,
            history: conversationHistory
        });
        ws.send(payload);
    }

    input.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Add event listener for Enter key
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default newline
        sendMessage();
    }
});

// Create WebSocket connection
let ws = null;

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = function() {
        console.log('Connected to server');
    };

    ws.onmessage = function(event) {
        const messagesDiv = document.getElementById('chat-messages');
        document.getElementById('data').value += event.data;
        update();

        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    };

    ws.onclose = function() {
        console.log('Disconnected from server');
        // Reset currentResponse when connection closes
        this.currentResponse = null;
        setTimeout(connectWebSocket, 5000);
    };
}

// Initialize WebSocket connection when page loads
document.addEventListener('DOMContentLoaded', connectWebSocket);

// Add event listener for Enter key
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default newline
        sendMessage();
    }
});
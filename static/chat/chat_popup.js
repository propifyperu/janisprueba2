function initChatPopup(conversationId, windowSelector, formSelector) {
    const win = document.querySelector(windowSelector);
    const form = document.querySelector(formSelector);
    const bodyInput = form.querySelector('input[name="body"]');

    // send message via AJAX
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const fd = new FormData(form);
        fetch('/chat/api/send_message/', {method: 'POST', body: fd, credentials: 'same-origin', headers: {'X-CSRFToken': getCookie('csrftoken')}})
            .then(r => r.json()).then(j => {
                if (j.ok) {
                    appendMessage(win, j.sender_name, bodyInput.value, j.created_at);
                    bodyInput.value = '';
                }
            }).catch(console.error);
    });

    // polling for new messages every 3s
    let last = null;
    setInterval(function () {
        const url = '/chat/api/fetch_messages/?conversation=' + conversationId + (last ? '&since=' + encodeURIComponent(last) : '');
        fetch(url, {credentials: 'same-origin'}).then(r => r.json()).then(j => {
            if (j.messages && j.messages.length) {
                j.messages.forEach(m => appendMessage(win, m.sender_name, m.body, m.created_at));
                last = j.messages[j.messages.length - 1].created_at;
                win.scrollTop = win.scrollHeight;
            }
        }).catch(console.error);
    }, 3000);
}

function appendMessage(win, sender, body, ts) {
    const div = document.createElement('div');
    div.className = 'mb-2';
    div.innerHTML = '<strong>' + escapeHtml(sender) + '</strong> <small class="text-muted">' + ts + '</small><div>' + escapeHtml(body) + '</div>';
    win.appendChild(div);
}

function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/[&<>"']/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c]; });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

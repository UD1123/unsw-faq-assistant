(() => {
  // 创建按钮
  const btn = document.createElement("button");
  btn.id = "openChatBtn";
  btn.innerText = "💬 FAQ Assistant";
  document.body.appendChild(btn);

  // 创建弹窗
  const modal = document.createElement("div");
  modal.id = "chatModal";
  modal.innerHTML = `
    <div class="chat-header" id="chatHeader">
      UNSW Intelligent FAQ Assistant 
      <span id="closeBtn">✖</span>
    </div>
    <div class="chatBox" id="chatBox"></div>
    <div class="suggestions" id="suggestions"></div>
    <div class="input-group">
      <input type="text" id="userInput" placeholder="Type your question..." autocomplete="off" />
      <button onclick="sendMessage()">Send</button>
    </div>
  `;
  document.body.appendChild(modal);

  // 显示弹窗并发送欢迎语（仅第一次点击时触发）
  let greeted = false;
  btn.addEventListener("click", () => {
    modal.style.display = "block";
    if (!greeted) {
      appendMessage("Assistant", "Hi there! 👋 I’m your UNSW Intelligent FAQ Assistant. How can I help you today?😊", "bot");
      greeted = true;
    }
  });

  // 关闭弹窗
  document.querySelector("#closeBtn").addEventListener("click", () => {
    modal.style.display = "none";
  });

  // 拖拽逻辑
  const header = document.getElementById("chatHeader");
  let isDragging = false;
  let offsetX = 0;
  let offsetY = 0;

  header.addEventListener("mousedown", (e) => {
    isDragging = true;
    const rect = modal.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    document.body.style.userSelect = "none";
  });

  document.addEventListener("mousemove", (e) => {
    if (isDragging) {
      modal.style.left = `${e.clientX - offsetX}px`;
      modal.style.top = `${e.clientY - offsetY}px`;
      modal.style.right = "auto";
      modal.style.bottom = "auto";
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.userSelect = "";
  });

  // 发送消息
  async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    appendMessage("You", message, "user");
    showLoader();
    input.value = "";
    clearSuggestions();

    try {
      const response = await fetch("https://unsw-faq-assistant.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      appendMessage("Assistant", parseMarkdown(data.answer), "bot");
    } catch (error) {
      appendMessage("Assistant", "Sorry, something went wrong.", "bot error");
    }

    hideLoader();
  }

  // 渲染 Markdown
  function parseMarkdown(text) {
    return text
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
      .replace(/\n/g, "<br>");
  }

  // 显示消息
  function appendMessage(sender, text, cls) {
    const chatBox = document.getElementById("chatBox");
    const div = document.createElement("div");
    div.className = `message ${cls}`;
    div.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // 显示加载动画
  function showLoader() {
    const chatBox = document.getElementById("chatBox");
    const loader = document.createElement("div");
    loader.id = "loader";
    loader.innerText = "Assistant is typing...";
    loader.className = "loader";
    chatBox.appendChild(loader);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function hideLoader() {
    const loader = document.getElementById("loader");
    if (loader) loader.remove();
  }

  // 联想推荐
  const inputField = document.getElementById("userInput");
  inputField.addEventListener("input", async () => {
    const keyword = inputField.value.trim();
    if (!keyword) {
      clearSuggestions();
      return;
    }

    const response = await fetch("https://unsw-faq-assistant.onrender.com/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prefix: keyword }),
    });
    const data = await response.json();
    renderSuggestions(data.suggestions || []);
  });

  function renderSuggestions(suggestions) {
    const container = document.getElementById("suggestions");
    container.innerHTML = "";
    suggestions.forEach((item) => {
      const div = document.createElement("div");
      div.className = "suggestion-item";
      div.innerText = item;
      div.addEventListener("click", () => {
        document.getElementById("userInput").value = item;
        clearSuggestions();
      });
      container.appendChild(div);
    });
  }

  function clearSuggestions() {
    document.getElementById("suggestions").innerHTML = "";
  }

  // 全局导出
  window.sendMessage = sendMessage;
})();
const chatBox = document.getElementById("chat-box");
const input = document.getElementById("user-input");

async function sendMessage() {
  const userMessage = input.value.trim();
  if (!userMessage) return;

  chatBox.innerHTML += `<p><strong>Tú:</strong> ${userMessage}</p>`;
  input.value = "";

  try {
    const response = await fetch("/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: userMessage }),
    });

    const data = await response.json();

    if (data.reply) {
      chatBox.innerHTML += `<p><strong>IA:</strong> ${data.reply}</p>`;
    } else {
      chatBox.innerHTML += `<p><strong>IA:</strong> Error en la respuesta.</p>`;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (error) {
    chatBox.innerHTML += `<p><strong>IA:</strong> Hubo un error al conectar con el servidor.</p>`;
  }
}

export default {
  // Эта функция срабатывает, когда Telegram пишет боту
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      const update = await request.json();
      await handleUpdate(update, env.BOT_TOKEN);
    }
    return new Response("OK");
  },

  // Эта функция срабатывает по таймеру (каждую минуту)
  async scheduled(event, env, ctx) {
    await checkUpdates(env.BOT_TOKEN);
  }
}

// Функция для получения сообщений (Long Polling)
async function checkUpdates(token) {
  const apiUrl = `https://api.telegram.org/bot${token}`;
  let offset = 0;

  while (true) {
    try {
      const res = await fetch(`${apiUrl}/getUpdates?offset=${offset}&timeout=5`);
      const data = await res.json();

      if (data.ok && data.result.length > 0) {
        for (const update of data.result) {
          offset = update.update_id + 1;
          await handleUpdate(update, token);
        }
      } else {
        break; // Если новых сообщений нет, выходим
      }
    } catch (e) {
      break;
    }
  }
}

async function handleUpdate(update, token) {
  const apiUrl = `https://api.telegram.org/bot${token}`;
  
  if (update.message && update.message.text) {
    const chatId = update.message.chat.id;
    const text = update.message.text;
    const firstName = update.message.from.first_name || "друг";

    if (text === "/start") {
      const welcomeText = `Привет, ${firstName}! 👋\n\nЭто бот студии декора Space Studio.\n\nВыбери действие в меню ниже:`;
      
      const keyboard = {
        inline_keyboard: [
          [{ text: "💬 Чат поддержки", url: "https://t.me/space_technical_support_chat" }],
          [{ text: "📅 Записаться на консультацию", callback_data: "consult" }],
          [{ text: "🛋 Вызвать специалиста (платно)", callback_data: "decor" }]
        ]
      };

      await sendMessage(apiUrl, chatId, welcomeText, keyboard);
    } 
    else if (text === "📅 Записаться на консультацию") {
      await sendMessage(apiUrl, chatId, "📅 Вы записались на консультацию! Напишите нам в чат поддержки для уточнения деталей: https://t.me/space_technical_support_chat");
    }
    else if (text === "🛋 Вызвать специалиста по декору") {
      await sendMessage(apiUrl, chatId, "🛋 Вызов специалиста — платная услуга. Напишите в чат поддержки, и мы обсудим детали и стоимость: https://t.me/space_technical_support_chat");
    }
  }

  if (update.callback_query) {
    const chatId = update.callback_query.message.chat.id;
    const data = update.callback_query.data;
    
    if (data === "consult") {
      await sendMessage(apiUrl, chatId, "Отлично! Напишите в наш чат поддержки, чтобы согласовать время: https://t.me/space_technical_support_chat");
    } else if (data === "decor") {
      await sendMessage(apiUrl, chatId, "Специалист приедет и оценит пространство. Услуга платная. Напишите в поддержку: https://t.me/space_technical_support_chat");
    }
    
    await fetch(`${apiUrl}/answerCallbackQuery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ callback_query_id: update.callback_query.id })
    });
  }
}

async function sendMessage(apiUrl, chatId, text, keyboard = null) {
  const payload = { chat_id: chatId, text: text };
  if (keyboard) payload.reply_markup = keyboard;

  await fetch(`${apiUrl}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
        }

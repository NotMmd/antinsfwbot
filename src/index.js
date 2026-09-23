const DEFAULTS = {
  auto_ban: true,
  delete_message: true,
  target_scope: "both",
  admin_alerts: true,
};

const HEART_PATTERN = /(?:❤️|♥️?|❤︎|🧡|💛|💚|💙|💜|🖤|🤍|🤎|💔|💕|💞|💓|💗|💖|💘|💝|❣️?)/u;
const MODERATION_MINUTES = 60;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== "/" && url.pathname !== "/webhook") {
      return json({ ok: false, error: "not_found" }, 404);
    }
    if (request.method !== "POST") {
      return json({ ok: false, error: "method_not_allowed" }, 405, { allow: "POST" });
    }

    if (env.WEBHOOK_SECRET) {
      const supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (!safeEqual(supplied, env.WEBHOOK_SECRET)) return json({ ok: false, error: "unauthorized" }, 401);
    }
    if (!env.DB) return json({ ok: false, error: "D1 binding DB is missing" }, 503);
    if (!env.BOT_TOKEN) return json({ ok: false, error: "BOT_TOKEN is missing" }, 503);

    let update;
    try {
      update = await request.json();
    } catch {
      return json({ ok: false, error: "invalid_json" }, 400);
    }

    try {
      await handleUpdate(update, env);
      return json({ ok: true });
    } catch (error) {
      console.error("Update handling failed", error);
      return json({ ok: false, error: "update_failed" }, 500);
    }
  },
};

async function handleUpdate(update, env) {
  if (update.callback_query) return handleCallback(update.callback_query, env);
  if (update.channel_post || update.edited_channel_post) {
    const message = update.channel_post || update.edited_channel_post;
    if (message.chat?.id) await recordPost(message, env);
    if (await scopeAllows(env.DB, env, "channel")) await moderate(message, env, "channel");
    return;
  }
  if (update.message || update.edited_message) {
    const message = update.message || update.edited_message;
    if (message.new_chat_members) {
      await recordJoinMessages(message, env);
      return;
    }
    if (message.chat?.type === "private") return handlePrivateMessage(message, env);
    if (message.chat?.type === "group" || message.chat?.type === "supergroup") {
      if (message.message_thread_id) await recordThread(message, env);
      await moderate(message, env, "group");
    }
  }
}

async function recordPost(message, env) {
  const db = env.DB;
  const date = Number(message.date) || Math.floor(Date.now() / 1000);
  await db.prepare(
    `INSERT INTO posts (chat_id, message_id, date, message_thread_id, text, created_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))
     ON CONFLICT(chat_id, message_id) DO UPDATE SET date=excluded.date,
       message_thread_id=excluded.message_thread_id, text=excluded.text`,
  ).bind(String(message.chat.id), message.message_id, date, message.message_thread_id || null,
    message.text || message.caption || "").run();

  if (message.message_thread_id) {
    await db.prepare(
      `INSERT INTO threads (chat_id, message_thread_id, channel_chat_id, channel_post_message_id, updated_at)
       VALUES (?, ?, ?, ?, datetime('now'))
       ON CONFLICT(chat_id, message_thread_id) DO UPDATE SET channel_chat_id=excluded.channel_chat_id,
         channel_post_message_id=excluded.channel_post_message_id, updated_at=datetime('now')`,
    ).bind(String(message.chat.id), message.message_thread_id, String(message.chat.id), message.message_id).run();
  }
}

async function recordThread(message, env) {
  const threadId = message.message_thread_id;
  const origin = getChannelOrigin(message.reply_to_message);
  const found = origin || await env.DB.prepare(
    "SELECT channel_chat_id, channel_post_message_id FROM threads WHERE chat_id=? AND message_thread_id=?",
  ).bind(String(message.chat.id), threadId).first();
  if (!found) return;
  await env.DB.prepare(
    `INSERT INTO threads (chat_id, message_thread_id, channel_chat_id, channel_post_message_id, updated_at)
     VALUES (?, ?, ?, ?, datetime('now'))
     ON CONFLICT(chat_id, message_thread_id) DO UPDATE SET channel_chat_id=excluded.channel_chat_id,
       channel_post_message_id=excluded.channel_post_message_id, updated_at=datetime('now')`,
  ).bind(String(message.chat.id), threadId, String(found.chat_id || found.channel_chat_id),
    found.message_id || found.channel_post_message_id).run();
}

async function recordJoinMessages(message, env) {
  for (const member of message.new_chat_members || []) {
    await env.DB.prepare(
      `INSERT INTO join_messages (chat_id, user_id, message_id, created_at)
       VALUES (?, ?, ?, datetime('now')) ON CONFLICT(chat_id, user_id, message_id) DO NOTHING`,
    ).bind(String(message.chat.id), String(member.id), message.message_id).run();
  }
}

async function moderate(message, env, source) {
  if (!message.chat?.id || !Number.isFinite(Number(message.message_id))) return;
  const body = `${message.text || ""}\n${message.caption || ""}`;
  if (!HEART_PATTERN.test(body)) return;
  const settings = await getSettings(env);
  if (settings.target_scope !== "both" && settings.target_scope !== source) return;

  const post = source === "group" ? await resolveChannelPost(message, env) : await findLatestPost(env)
    .then((row) => row && ({ date: row.date, chatId: row.chat_id, messageId: row.message_id }));
  if (!post) return;
  const minutes = positiveNumber(env.WINDOW_MINUTES, 10);
  const ageSeconds = Number(message.date || Date.now() / 1000) - Number(post.date);
  if (ageSeconds < 0 || ageSeconds > minutes * 60) return;

  const user = message.from;
  if (!user || user.is_bot || user.id == env.ADMIN_USER_ID) return;

  if (source === "group" && settings.auto_ban) {
    const until = Math.floor(Date.now() / 1000) + MODERATION_MINUTES * 60;
    const response = await telegram(env, "restrictChatMember", {
      chat_id: message.chat.id,
      user_id: user.id,
      permissions: {
        can_send_messages: false,
        can_send_audios: false,
        can_send_documents: false,
        can_send_photos: false,
        can_send_videos: false,
        can_send_video_notes: false,
        can_send_voice_notes: false,
        can_send_polls: false,
        can_send_other_messages: false,
        can_add_web_page_previews: false,
      },
      use_independent_chat_permissions: true,
      until_date: until,
    });
    if (!response.ok) console.warn("Unable to restrict member", response.description);
  }

  if (settings.admin_alerts && env.ADMIN_USER_ID) {
    if (source === "group") {
      const forwarded = await telegram(env, "forwardMessage", {
        chat_id: env.ADMIN_USER_ID, from_chat_id: message.chat.id, message_id: message.message_id,
      });
      if (!forwarded.ok) console.warn("Unable to forward moderated message", forwarded.description);
    }
    const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ") || "Unknown user";
    const label = source === "group" ? "group message" : "channel post";
    const alert = await telegram(env, "sendMessage", {
      chat_id: env.ADMIN_USER_ID,
      text: `Heart detected in a ${label} within ${minutes} minutes of channel post ${post.message_id ?? post.messageId}.\nUser: ${displayName} (${user.id})\nChat: ${message.chat.title || message.chat.id}`,
      reply_markup: source === "group" ? { inline_keyboard: [[
        actionButton("Ban permanently", message.chat.id, message.message_id, user.id, "ban"),
        actionButton("Unmute", message.chat.id, message.message_id, user.id, "unmute"),
      ], [
        actionButton("Delete", message.chat.id, message.message_id, user.id, "delete"),
        actionButton("Dismiss", message.chat.id, message.message_id, user.id, "dismiss"),
      ]] } : undefined,
    });
    if (!alert.ok) console.warn("Unable to send admin alert", alert.description);
  }

  if (source === "group" && settings.delete_message) {
    const deleted = await telegram(env, "deleteMessage", { chat_id: message.chat.id, message_id: message.message_id });
    if (!deleted.ok) console.warn("Unable to delete moderated message", deleted.description);
  }
}

async function resolveChannelPost(message, env) {
  const origin = getChannelOrigin(message.reply_to_message);
  if (origin) {
    const row = await env.DB.prepare("SELECT date FROM posts WHERE chat_id=? AND message_id=?")
      .bind(String(origin.chat_id), origin.message_id).first();
    if (row) return { ...origin, date: row.date };
    return { ...origin, date: Number(message.reply_to_message?.date) || 0 };
  }

  if (message.message_thread_id) {
    const thread = await env.DB.prepare(
      `SELECT t.channel_chat_id AS chat_id, t.channel_post_message_id AS message_id, p.date
       FROM threads t LEFT JOIN posts p ON p.chat_id=t.channel_chat_id AND p.message_id=t.channel_post_message_id
       WHERE t.chat_id=? AND t.message_thread_id=?`,
    ).bind(String(message.chat.id), message.message_thread_id).first();
    if (thread) return { chat_id: thread.chat_id, message_id: thread.message_id, date: thread.date || 0 };
  }

  const latest = await findLatestPost(env);
  return latest && { chat_id: latest.chat_id, message_id: latest.message_id, date: latest.date };
}

function getChannelOrigin(reply) {
  if (!reply) return null;
  const origin = reply.forward_origin;
  if (origin?.type === "channel" && origin.chat?.id && origin.message_id) {
    return { chat_id: String(origin.chat.id), message_id: Number(origin.message_id) };
  }
  if (reply.forward_from_chat?.id && reply.forward_from_message_id) {
    return { chat_id: String(reply.forward_from_chat.id), message_id: Number(reply.forward_from_message_id) };
  }
  if (reply.is_automatic_forward && reply.sender_chat?.id && reply.message_id) {
    return { chat_id: String(reply.sender_chat.id), message_id: Number(reply.message_id) };
  }
  return null;
}

async function findLatestPost(env) {
  return env.DB.prepare("SELECT chat_id, message_id, date FROM posts ORDER BY date DESC, message_id DESC LIMIT 1").first();
}

async function handlePrivateMessage(message, env) {
  if (!isAdmin(message.from?.id, env)) return;
  const command = (message.text || "").trim().split(/\s+/, 1)[0].split("@")[0].toLowerCase();
  if (command === "/settings" || command === "/panel") {
    const settings = await getSettings(env);
    await telegram(env, "sendMessage", {
      chat_id: message.chat.id,
      text: "AntiNSFWBot settings — tap an option to change it:",
      reply_markup: panelKeyboard(settings),
    });
  }
}

async function handleCallback(callback, env) {
  const queryId = callback.id;
  const actorId = callback.from?.id;
  const data = callback.data || "";
  if (!isAdmin(actorId, env) || String(callback.message?.chat?.id) !== String(env.ADMIN_USER_ID)) {
    await telegram(env, "answerCallbackQuery", { callback_query_id: queryId, text: "Not authorized", show_alert: true });
    return;
  }

  if (data.startsWith("s:")) {
    const key = data.slice(2);
    if (key === "auto_ban" || key === "delete_message" || key === "admin_alerts") {
      const current = await getSettings(env);
      await setSetting(env.DB, key, current[key] ? "false" : "true");
    } else if (key === "target_scope") {
      const current = await getSettings(env);
      const scopes = ["group", "channel", "both"];
      await setSetting(env.DB, key, scopes[(scopes.indexOf(current.target_scope) + 1) % scopes.length]);
    } else {
      await telegram(env, "answerCallbackQuery", { callback_query_id: queryId, text: "Unknown setting" });
      return;
    }
    const settings = await getSettings(env);
    await telegram(env, "editMessageReplyMarkup", {
      chat_id: callback.message.chat.id,
      message_id: callback.message.message_id,
      reply_markup: panelKeyboard(settings),
    });
    await telegram(env, "answerCallbackQuery", { callback_query_id: queryId, text: "Setting saved" });
    return;
  }

  if (data.startsWith("m:")) {
    const [, chatId, messageId, userId, action] = data.split(":");
    if (!chatId || !messageId || !userId) return;
    const chat = decodeURIComponent(chatId);
    let result = { ok: true };
    if (action === "ban") {
      result = await telegram(env, "banChatMember", { chat_id: chat, user_id: Number(userId) });
    } else if (action === "unmute") {
      result = await telegram(env, "restrictChatMember", {
        chat_id: chat, user_id: Number(userId),
        permissions: { can_send_messages: true, can_send_audios: true, can_send_documents: true,
          can_send_photos: true, can_send_videos: true, can_send_video_notes: true,
          can_send_voice_notes: true, can_send_polls: true, can_send_other_messages: true,
          can_add_web_page_previews: true },
        use_independent_chat_permissions: true,
      });
    } else if (action === "delete") {
      result = await telegram(env, "deleteMessage", { chat_id: chat, message_id: Number(messageId) });
    }
    const text = action === "dismiss" ? "Dismissed" : result.ok ? "Action applied" : "Action failed: " + (result.description || "Telegram API error");
    await telegram(env, "answerCallbackQuery", { callback_query_id: queryId, text, show_alert: !result.ok });
    return;
  }
  await telegram(env, "answerCallbackQuery", { callback_query_id: queryId });
}

function actionButton(label, chatId, messageId, userId, action) {
  return { text: label, callback_data: `m:${encodeURIComponent(String(chatId))}:${messageId}:${userId}:${action}` };
}

function panelKeyboard(settings) {
  const state = (key) => settings[key] ? "ON" : "OFF";
  return { inline_keyboard: [
    [{ text: `Auto-Ban: ${state("auto_ban")}`, callback_data: "s:auto_ban" },
      { text: `Delete Msg: ${state("delete_message")}`, callback_data: "s:delete_message" }],
    [{ text: `Target Scope: ${settings.target_scope.toUpperCase()}`, callback_data: "s:target_scope" },
      { text: `Admin Alerts: ${state("admin_alerts")}`, callback_data: "s:admin_alerts" }],
  ] };
}

async function getSettings(env) {
  const result = { ...DEFAULTS };
  result.auto_ban = envBoolean(env.AUTO_BAN, result.auto_ban);
  result.delete_message = envBoolean(env.DELETE_MESSAGE, result.delete_message);
  result.admin_alerts = envBoolean(env.ADMIN_ALERTS, result.admin_alerts);
  const scope = String(env.TARGET_SCOPE || result.target_scope).toLowerCase();
  result.target_scope = ["group", "channel", "both"].includes(scope) ? scope : "both";

  const rows = await env.DB.prepare("SELECT key, value FROM settings").all();
  for (const row of rows.results || []) {
    if (row.key === "auto_ban" || row.key === "delete_message" || row.key === "admin_alerts") {
      result[row.key] = String(row.value) === "true";
    }
    if (row.key === "target_scope" && ["group", "channel", "both"].includes(row.value)) {
      result.target_scope = row.value;
    }
  }
  return result;
}

async function setSetting(db, key, value) {
  await db.prepare(
    `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
     ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')`,
  ).bind(key, value).run();
}

async function scopeAllows(db, env, source) {
  const settings = await getSettings({ ...env, DB: db });
  return settings.target_scope === "both" || settings.target_scope === source;
}

async function telegram(env, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  try {
    return await response.json();
  } catch {
    return { ok: false, description: `Telegram returned HTTP ${response.status}` };
  }
}

function isAdmin(userId, env) {
  return env.ADMIN_USER_ID !== undefined && env.ADMIN_USER_ID !== "" && String(userId) === String(env.ADMIN_USER_ID);
}

function envBoolean(value, fallback) {
  if (value === undefined || value === "") return fallback;
  return ["true", "1", "yes", "on"].includes(String(value).toLowerCase());
}

function positiveNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function safeEqual(left, right) {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let i = 0; i < left.length; i++) difference |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return difference === 0;
}

function json(value, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extraHeaders },
  });
}

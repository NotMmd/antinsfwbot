import { api, db } from 'sdk';
import { posts, threads, joinMessages } from 'schema';
import { eq, desc } from 'sdk/db';
import { CONFIG, isSingleHeart, escapeHtml } from 'lib/config';
import { getSettings, settingsKeyboard, settingsText } from 'lib/settings';

function getOriginDate(msg) {
  if (msg.sender_chat && msg.sender_chat.id === CONFIG.TARGET_CHANNEL_ID) {
    return msg.date;
  }
  if (msg.forward_origin && msg.forward_origin.chat && msg.forward_origin.chat.id === CONFIG.TARGET_CHANNEL_ID) {
    return msg.forward_origin.date;
  }
  if (msg.is_automatic_forward) {
    return (msg.forward_origin && msg.forward_origin.date) ? msg.forward_origin.date : msg.date;
  }
  return null;
}

async function resolvePostTime(msg) {
  if (msg.reply_to_message) {
    const dt = getOriginDate(msg.reply_to_message);
    if (dt) {
      if (msg.message_thread_id) {
        const dtIso = new Date(dt * 1000).toISOString();
        try {
          await db.insert(threads).values({ threadId: msg.message_thread_id, pubDate: dtIso })
            .onConflictDoUpdate({ target: threads.threadId, set: { pubDate: dtIso } }).run();
        } catch (_) {}
      }
      return dt;
    }
  }

  if (msg.message_thread_id) {
    try {
      const row = await db.select().from(threads).where(eq(threads.threadId, msg.message_thread_id)).get();
      if (row && row.pubDate) {
        return Math.floor(new Date(row.pubDate).getTime() / 1000);
      }
    } catch (_) {}
  }

  try {
    const row = await db.select().from(posts).orderBy(desc(posts.pubDate)).limit(1).get();
    if (row && row.pubDate) {
      return Math.floor(new Date(row.pubDate).getTime() / 1000);
    }
  } catch (_) {}

  return null;
}

export default async function (msg) {
  if (!msg || !msg.chat) return;

  if (msg.chat.type === 'private') {
    if (msg.from && msg.from.id === CONFIG.ADMIN_USER_ID && (msg.text || '').startsWith('/start')) {
      await api.sendMessage({
        chat_id: CONFIG.ADMIN_USER_ID,
        text: '👋 Anti-NSFW Bot is running serverless on Telegram.'
      });
    }
    const command = (msg.text || '').trim().split(/\s+/)[0].split('@')[0];
    if (msg.from && msg.from.id === CONFIG.ADMIN_USER_ID && ['/settings', '/panel'].includes(command)) {
      const current = await getSettings();
      await api.sendMessage({
        chat_id: CONFIG.ADMIN_USER_ID,
        text: settingsText(),
        parse_mode: 'HTML',
        reply_markup: settingsKeyboard(current),
      });
    }
    return;
  }

  if (msg.chat.id !== CONFIG.TARGET_GROUP_ID) return;

  if (msg.new_chat_members && msg.new_chat_members.length > 0) {
    const joinDateIso = new Date(msg.date * 1000).toISOString();
    for (const member of msg.new_chat_members) {
      try {
        await db.insert(joinMessages).values({
          userId: member.id,
          msgId: msg.message_id,
          joinDate: joinDateIso
        }).onConflictDoUpdate({
          target: joinMessages.userId,
          set: { msgId: msg.message_id, joinDate: joinDateIso }
        }).run();
      } catch (_) {}
    }
    return;
  }

  const autoDt = getOriginDate(msg);
  if (autoDt && msg.is_automatic_forward) {
    const dtIso = new Date(autoDt * 1000).toISOString();
    try {
      await db.insert(threads).values({ threadId: msg.message_id, pubDate: dtIso })
        .onConflictDoUpdate({ target: threads.threadId, set: { pubDate: dtIso } }).run();
    } catch (_) {}
  }

  const user = msg.from;
  if (!user) return;

  const text = msg.text || '';
  if (!isSingleHeart(text)) return;

  const postTimeSec = await resolvePostTime(msg);
  if (!postTimeSec) return;

  const diffMins = (msg.date - postTimeSec) / 60.0;
  if (diffMins < 0 || diffMins > CONFIG.WINDOW_MINUTES) return;

  const current = await getSettings();

  const userLink = `tg://user?id=${user.id}`;
  const usernameStr = user.username ? `@${user.username}` : 'No username';
  const infoText =
    `🚨 <b>Heart Emoji Auto-Mute Alert</b>\n\n` +
    `• <b>User:</b> <a href="${userLink}">${escapeHtml(user.first_name || 'user')}</a>\n` +
    `• <b>Username:</b> ${escapeHtml(usernameStr)}\n` +
    `• <b>User ID:</b> <code>${user.id}</code>\n` +
    `• <b>Sent:</b> ${diffMins.toFixed(1)} mins after channel post`;

  const keyboard = {
    inline_keyboard: [
      [
        { text: '🚷 Ban Group', callback_data: `ban_confirm_${user.id}` },
        { text: '🚫 Ban Channel', callback_data: `banchannel_confirm_${user.id}` }
      ],
      [
        { text: '🔨 Ban Both', callback_data: `banboth_confirm_${user.id}` }
      ],
      [
        { text: '🔊 Unmute', callback_data: `unmute_confirm_${user.id}` },
        { text: '❌ Keep Muted', callback_data: `ignore_${user.id}` }
      ],
      [
        { text: '👤 Open Profile', url: userLink }
      ]
    ]
  };

  if (current.adminNotifications) {
    try {
      await api.forwardMessage({
        chat_id: CONFIG.ADMIN_USER_ID,
        from_chat_id: CONFIG.TARGET_GROUP_ID,
        message_id: msg.message_id
      });
    } catch (_) {}

    try {
      await api.sendMessage({
        chat_id: CONFIG.ADMIN_USER_ID,
        text: infoText,
        parse_mode: 'HTML',
        reply_markup: keyboard
      });
    } catch (_) {}
  }

  if (current.autoDelete) {
    try {
      await api.deleteMessage({
        chat_id: CONFIG.TARGET_GROUP_ID,
        message_id: msg.message_id
      });
    } catch (_) {}
  }

  if (current.autoBan) {
    const banTargets = current.banScope === 'both'
      ? [CONFIG.TARGET_GROUP_ID, CONFIG.TARGET_CHANNEL_ID]
      : [current.banScope === 'channel' ? CONFIG.TARGET_CHANNEL_ID : CONFIG.TARGET_GROUP_ID];
    for (const chatId of banTargets) {
      try {
        await api.banChatMember({ chat_id: chatId, user_id: user.id });
        if (chatId === CONFIG.TARGET_GROUP_ID) {
          const joinRow = await db.select().from(joinMessages).where(eq(joinMessages.userId, user.id)).get();
          if (joinRow && joinRow.msgId) {
            try {
              await api.deleteMessage({ chat_id: CONFIG.TARGET_GROUP_ID, message_id: joinRow.msgId });
            } catch (_) {}
            await db.delete(joinMessages).where(eq(joinMessages.userId, user.id)).run();
          }
        }
      } catch (_) {}
    }
  }
}

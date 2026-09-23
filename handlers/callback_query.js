import { api, db } from 'sdk';
import { joinMessages } from 'schema';
import { eq } from 'sdk/db';
import { CONFIG, escapeHtml } from 'lib/config';
import { getSettings, setSetting, settingsKeyboard, settingsText } from 'lib/settings';

export default async function (query) {
  if (!query || !query.from) return;

  if (query.from.id !== CONFIG.ADMIN_USER_ID) {
    try {
      await api.answerCallbackQuery({
        callback_query_id: query.id,
        text: 'Not authorized.',
        show_alert: true
      });
    } catch (_) {}
    return;
  }

  try {
    await api.answerCallbackQuery({ callback_query_id: query.id });
  } catch (_) {}

  const data = query.data || '';
  const msg = query.message;
  if (!msg) return;

  if (data.startsWith('settings:')) {
    const name = data.slice('settings:'.length);
    try {
      const current = await getSettings();
      if (name === 'banScope') {
        const scopes = ['group', 'channel', 'both'];
        const nextScope = scopes[(scopes.indexOf(current.banScope) + 1) % scopes.length];
        await setSetting(name, nextScope);
      } else if (['autoBan', 'autoDelete', 'adminNotifications'].includes(name)) {
        await setSetting(name, !current[name]);
      } else {
        await api.answerCallbackQuery({ callback_query_id: query.id, text: 'Unknown setting.', show_alert: true });
        return;
      }

      const updated = await getSettings();
      try {
        await api.editMessageText({
          chat_id: msg.chat.id,
          message_id: msg.message_id,
          text: settingsText(),
          parse_mode: 'HTML',
          reply_markup: settingsKeyboard(updated),
        });
      } catch (_) {}
      await api.answerCallbackQuery({ callback_query_id: query.id, text: 'Settings updated.' });
    } catch (_) {
      try {
        await api.answerCallbackQuery({ callback_query_id: query.id, text: 'Could not save setting.', show_alert: true });
      } catch (_) {}
    }
    return;
  }

  const base = msg.text || '';

  if (data.startsWith('banboth_confirm_')) {
    const uid = data.split('_')[2];
    const kb = {
      inline_keyboard: [
        [{ text: 'YES, Ban from BOTH', callback_data: `banboth_do_${uid}` }],
        [{ text: 'Cancel', callback_data: `reset_${uid}` }]
      ]
    };
    try {
      await api.editMessageText({
        chat_id: CONFIG.ADMIN_USER_ID,
        message_id: msg.message_id,
        text: `${base}\n\n<b>Are you sure you want to BAN user ${uid} from BOTH channel and group?</b>`,
        parse_mode: 'HTML',
        reply_markup: kb
      });
    } catch (_) {}
    return;
  }

  if (data.startsWith('banchannel_confirm_')) {
    const uid = data.split('_')[2];
    const kb = {
      inline_keyboard: [
        [{ text: 'YES, Ban from Channel', callback_data: `banchannel_do_${uid}` }],
        [{ text: 'Cancel', callback_data: `reset_${uid}` }]
      ]
    };
    try {
      await api.editMessageText({
        chat_id: CONFIG.ADMIN_USER_ID,
        message_id: msg.message_id,
        text: `${base}\n\n<b>Are you sure you want to BAN user ${uid} from Channel?</b>`,
        parse_mode: 'HTML',
        reply_markup: kb
      });
    } catch (_) {}
    return;
  }

  if (data.startsWith('ban_confirm_')) {
    const uid = data.split('_')[2];
    const kb = {
      inline_keyboard: [
        [{ text: 'YES, Ban from Group', callback_data: `ban_do_${uid}` }],
        [{ text: 'Cancel', callback_data: `reset_${uid}` }]
      ]
    };
    try {
      await api.editMessageText({
        chat_id: CONFIG.ADMIN_USER_ID,
        message_id: msg.message_id,
        text: `${base}\n\n<b>Are you sure you want to BAN user ${uid} from Group?</b>`,
        parse_mode: 'HTML',
        reply_markup: kb
      });
    } catch (_) {}
    return;
  }

  if (data.startsWith('unmute_confirm_')) {
    const uid = data.split('_')[2];
    const kb = {
      inline_keyboard: [
        [{ text: 'YES, Unmute User', callback_data: `unmute_do_${uid}` }],
        [{ text: 'Cancel', callback_data: `reset_${uid}` }]
      ]
    };
    try {
      await api.editMessageText({
        chat_id: CONFIG.ADMIN_USER_ID,
        message_id: msg.message_id,
        text: `${base}\n\n<b>Are you sure you want to UNMUTE user ${uid}?</b>`,
        parse_mode: 'HTML',
        reply_markup: kb
      });
    } catch (_) {}
    return;
  }

  if (data.startsWith('reset_')) {
    const uid = data.split('_')[1];
    const userLink = `tg://user?id=${uid}`;
    const kb = {
      inline_keyboard: [
        [
          { text: '🚷 Ban Group', callback_data: `ban_confirm_${uid}` },
          { text: '🚫 Ban Channel', callback_data: `banchannel_confirm_${uid}` }
        ],
        [
          { text: '🔨 Ban Both', callback_data: `banboth_confirm_${uid}` }
        ],
        [
          { text: '🔊 Unmute', callback_data: `unmute_confirm_${uid}` },
          { text: '❌ Keep Muted', callback_data: `ignore_${uid}` }
        ],
        [
          { text: '👤 Open Profile', url: userLink }
        ]
      ]
    };
    const cleanText = base.split('\n\nAre you sure')[0];
    try {
      await api.editMessageText({
        chat_id: CONFIG.ADMIN_USER_ID,
        message_id: msg.message_id,
        text: cleanText,
        parse_mode: 'HTML',
        reply_markup: kb
      });
    } catch (_) {}
    return;
  }

  let status = '';
  if (data.startsWith('banboth_do_')) {
    const userId = parseInt(data.split('_')[2], 10);
    let gRes = 'ok';
    let cRes = 'ok';

    try {
      await api.banChatMember({ chat_id: CONFIG.TARGET_GROUP_ID, user_id: userId });
      const joinRow = await db.select().from(joinMessages).where(eq(joinMessages.userId, userId)).get();
      if (joinRow && joinRow.msgId) {
        try {
          await api.deleteMessage({ chat_id: CONFIG.TARGET_GROUP_ID, message_id: joinRow.msgId });
        } catch (_) {}
        await db.delete(joinMessages).where(eq(joinMessages.userId, userId)).run();
      }
    } catch (e) {
      gRes = e.message || String(e);
    }

    try {
      await api.banChatMember({ chat_id: CONFIG.TARGET_CHANNEL_ID, user_id: userId });
    } catch (e) {
      cRes = e.message || String(e);
    }

    if (gRes === 'ok' && cRes === 'ok') {
      status = `✅ <b>User ${userId} BANNED from BOTH channel & group.</b>`;
    } else {
      status = `⚠️ <b>Ban Both result:</b> Group (${escapeHtml(gRes)}), Channel (${escapeHtml(cRes)})`;
    }
  } else if (data.startsWith('banchannel_do_')) {
    const userId = parseInt(data.split('_')[2], 10);
    try {
      await api.banChatMember({ chat_id: CONFIG.TARGET_CHANNEL_ID, user_id: userId });
      status = `🚫 <b>User ${userId} BANNED from CHANNEL.</b>`;
    } catch (e) {
      status = `❌ <b>Failed channel ban:</b> ${escapeHtml(e.message || String(e))}`;
    }
  } else if (data.startsWith('ban_do_')) {
    const userId = parseInt(data.split('_')[2], 10);
    try {
      await api.banChatMember({ chat_id: CONFIG.TARGET_GROUP_ID, user_id: userId });
      const joinRow = await db.select().from(joinMessages).where(eq(joinMessages.userId, userId)).get();
      if (joinRow && joinRow.msgId) {
        try {
          await api.deleteMessage({ chat_id: CONFIG.TARGET_GROUP_ID, message_id: joinRow.msgId });
        } catch (_) {}
        await db.delete(joinMessages).where(eq(joinMessages.userId, userId)).run();
      }
      status = `🚷 <b>User ${userId} BANNED from GROUP.</b>`;
    } catch (e) {
      status = `❌ <b>Failed group ban:</b> ${escapeHtml(e.message || String(e))}`;
    }
  } else if (data.startsWith('unmute_do_')) {
    const userId = parseInt(data.split('_')[2], 10);
    try {
      await api.restrictChatMember({
        chat_id: CONFIG.TARGET_GROUP_ID,
        user_id: userId,
        permissions: {
          can_send_messages: true,
          can_send_audios: true,
          can_send_documents: true,
          can_send_photos: true,
          can_send_videos: true,
          can_send_video_notes: true,
          can_send_voice_notes: true,
          can_send_polls: true,
          can_send_other_messages: true,
          can_add_web_page_previews: true,
          can_change_info: false,
          can_invite_users: true,
          can_pin_messages: false,
          can_manage_topics: false
        }
      });
      status = `🔊 <b>User ${userId} UNMUTED.</b>`;
    } catch (e) {
      status = `❌ <b>Failed to unmute:</b> ${escapeHtml(e.message || String(e))}`;
    }
  } else if (data.startsWith('ignore_')) {
    status = 'ℹ️ <b>Ignored. User remains muted.</b>';
  } else {
    return;
  }

  const cleanText = base.split('\n\nAre you sure')[0];
  try {
    await api.editMessageText({
      chat_id: CONFIG.ADMIN_USER_ID,
      message_id: msg.message_id,
      text: `${cleanText}\n\n${status}`,
      parse_mode: 'HTML'
    });
  } catch (_) {}
}

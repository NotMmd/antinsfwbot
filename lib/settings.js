import { db } from 'sdk';
import { settings } from 'schema';
import { eq } from 'sdk/db';
import { CONFIG } from 'lib/config';

const SETTING_KEYS = {
  autoBan: 'auto_ban_enabled',
  autoDelete: 'auto_delete_enabled',
  banScope: 'ban_scope',
  adminNotifications: 'admin_notifications_enabled',
};

const DEFAULTS = {
  autoBan: CONFIG.AUTO_BAN_ENABLED,
  autoDelete: CONFIG.AUTO_DELETE_ENABLED,
  banScope: CONFIG.BAN_SCOPE,
  adminNotifications: CONFIG.ADMIN_NOTIFICATIONS_ENABLED,
};

function parseBoolean(value, fallback) {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return fallback;
}

export async function getSettings() {
  const current = { ...DEFAULTS };
  for (const [name, key] of Object.entries(SETTING_KEYS)) {
    try {
      const row = await db.select().from(settings).where(eq(settings.key, key)).get();
      if (!row) continue;
      if (name === 'banScope') {
        if (['group', 'channel', 'both'].includes(row.value)) current[name] = row.value;
      } else {
        current[name] = parseBoolean(row.value, current[name]);
      }
    } catch (_) {}
  }
  return current;
}

export async function setSetting(name, value) {
  const key = SETTING_KEYS[name];
  if (!key) throw new Error(`Unknown setting: ${name}`);
  if (name === 'banScope') {
    if (!['group', 'channel', 'both'].includes(value)) throw new Error('Invalid ban scope');
  } else if (typeof value !== 'boolean') {
    throw new Error(`Setting ${name} must be a boolean`);
  }

  await db.insert(settings).values({ key, value: String(value) })
    .onConflictDoUpdate({ target: settings.key, set: { value: String(value) } }).run();
}

export function settingsKeyboard(current) {
  const state = (value) => value ? 'ON' : 'OFF';
  const icon = (value) => value ? '✅' : '❌';
  const scope = { group: 'Group only', channel: 'Channel only', both: 'Both' }[current.banScope];
  return {
    inline_keyboard: [
      [{ text: `${icon(current.autoBan)} Auto-Ban: ${state(current.autoBan)}`, callback_data: 'settings:autoBan' }],
      [{ text: `${icon(current.autoDelete)} Delete Msg: ${state(current.autoDelete)}`, callback_data: 'settings:autoDelete' }],
      [{ text: `🎯 Target: ${scope}`, callback_data: 'settings:banScope' }],
      [{ text: `${icon(current.adminNotifications)} Admin Alerts: ${state(current.adminNotifications)}`, callback_data: 'settings:adminNotifications' }],
    ],
  };
}

export function settingsText() {
  return '⚙️ <b>Anti-NSFW Bot Settings</b>\nTap an option to change it. Target scope cycles through Group, Channel, and Both.';
}

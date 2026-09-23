export const CONFIG = {
  TARGET_GROUP_ID: 0,
  TARGET_CHANNEL_ID: 0,
  ADMIN_USER_ID: 0,
  WINDOW_MINUTES: 30,
  AUTO_BAN_ENABLED: true,
  AUTO_DELETE_ENABLED: true,
  BAN_SCOPE: 'group',
  ADMIN_NOTIFICATIONS_ENABLED: true,
};

const HEART_EMOJIS_RAW = [
  "🩷", "❤️", "🧡", "💛", "💚", "🩵", "💙", "💜", "🖤", "🩶", "🤍", "🤎",
  "❤️‍🔥", "❤️‍🩹", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "🫦", "👄"
];

const INVISIBLE_REGEX = /[\uFE0E\uFE0F\u200B\u200C\uFEFF\u2060]/g;

export function normalize(str) {
  if (!str) return '';
  return str.trim().replace(INVISIBLE_REGEX, '');
}

const NORMALIZED_HEARTS = new Set(HEART_EMOJIS_RAW.map(e => normalize(e)));

export function isSingleHeart(text) {
  if (!text) return false;
  return NORMALIZED_HEARTS.has(normalize(text));
}

export function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

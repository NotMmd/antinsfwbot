import { db } from 'sdk';
import { posts } from 'schema';
import { CONFIG } from 'lib/config';

export default async function (post) {
  if (!post || !post.chat || post.chat.id !== CONFIG.TARGET_CHANNEL_ID) {
    return;
  }

  const dateIso = new Date(post.date * 1000).toISOString();

  try {
    await db.insert(posts).values({
      msgId: post.message_id,
      pubDate: dateIso,
    }).onConflictDoUpdate({
      target: posts.msgId,
      set: { pubDate: dateIso }
    }).run();
  } catch (err) {
    console.error('Failed to record channel post:', err);
  }
}

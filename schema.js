import { table, integer, text } from 'sdk/db';

export const posts = table('posts', {
  msgId: integer('msg_id').primaryKey(),
  pubDate: text('pub_date').notNull(),
});

export const threads = table('threads', {
  threadId: integer('thread_id').primaryKey(),
  pubDate: text('pub_date').notNull(),
});

export const joinMessages = table('join_messages', {
  userId: integer('user_id').primaryKey(),
  msgId: integer('msg_id').notNull(),
  joinDate: text('join_date').notNull(),
});

export const settings = table('settings', {
  key: text('key').primaryKey(),
  value: text('value').notNull(),
});

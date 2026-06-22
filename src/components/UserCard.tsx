/**
 * UserCard 组件
 * 框架: react
 * 自动生成于 2026-06-20 09:33:53
 */

import React from 'react';
import styles from './UserCard.module.css';

interface UserCardProps {
  name: nameType;,
    email: emailType;
}

export const UserCard: React.FC<UserCardProps> = (name, email) => {
  return (
    <div className={styles.container}>
      {/* TODO: 实现 UserCard 组件内容 */}
      <h2>UserCard</h2>
    </div>
  );
};

export default UserCard;

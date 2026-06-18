/**
 * User 模型
 * 自动生成于 2026-06-19 00:37:25
 */

export interface User {
  email: string;
    age: number;

  id: string;
  createdAt: Date;
  updatedAt: Date;
}

export class UserModel {
  static tableName = "users";

  static async findById(id: string): Promise<User | null> {
    // TODO: 实现数据库查询
    return null;
  }

  static async findAll(): Promise<User[]> {
    // TODO: 实现列表查询
    return [];
  }
}

/**
 * users 相关类型定义
 * 自动生成于 2026-06-20 09:33:53
 */

// 请求参数类型
export interface UsersRequest {
  id?: string;
  // 根据实际需求补充字段
}

// 响应数据类型
export interface UsersData {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// 列表响应
export interface UsersListResponse {
  data: UsersData[];
  total: number;
  page: number;
  pageSize: number;
}

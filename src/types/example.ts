/**
 * example 相关类型定义
 * 自动生成于 2026-06-22 13:20:24
 */

// 请求参数类型
export interface ExampleRequest {
  id?: string;
  // 根据实际需求补充字段
}

// 响应数据类型
export interface ExampleData {
  id: string;
  createdAt: string;
  updatedAt: string;
}

// 列表响应
export interface ExampleListResponse {
  data: ExampleData[];
  total: number;
  page: number;
  pageSize: number;
}

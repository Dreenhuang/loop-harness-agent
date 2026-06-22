/**
 * 用户列表 API
 * Method: GET
 * Endpoint: /api/users
 */
import { request } from '@/utils/http';

export interface UsersParams {
  // TODO: 定义请求参数
  [key: string]: any;
}

export interface UsersResponse {
  // TODO: 定义响应数据结构
  [key: string]: any;
}

export async function users(params?: UsersParams): Promise<UsersResponse> {
  return request<UsersResponse>({
    url: `/api/users`,
    method: 'GET',
    data: params,
  });
}

export default users;

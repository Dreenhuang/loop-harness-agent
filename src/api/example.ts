/**
 * 
 * Method: GET
 * Endpoint: /api/example
 */
import { request } from '@/utils/http';

export interface ExampleParams {
  // TODO: 定义请求参数
  [key: string]: any;
}

export interface ExampleResponse {
  // TODO: 定义响应数据结构
  [key: string]: any;
}

export async function example(params?: ExampleParams): Promise<ExampleResponse> {
  return request<ExampleResponse>({
    url: `/api/example`,
    method: 'GET',
    data: params,
  });
}

export default example;

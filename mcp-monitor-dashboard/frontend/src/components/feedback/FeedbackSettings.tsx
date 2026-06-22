/**
 * FeedbackSettings - 用户提示配置面板
 *
 * 允许用户调整：
 * - 提示显示时长（1s / 3s / 5s / 10s / 永久）
 * - Toast 位置（右上 / 左上 / 右下 / 左下）
 * - 声音开关
 * - 最大同时显示数量
 * - 悬停暂停
 */

import React from 'react';
import { Drawer, Form, Radio, Slider, Switch, Divider, Typography, Space, Button } from 'antd';
import {
  SoundOutlined,
  SoundFilled,
  ClockCircleOutlined,
  PushpinOutlined,
  ColumnHeightOutlined,
} from '@ant-design/icons';
import { useNotificationContext } from './NotificationProvider';

interface FeedbackSettingsProps {
  visible: boolean;
  onClose: () => void;
}

const durationOptions = [
  { label: '1 秒', value: 1000 },
  { label: '3 秒', value: 3000 },
  { label: '5 秒', value: 5000 },
  { label: '10 秒', value: 10000 },
  { label: '永久显示', value: 0 },
];

const positionOptions = [
  { label: '右上', value: 'topRight' },
  { label: '左上', value: 'topLeft' },
  { label: '右下', value: 'bottomRight' },
  { label: '左下', value: 'bottomLeft' },
];

export const FeedbackSettings: React.FC<FeedbackSettingsProps> = ({ visible, onClose }) => {
  const { config, updateConfig, clearAll } = useNotificationContext();

  return (
    <Drawer
      title={
        <Space>
          <PushpinOutlined />
          <span>提示与反馈设置</span>
        </Space>
      }
      placement="right"
      onClose={onClose}
      open={visible}
      width={400}
      footer={
        <Button type="primary" onClick={onClose} block aria-label="保存设置并关闭">
          完成
        </Button>
      }
    >
      <Form layout="vertical">
        {/* 显示时长 */}
        <Form.Item label={<><ClockCircleOutlined /> 提示显示时长</>}>
          <Radio.Group
            optionType="button"
            buttonStyle="solid"
            options={durationOptions}
            value={config.duration}
            onChange={(e) => updateConfig({ duration: e.target.value })}
          />
        </Form.Item>

        <Divider />

        {/* 显示位置 */}
        <Form.Item label={<><PushpinOutlined /> Toast 显示位置</>}>
          <Radio.Group
            optionType="button"
            options={positionOptions}
            value={config.position}
            onChange={(e) => updateConfig({ position: e.target.value })}
          />
        </Form.Item>

        <Divider />

        {/* 声音开关 */}
        <Form.Item label={<>{config.soundEnabled ? <SoundFilled /> : <SoundOutlined />} 提示音</>}>
          <Switch
            checked={config.soundEnabled}
            onChange={(checked) => updateConfig({ soundEnabled: checked })}
            checkedChildren="开启"
            unCheckedChildren="关闭"
          />
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            开启后，每次弹出提示时会播放简短音效（error / warning / success / info 音高不同）。
          </Typography.Text>
        </Form.Item>

        <Divider />

        {/* 最大同时显示数量 */}
        <Form.Item label={<><ColumnHeightOutlined /> 最大同时显示数量</>}>
          <Slider
            min={1}
            max={10}
            value={config.maxToastCount}
            onChange={(value) => updateConfig({ maxToastCount: value })}
            marks={{ 1: '1', 5: '5', 10: '10' }}
          />
        </Form.Item>

        {/* 悬停暂停 */}
        <Form.Item label="悬停暂停自动关闭">
          <Switch
            checked={config.pauseOnHover}
            onChange={(checked) => updateConfig({ pauseOnHover: checked })}
            checkedChildren="开启"
            unCheckedChildren="关闭"
          />
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            开启后，鼠标悬停在提示上时会暂停倒计时，移开后继续。
          </Typography.Text>
        </Form.Item>
      </Form>

      <Divider />

      <Button danger block onClick={clearAll} aria-label="清空当前所有提示">
        清空当前所有提示
      </Button>
    </Drawer>
  );
};

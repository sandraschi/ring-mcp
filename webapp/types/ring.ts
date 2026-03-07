// Ring MCP API Types
export interface RingDevice {
  id: string;
  name: string;
  type: 'doorbell' | 'camera' | 'alarm' | 'sensor';
  model: string;
  firmware?: string;
  battery_life?: number; // 0-100, null for wired devices
  online: boolean;
  address?: string;
  timezone?: string;
  has_subscription: boolean;
  last_update: string;
}

export interface RingEvent {
  id: string;
  created_at: string;
  answered: boolean;
  kind: 'motion' | 'doorbell' | 'alarm';
  recording_status: 'ready' | 'processing' | 'failed';
  deviceType?: string; // Added for enriched events with device information
}

export interface StreamResponse {
  url: string;
}

export interface StatusResponse {
  success: boolean;
  message: string;
  operation?: string;
  timestamp?: string;
  device_id?: string;
}

export interface AuthConfigureResponse {
  success: boolean;
  message: string;
  user?: string;
}

export interface HealthStatus {
  success: boolean;
  message: string;
  health_status?: {
    api_connected: boolean;
    devices_accessible: number;
    authentication_valid: boolean;
    last_check: string;
  };
}

export interface DeviceListResponse {
  devices: RingDevice[];
}

export interface EventListResponse {
  events: RingEvent[];
}

// UI State Types
export interface DeviceStatus {
  device: RingDevice;
  lastSeen: Date;
  batteryStatus: 'good' | 'warning' | 'critical' | 'unknown';
  connectivityStatus: 'online' | 'offline' | 'unknown';
}

export interface SecuritySystem {
  armed: boolean;
  lastArmed?: Date;
  lastDisarmed?: Date;
  devices: RingDevice[];
}

export interface DashboardStats {
  totalDevices: number;
  onlineDevices: number;
  offlineDevices: number;
  batteryWarnings: number;
  recentEvents: number;
  securityStatus: 'armed' | 'disarmed' | 'partial';
}

// API Error Types
export interface ApiError {
  error: boolean;
  message: string;
  code?: string;
  status_code?: number;
}

// WebSocket Event Types
export interface RealtimeEvent {
  type: 'device_status' | 'motion_detected' | 'doorbell_rang' | 'alarm_triggered';
  device_id: string;
  timestamp: string;
  data: any;
}

// Component Props Types
export interface DeviceCardProps {
  device: RingDevice;
  onClick?: (device: RingDevice) => void;
  showControls?: boolean;
}

export interface StreamViewerProps {
  device: RingDevice;
  streamUrl?: string;
  onClose?: () => void;
}

export interface SecurityPanelProps {
  devices: RingDevice[];
  securityStatus: SecuritySystem;
  onArmSystem?: () => void;
  onDisarmSystem?: () => void;
}

// Form Types
export interface LoginFormData {
  username: string;
  password: string;
  rememberMe: boolean;
}

export interface DeviceFilter {
  type?: RingDevice['type'];
  online?: boolean;
  batteryWarning?: boolean;
}

// Notification Types
export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  deviceId?: string;
  dismissible: boolean;
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system';

// Export all types
export type {
  RingDevice as Device,
  RingEvent as Event,
  StreamResponse as Stream,
  StatusResponse as Status,
  HealthStatus as Health,
  DeviceListResponse as DeviceList,
  EventListResponse as EventList,
  DeviceStatus as DeviceState,
  SecuritySystem as Security,
  DashboardStats as Stats,
  ApiError as Error,
  RealtimeEvent as WSMessage,
  DeviceCardProps as CardProps,
  StreamViewerProps as ViewerProps,
  SecurityPanelProps as PanelProps,
  LoginFormData as LoginData,
  DeviceFilter as Filter,
  NotificationItem as Notification
};
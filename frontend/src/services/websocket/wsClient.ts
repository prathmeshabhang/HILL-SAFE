import { useHazardStore } from '../../store/useHazardStore';
import { useEmergencyStore } from '../../store/useEmergencyStore';
import { AlertItem, StationTelemetry } from '../../types';

class WebSocketManager {
  private socket: WebSocket | null = null;
  private reconnectTimeout: number | null = null;
  private heartbeatInterval: number | null = null;
  private isIntentionalClose = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  public connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isIntentionalClose = false;

    let wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      const apiBase = import.meta.env.VITE_API_BASE_URL;
      if (apiBase) {
        const cleanBase = apiBase.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://');
        wsUrl = `${cleanBase.replace(/\/+$/, '')}/ws/v1/events`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/ws/v1/events`;
      }
    }

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('[WebSocket] Connected to FLOODY SHIELD events gateway:', wsUrl);
        useHazardStore.getState().setBackendOnline(true);
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.handleIncomingEvent(payload);
        } catch (err) {
          console.warn('[WebSocket] Received non-JSON message:', event.data);
        }
      };

      this.socket.onclose = () => {
        console.log('[WebSocket] Connection closed.');
        this.cleanup();
        if (!this.isIntentionalClose) {
          this.scheduleReconnect();
        }
      };

      this.socket.onerror = (err) => {
        console.warn('[WebSocket] Gateway error, falling back to polling.', err);
        this.socket?.close();
      };
    } catch (e) {
      console.warn('[WebSocket] Init error:', e);
      this.scheduleReconnect();
    }
  }

  private handleIncomingEvent(data: any) {
    const eventType = data.type || data.event;

    switch (eventType) {
      case 'ping':
      case 'pong':
        break;

      case 'alert_issued':
      case 'emergency_broadcast': {
        const alert: AlertItem = data.alert || data.payload;
        if (alert) {
          const currentAlerts = useHazardStore.getState().activeAlerts;
          useHazardStore.getState().setActiveAlerts([alert, ...currentAlerts.filter(a => a.id !== alert.id)]);
          
          // Trigger full screen emergency overlay if severe
          if (alert.severity === 'CRITICAL' || alert.severity === 'WARNING') {
            useEmergencyStore.getState().triggerEmergency(alert);
          }
        }
        break;
      }

      case 'telemetry_packet':
      case 'telemetry_update': {
        const telemetry: StationTelemetry = data.telemetry || data.payload;
        if (telemetry && useHazardStore.getState().selectedStation?.station_id === telemetry.station_id) {
          useHazardStore.getState().setSelectedStation(telemetry);
        }
        break;
      }

      case 'risk_update': {
        if (data.summary) {
          useHazardStore.getState().setRiskSummary(data.summary);
        }
        break;
      }

      default:
        // Generic event logged
        console.log('[WebSocket] Event received:', eventType, data);
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      }
    }, 25000);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WebSocket] Max reconnect attempts reached. Remaining in polling mode.');
      return;
    }

    const backoff = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 20000);
    this.reconnectAttempts++;

    this.reconnectTimeout = window.setTimeout(() => {
      console.log(`[WebSocket] Reconnecting (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, backoff);
  }

  private cleanup() {
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.socket = null;
  }

  public disconnect() {
    this.isIntentionalClose = true;
    this.cleanup();
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const wsClient = new WebSocketManager();

# Ring MCP Monitoring Stack

Complete observability setup for Ring Security MCP Server with Grafana, Prometheus, Loki, and Promtail.

## Overview

This monitoring stack provides comprehensive visibility into your Ring security system:

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation and querying
- **Promtail**: Log shipping from Ring MCP server
- **Node Exporter**: System metrics (CPU, memory, disk)

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Start the monitoring stack**:
   ```bash
   docker-compose up -d
   ```

3. **Access the services**:
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Prometheus**: http://localhost:9090
   - **Loki**: http://localhost:3100

4. **Start Ring MCP with metrics**:
   ```bash
   python -m ring_mcp
   ```

## Metrics Collected

### Ring Security Metrics
- `ring_api_calls_total`: Total API calls to Ring services
- `ring_api_duration_seconds`: API call response times
- `ring_device_battery_percent`: Device battery levels
- `ring_device_online`: Device online/offline status
- `ring_security_armed`: Security system armed status
- `ring_tool_calls_total`: MCP tool usage statistics

### System Metrics
- CPU usage, memory usage, disk I/O
- Container performance
- Network connectivity

## Dashboards

### Ring Security Overview
Pre-built dashboard showing:
- Security system status (armed/disarmed)
- Device battery levels and connectivity
- API performance and error rates
- Real-time device status monitoring

### Creating Custom Dashboards

1. Go to Grafana (http://localhost:3000)
2. Click "Create" → "Dashboard"
3. Add panels with Prometheus queries like:
   - `ring_device_battery_percent` - Device battery levels
   - `ring_security_armed` - Security system status
   - `rate(ring_api_calls_total[5m])` - API call rates

## Alerts

Pre-configured alerts for:
- **Security**: System disarmed unexpectedly
- **Maintenance**: Low battery warnings
- **Connectivity**: Device offline alerts
- **Performance**: High API error rates, slow responses

### Managing Alerts

1. Go to Prometheus: http://localhost:9090/alerts
2. Or view in Grafana: http://localhost:3000/alerting

## Logs

### Viewing Logs
- **Grafana Explore**: http://localhost:3000/explore
- **Direct Loki**: http://localhost:3100

### Log Labels
- `job`: ring-mcp (application logs)
- `level`: info, warning, error, debug
- `device_id`: Specific device identifiers
- `error_code`: Error classification

### Example Log Queries
```
{job="ring-mcp"} |= "device"
{job="ring-mcp"} | level="error"
{job="ring-mcp"} | device_id="front_door_sensor"
```

## Troubleshooting

### No Metrics in Prometheus
1. Check if Ring MCP server is running with metrics enabled
2. Verify Prometheus can reach `ring-mcp:8001/metrics`
3. Check Prometheus logs: `docker-compose logs prometheus`

### Missing Logs in Loki
1. Ensure logs directory exists: `./logs/`
2. Check Promtail configuration and logs
3. Verify Loki is running: `docker-compose logs loki`

### Dashboard Not Loading
1. Check data source configuration in Grafana
2. Verify Prometheus is responding
3. Import dashboard JSON if needed

## Configuration Files

- `prometheus/prometheus.yml` - Metrics collection
- `prometheus/alert_rules.yml` - Alerting rules
- `loki/loki-config.yml` - Log storage
- `promtail/promtail-config.yml` - Log shipping
- `grafana/provisioning/dashboards/` - Dashboard definitions

## Security Notes

- Change default Grafana password: Set `GRAFANA_ADMIN_PASSWORD` environment variable
- Consider enabling SSL/TLS for production use
- Monitor resource usage of monitoring stack
- Regular backup of Grafana dashboards and configurations

## Performance Tuning

- Adjust scrape intervals in `prometheus.yml`
- Configure log retention in Loki
- Set up data retention policies
- Monitor monitoring stack resource usage

## Integration with Other Systems

The metrics can be integrated with:
- Slack/Discord notifications
- Email alerts
- External monitoring systems
- SIEM platforms

## Development

To add new metrics:
1. Add Prometheus metric definitions to `server.py`
2. Update the metrics collection in tool functions
3. Create Grafana dashboard panels
4. Add alerting rules if needed

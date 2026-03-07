# Ring MCP React Webapp

A beautiful, modern React web application for testing and demonstrating Ring MCP functionality.

## ✨ Features

- **Beautiful Dashboard**: Modern UI with real-time device monitoring
- **Interactive Device Cards**: Live status updates and device controls
- **Security Panel**: Arm/disarm security systems with visual feedback
- **Activity Feed**: Real-time event monitoring and history
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **TypeScript**: Full type safety and excellent developer experience
- **Tailwind CSS**: Beautiful, consistent styling with dark mode support

## 🚀 Quick Start

### Prerequisites

1. **Ring MCP Server**: Ensure the Ring MCP server is running on `http://localhost:8123`
2. **Node.js 18+**: Required for Next.js
3. **Ring Credentials**: Configure your Ring account credentials

### Installation

```bash
# Navigate to the webapp directory
cd webapp

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Access the Dashboard

Open [http://localhost:11110](http://localhost:11110) in your browser.

## 🏗️ Architecture

### Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast

### Project Structure

```
webapp/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Dashboard page
├── components/            # React components
│   ├── DeviceCard.tsx     # Device display card
│   ├── SecurityPanel.tsx  # Security controls
│   ├── ActivityFeed.tsx   # Event monitoring
│   ├── Navigation.tsx     # Sidebar navigation
│   └── StatsCard.tsx      # Statistics display
├── lib/                   # Utilities and API client
│   ├── api.ts            # Ring MCP API client
│   └── utils.ts          # Utility functions
├── types/                 # TypeScript type definitions
│   └── ring.ts           # Ring device and API types
├── hooks/                 # Custom React hooks (future)
├── utils/                 # Additional utilities (future)
└── public/               # Static assets (future)
```

## 🎨 Components

### Dashboard (`app/page.tsx`)
- **System Overview**: Real-time stats and connectivity status
- **Device Grid**: Interactive cards for all Ring devices
- **Security Panel**: Arm/disarm controls with status indicators
- **Activity Feed**: Recent events and motion detection

### Device Card (`components/DeviceCard.tsx`)
- **Device Information**: Name, type, model, and firmware
- **Status Indicators**: Online/offline, battery level
- **Quick Actions**: Stream cameras, trigger doorbells
- **Real-time Updates**: Live status monitoring

### Security Panel (`components/SecurityPanel.tsx`)
- **System Status**: Armed/disarmed with visual indicators
- **Security Controls**: One-click arm/disarm functionality
- **Device Overview**: Security device status summary
- **Safety Features**: Confirmation and error handling

### Activity Feed (`components/ActivityFeed.tsx`)
- **Event Stream**: Real-time motion and doorbell events
- **Device Context**: Shows which device triggered each event
- **Status Indicators**: Recording status and event details
- **Time Formatting**: Relative timestamps and history

### Navigation (`components/Navigation.tsx`)
- **System Status**: Connection and health indicators
- **Device Summary**: Quick stats in sidebar
- **Security Status**: Current armed/disarmed state
- **Responsive Design**: Collapsible on mobile

## 🔗 API Integration

### Ring MCP Server Connection

The webapp connects to the Ring MCP server via HTTP API:

```typescript
// API Base URL (configured in next.config.js)
const API_BASE = '/api'  // Proxies to http://localhost:8123/api

// Example API calls
const devices = await ringApi.getDevices()
const events = await ringApi.getDeviceEvents(deviceId)
const streamUrl = await ringApi.getLiveStreamUrl(cameraId)
```

### Real-time Updates

Future enhancements will include WebSocket support for real-time updates:

```typescript
// Planned: WebSocket connection for live events
const socket = io('/api/socket')
socket.on('device_status', (data) => {
  // Update device status in real-time
})
```

## 🎯 Usage Scenarios

### Testing Ring MCP Server
1. **Start the Ring MCP server**: `ring-mcp` or via Docker
2. **Launch the webapp**: `npm run dev`
3. **Test device discovery**: View all connected Ring devices
4. **Test device controls**: Arm/disarm security, trigger chimes
5. **Monitor activity**: Watch real-time events and status updates

### Demo and Presentation
1. **Device Management**: Show all Ring devices in an elegant interface
2. **Security Controls**: Demonstrate security system management
3. **Live Monitoring**: Display real-time activity and status
4. **Responsive Design**: Works on any screen size

### Development Testing
1. **API Testing**: Verify all Ring MCP endpoints work correctly
2. **UI Testing**: Test responsive design and user interactions
3. **Performance Testing**: Monitor loading times and responsiveness
4. **Error Handling**: Test failure scenarios and recovery

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file:

```bash
# Ring MCP API URL (optional, defaults to proxy)
NEXT_PUBLIC_RING_API_URL=/api

# WebSocket URL for real-time updates (future)
NEXT_PUBLIC_WS_URL=ws://localhost:8123
```

### Tailwind Customization

Modify `tailwind.config.ts` to customize colors and themes:

```typescript
colors: {
  ring: {
    50: '#f0f9ff',
    500: '#0ea5e9',
    600: '#0284c7',
    // ... more colors
  }
}
```

## 🚀 Development

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

### Adding New Components

1. **Create component**: `components/NewComponent.tsx`
2. **Add types**: Update `types/ring.ts` if needed
3. **Export from index**: Add to component exports
4. **Use in pages**: Import and use in pages

### API Integration

1. **Add API method**: Update `lib/api.ts`
2. **Add types**: Update `types/ring.ts`
3. **Create component**: Use new API in components
4. **Handle errors**: Add proper error handling

## 📱 Responsive Design

The webapp is fully responsive with:

- **Mobile-first**: Optimized for mobile devices
- **Tablet support**: Adapts to tablet screen sizes
- **Desktop enhancement**: Full-featured desktop experience
- **Touch-friendly**: Large touch targets and gestures

## 🎨 Theming

### Current Theme
- **Primary Colors**: Ring blue (#0ea5e9) and security colors
- **Background**: Clean white with subtle gradients
- **Typography**: Inter font family for modern look
- **Shadows**: Soft shadows for depth without harshness

### Future Enhancements
- **Dark Mode**: Toggle between light and dark themes
- **Custom Themes**: User-selectable color schemes
- **High Contrast**: Accessibility-focused theme option

## 🔒 Security Features

- **No Credentials Stored**: Never stores Ring credentials in browser
- **Secure API Calls**: All API calls go through secure backend
- **Input Validation**: Client-side validation for all inputs
- **Error Handling**: Graceful error handling without exposing sensitive data

## 📈 Performance

- **Fast Loading**: Optimized bundles and lazy loading
- **Efficient Updates**: Minimal re-renders with React best practices
- **API Optimization**: Debounced requests and caching
- **Image Optimization**: Next.js automatic image optimization

## 🐛 Troubleshooting

### Common Issues

#### "Failed to connect to Ring MCP server"
```bash
# Check if Ring MCP server is running
curl http://localhost:8123/api/v1/health

# Start Ring MCP server
ring-mcp
```

#### "No devices found"
```bash
# Check Ring credentials
echo $RING_USERNAME

# Test Ring MCP server directly
curl http://localhost:8123/api/v1/devices
```

#### "Build errors"
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

## 🤝 Contributing

### Code Style
- **TypeScript**: Strict type checking enabled
- **ESLint**: Next.js recommended rules
- **Prettier**: Automatic code formatting (planned)

### Component Guidelines
- **Functional Components**: Use modern React patterns
- **TypeScript**: Full type safety required
- **Tailwind**: Utility-first CSS approach
- **Accessibility**: ARIA labels and keyboard navigation

### Testing
- **Component Tests**: React Testing Library (planned)
- **E2E Tests**: Playwright integration (planned)
- **API Tests**: Mock API responses for component testing

## 📄 License

MIT License - See main Ring MCP project LICENSE file.

## 🙏 Acknowledgments

- **Ring MCP Team**: For the excellent backend API
- **Next.js Team**: For the amazing React framework
- **Tailwind CSS**: For the utility-first CSS framework
- **Lucide**: For the beautiful icon set
- **Framer Motion**: For smooth animations

---

**Ring MCP Webapp** - Because your security dashboard should be as beautiful as it is functional! 🏠✨🛡️
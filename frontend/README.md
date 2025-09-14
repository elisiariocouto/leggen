# Leggen Frontend

A modern React dashboard for the Leggen Open Banking CLI tool. This frontend provides a user-friendly interface to view bank accounts, transactions, and balances.

## Features

- **Modern Dashboard**: Clean, responsive interface built with React and TypeScript
- **Bank Accounts Overview**: View all connected bank accounts with real-time balances
- **Transaction Management**: Browse, search, and filter transactions across all accounts
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Data**: Powered by React Query for efficient data fetching and caching

## Prerequisites

- Node.js 18+ and npm
- Leggen API server running (configurable via environment variables)

## Getting Started

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Start the development server:**

   ```bash
   npm run dev
   ```

3. **Open your browser to:**
   ```
   http://localhost:5173
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Architecture

### Key Technologies

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **Axios** - HTTP client for API calls
- **Lucide React** - Modern icon library

### Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.tsx    # Main dashboard layout
│   ├── AccountsOverview.tsx
│   └── TransactionsList.tsx
├── lib/                # Utilities and API client
│   ├── api.ts          # API client and endpoints
│   └── utils.ts        # Helper functions
├── types/              # TypeScript type definitions
│   └── api.ts          # API response types
└── App.tsx             # Main application component
```

## API Integration

The frontend connects to the Leggen API server (configurable via environment variables). The API client handles:

- Account retrieval and management
- Transaction fetching with filtering
- Balance information
- Error handling and loading states

## Configuration

### API URL Configuration

The frontend supports configurable API URLs through environment variables:

**Development:**

- Set `VITE_API_URL` to call external APIs during development
- Example: `VITE_API_URL=https://staging-api.example.com npm run dev`

**Production:**

- Uses relative URLs (`/api/v1`) that nginx proxies to the backend
- Configure nginx proxy target via `API_BACKEND_URL` environment variable
- Default: `http://leggen-server:8000`

**Docker Compose:**

```bash
# Override API backend URL
API_BACKEND_URL=https://prod-api.example.com docker-compose up
```

## Development

The dashboard is designed to work with the Leggen CLI tool's API endpoints. Make sure your Leggen server is running before starting the frontend development server.

### Adding New Features

1. Define TypeScript types in `src/types/api.ts`
2. Add API methods to `src/lib/api.ts`
3. Create React components in `src/components/`
4. Use React Query for data fetching and state management

## Deployment

Build the application for production:

```bash
npm run build
```

The built files will be in the `dist/` directory, ready to be served by any static web server.

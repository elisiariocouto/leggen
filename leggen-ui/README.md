# Leggen UI

A modern financial dashboard built with SvelteKit, TypeScript, TailwindCSS, and shadcn-svelte components.

## Features

- 📊 **Dashboard** - Overview of financial transactions
- 💳 **Transactions** - Detailed transaction management
- 🏦 **Accounts** - Bank account overview
- ⚙️ **Settings** - Configuration management
- 🎨 **Modern UI** - Built with shadcn-svelte components
- 📱 **Responsive Design** - Works on all devices

## Tech Stack

- **SvelteKit** - Full-stack Svelte framework
- **TypeScript** - Type-safe JavaScript
- **TailwindCSS** - Utility-first CSS framework
- **shadcn-svelte** - High-quality UI components
- **Lucide Svelte** - Beautiful icons

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm, pnpm, or yarn package manager

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open your browser to `http://localhost:5173`

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check

# Linting and formatting
npm run lint
npm run format
```

## Adding shadcn-svelte Components

This project uses [shadcn-svelte](https://shadcn-svelte.com/) for UI components. To add new components:

### 1. Browse Available Components

Visit [shadcn-svelte.com](https://shadcn-svelte.com/) to see all available components.

### 2. Add Components

Use the CLI to add components to your project:

```bash
# Add a single component
npx shadcn-svelte@latest add button

# Add multiple components at once
npx shadcn-svelte@latest add card dialog sheet

# Add all components (not recommended for most projects)
npx shadcn-svelte@latest add --all
```

### 3. Use Components in Your Code

After adding components, import and use them in your Svelte files:

```svelte
<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
</script>

<Card class="w-96">
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description goes here</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Card content</p>
    <Button>Click me</Button>
  </CardContent>
</Card>
```

### 4. Commonly Used Components

Here are some frequently used components you might want to add:

```bash
# Form components
npx shadcn-svelte@latest add input label textarea select

# Layout components
npx shadcn-svelte@latest add card separator

# Navigation components
npx shadcn-svelte@latest add navigation-menu breadcrumb

# Feedback components
npx shadcn-svelte@latest add alert toast dialog

# Data display components
npx shadcn-svelte@latest add table badge avatar
```

### 5. Customization

Components are installed in `src/lib/components/ui/` and can be customized:

- **Styling**: Modify the component files directly
- **Variants**: Use `tailwind-variants` to create new component variants
- **Themes**: Modify the CSS variables in `src/app.css`

### 6. Component Documentation

Each component comes with:
- TypeScript definitions
- Full customization options
- Accessibility features built-in
- Examples and usage patterns

## Project Structure

```
src/
├── lib/
│   ├── components/
│   │   ├── ui/          # shadcn-svelte components
│   │   ├── Navbar.svelte
│   │   └── Sidebar.svelte
│   └── assets/
├── routes/
│   ├── +layout.svelte   # App layout with sidebar & navbar
│   └── +page.svelte     # Dashboard page
└── app.css             # Global styles & CSS variables
```

## Deployment

To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment:

```bash
# For Vercel
npm install @sveltejs/adapter-vercel

# For Netlify
npm install @sveltejs/adapter-netlify

# For static sites
npm install @sveltejs/adapter-static
```

Then update your `svelte.config.js` to use the appropriate adapter.

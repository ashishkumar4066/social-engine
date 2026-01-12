# Social Intelligence Engine - Frontend

A React + TypeScript frontend application for the Social Intelligence Engine API. This application provides a user-friendly interface to browse companies, view entity analysis, and explore Reddit mentions.

## Features

- **Home Page**: Overview of available API endpoints and quick navigation
- **Companies List**: Browse all analyzed companies with details
- **Company Details**: View comprehensive information about a specific company including:
  - Company profile (domain, industry, description)
  - Keywords, products, and technologies
  - Statistics (entities, mentions, subreddits, posts)
  - Top subreddits with business value scores
- **Entity Browser**: Explore resolved entities with:
  - Entity names, types (ORG, PERSON, PRODUCT), and aliases
  - Mention counts and confidence scores
  - Contextual mentions from Reddit posts
  - Subreddit sources

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **CSS** for styling (no external UI frameworks)

## Project Structure

```
src/
├── api.ts              # API service layer for backend communication
├── types.ts            # TypeScript type definitions
├── App.tsx             # Main app component with routing
├── App.css             # Global styles and navigation
├── pages/
│   ├── Home.tsx        # Landing page
│   ├── Home.css
│   ├── Companies.tsx   # Companies list view
│   ├── Companies.css
│   ├── CompanyDetail.tsx  # Company detail view
│   ├── CompanyDetail.css
│   ├── EntityBrowser.tsx  # Entity browser UI
│   └── EntityBrowser.css
└── main.tsx           # App entry point
```

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure the API URL (optional):
Edit `.env` file:
```
VITE_API_URL=http://localhost:8000
```

### Development

Run the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## API Integration

The frontend communicates with the FastAPI backend through the `api.ts` service layer. All API endpoints are typed using TypeScript interfaces defined in `types.ts`.

### API Endpoints Used

- `GET /companies` - List all companies
- `GET /companies/{id}` - Get company details
- `GET /companies/{id}/subreddits` - Get company subreddits
- `GET /companies/{id}/entities` - Get company entities
- `GET /companies/{id}/summary` - Get company statistics
- `GET /entities/{id}/mentions` - Get entity mentions

## Component Details

### Home Page
Shows a welcome message and lists all available API endpoints with descriptions.

### Companies Page
Displays a grid of company cards with:
- Company name and domain
- Industry tag
- Description
- Products and technologies

### Company Detail Page
Shows comprehensive company information with:
- Header with company name, domain, and industry
- Statistics dashboard (4 stat cards)
- Keywords, products, and technologies as tags
- Top 10 subreddits with subscriber counts and business value scores
- Link to entity browser

### Entity Browser Page
Displays entities discovered for a company:
- Statistics overview
- Entity cards with icons for type (🏢 ORG, 👤 PERSON, 📦 PRODUCT)
- Entity aliases
- Top 5 mentions per entity with context and confidence scores
- Source subreddit for each mention

## Styling

The app uses a clean, modern design with:
- Purple accent color (#667eea) for primary actions
- Card-based layout with subtle shadows
- Responsive grid layouts
- Hover effects for interactive elements
- Color-coded tags for different entity types

## Environment Variables

- `VITE_API_URL` - Backend API base URL (default: http://localhost:8000)

## Development Notes

- All components are functional components using React Hooks
- State management uses `useState` and `useEffect`
- Navigation uses React Router v6
- Error handling displays user-friendly messages
- Loading states are shown during API calls

## Future Enhancements

- Add search and filtering for companies and entities
- Implement pagination for large datasets
- Add data visualization (charts, graphs)
- Implement authentication if needed
- Add dark mode toggle
- Export data functionality

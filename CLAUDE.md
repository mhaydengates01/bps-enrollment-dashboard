# BPS Enrollment Dashboard - AI Coding Assistant Context

## Project Purpose
Single-page React dashboard analyzing Boston Public Schools enrollment data (2020-2024) with focus on insights for underprivileged schools.

## Tech Stack

**Frontend**
- React 18 + Vite
- ShadCN/UI + Tailwind CSS
- ApexCharts (react-apexcharts)

**Backend/Database**
- Supabase (PostgreSQL)
- Direct queries using @supabase/supabase-js
- **No custom backend server** - uses Supabase auto-generated REST API

**Data Pipeline**
- n8n workflows for ETL from DESE data sources

## Architecture

### Single-Page Application
- All functionality client-side
- Direct Supabase queries from React components
- No Express/Node.js backend
- No custom API endpoints

### Data Access Pattern
```javascript
// src/services/enrollmentService.js
import { supabase } from './supabaseClient'

export async function getSchoolEnrollment(filters) {
  const { data, error } = await supabase
    .from('enrollment')
    .select('*')
    .eq('school_id', filters.schoolId)
  
  if (error) throw error
  return data
}
```

### Component Pattern
- Use hooks (useState, useEffect) for data fetching
- Custom hooks for reusable data logic
- Handle loading/error states
- Transform data for visualizations

## Environment Variables
```
VITE_SUPABASE_URL=your_project_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

## Database Schema (Key Tables)

- `schools` - School metadata
- `enrollment` - Core enrollment by year/school/grade
- `demographics` - Race/ethnicity/gender breakdowns
- `selected_populations` - ELL, SPED, economically disadvantaged
- `accountability` - Performance metrics
- `mcas_results` - Assessment data

Design for:
- Efficient dashboard queries
- Filtering by year, school, demographic
- Aggregation for visualizations

## Code Style & Preferences

- Functional components with hooks
- Keep components focused and composable
- Extract reusable logic to custom hooks
- Use ShadCN components for UI consistency
- Tailwind for styling (utility-first)
- Handle errors gracefully with user-friendly messages

## Key Visualizations to Support

- Enrollment trends (line charts)
- Demographic breakdowns (pie/donut charts)
- School comparisons (bar charts)
- Year-over-year changes (area charts)
- Focus on highlighting equity gaps

## Development Priorities

1. Core functionality over advanced features
2. Working code over perfect architecture
3. Simple solutions for 4-week timeline
4. Performance matters (dashboard should be responsive)
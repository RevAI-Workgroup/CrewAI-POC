# CrewAI Frontend Development - AI Agent Task Brief

## Project Context
You are implementing the frontend for a CrewAI Graph Builder application. The frontend will be located in the `frontend/` directory and connects to the backend API to allow users to create and execute CrewAI crews through visual graphs.

## Compliance Requirements
This development MUST follow the AI Coding Agent Policy. All work requires:
- Task-driven development with agreed-upon authorizing tasks
- PBI association for all tasks
- Proper documentation structure in `docs/delivery/`
- Status synchronization between index and individual task files
- External package research with guide creation

## Product Backlog Item (PBI)

### PBI-002: CrewAI Frontend Application Development

**User Story**: As a user, I need a modern React frontend application that allows me to register with a pseudo and login with a generated passphrase, create and manage CrewAI crews through a visual graph interface, so that I can build and execute AI workflows without password complexity.

**Status**: Proposed → (awaiting User approval to move to Agreed)

**Conditions of Satisfaction**:
1. React + Vite + TypeScript project setup with modern tooling
2. React Router v6 routing system with protected routes
3. Responsive layout system with sidebar navigation
4. **Pseudo/Passphrase authentication system** with register/login flows
5. Visual graph editor using React Flow for crew creation
6. Real-time graph editing with backend synchronization
7. Node definition structure integration from backend API
8. Comprehensive error handling and loading states
9. Modern UI with Tailwind CSS and component library
10. Full TypeScript integration with proper type safety
11. Complete testing suite (unit, integration, e2e)
12. Performance optimization and responsive design

## Authentication System Details

### **Pseudo/Passphrase Authentication Flow**

The backend uses a unique authentication system that replaces traditional email/password with:

#### **Registration Process:**
1. **User Input**: User provides only a `pseudo` (display name, non-unique)
2. **Passphrase Generation**: Backend generates a unique 6-word passphrase 
3. **Auto-Login**: Registration response includes JWT tokens for immediate login
4. **Passphrase Display**: Frontend must prominently display generated passphrase for user to save

**Registration Request:**
```typescript
interface RegisterRequest {
  pseudo: string;  // Display name (1-100 chars, non-unique)
}
```

**Registration Response:**
```typescript
interface RegisterResponse {
  id: string;
  pseudo: string;
  role: 'user' | 'admin';
  passphrase: string;          // Generated 6-word passphrase (SAVE THIS!)
  created_at: string;
  updated_at: string;
  access_token: string;        // JWT for immediate login
  refresh_token: string;       // For session management  
  token_type: 'bearer';
  expires_in: number;          // Token expiration (seconds)
}
```

#### **Login Process:**
1. **User Input**: User provides only their `passphrase` (no pseudo needed)
2. **Authentication**: Backend validates passphrase and returns JWT tokens
3. **Session Management**: Frontend stores tokens and manages refresh

**Login Request:**
```typescript
interface LoginRequest {
  passphrase: string;  // 6-word passphrase (e.g., "apple-harbor-crystal-journey-thunder-violet")
}
```

**Login Response:**
```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: {
    id: string;
    pseudo: string;
    role: 'user' | 'admin';
    created_at: string;
    updated_at: string;
    last_login?: string;
  };
}
```

#### **Passphrase Format:**
- **Pattern**: `word-word-word-word-word-word` (6 words separated by hyphens)
- **Example**: `backstage-epileptic-wimp-petunia-outpost-undergrad`
- **Uniqueness**: Each passphrase is globally unique across all users
- **Word Pool**: ~70 carefully selected words for readability and uniqueness

#### **Frontend Authentication Requirements:**

1. **Registration UI Must:**
   - Provide pseudo input field with 1-100 character validation
   - Display generated passphrase prominently with copy-to-clipboard
   - Show warning to save passphrase (it's their only login method)
   - Auto-login user after successful registration
   - Provide option to download/print passphrase for safekeeping

2. **Login UI Must:**
   - Provide single passphrase input field (no pseudo field)
   - Support paste functionality for 6-word format
   - Validate passphrase format client-side before submission
   - Handle "invalid passphrase" errors gracefully
   - Provide "forgot passphrase" guidance (contact admin)

3. **Session Management Must:**
   - Store JWT tokens securely (httpOnly cookies recommended)
   - Implement automatic token refresh (tokens expire in 30 minutes)
   - Handle logout by clearing all stored authentication data
   - Redirect to login on token expiration
   - Show user's pseudo in header/profile areas

4. **Security Considerations:**
   - No password strength requirements (passphrase is generated)
   - No password reset functionality (new registration required)
   - No email/username recovery (contact admin for account issues)
   - Rate limiting on login attempts (backend handles this)

## Technical Stack Requirements
- **Framework**: React 18 + Vite (for fast builds and HMR)
- **Routing**: React Router v6 (mandatory version)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS + Shadcn UI components
- **Graph Editor**: React Flow (for visual node editing)
- **State Management**: Zustand (lightweight, TypeScript-friendly)
- **HTTP Client**: Axios with interceptors for auth
- **Testing**: Vitest + React Testing Library + Playwright
- **Location**: `frontend/` directory

## Task Breakdown Strategy

The PBI will be broken into minimal, testable tasks following these categories:

### Phase 1: Foundation & Setup (Tasks 2-1 through 2-6)
1. **2-1**: Project setup with Vite + React + TypeScript
2. **2-2**: Tailwind CSS and component library integration
3. **2-3**: React Router v6 setup with basic routing
4. **2-4**: Project structure and configuration
5. **2-5**: Development tooling (ESLint, Prettier, Husky)
6. **2-6**: Environment configuration and build setup

### Phase 2: Pseudo/Passphrase Authentication System (Tasks 2-7 through 2-12)
7. **2-7**: Authentication store with Zustand for pseudo/passphrase system
8. **2-8**: Registration form with pseudo input and passphrase display
9. **2-9**: Login form with passphrase-only authentication
10. **2-10**: JWT token management and auto-refresh functionality
11. **2-11**: Protected route components with token validation
12. **2-12**: Authentication flow integration with pseudo/passphrase backend

### Phase 3: Layout & Navigation (Tasks 2-13 through 2-18)
13. **2-13**: Main layout component structure
14. **2-14**: Sidebar navigation with routing
15. **2-15**: Header component with user pseudo display and logout
16. **2-16**: Responsive layout implementation
17. **2-17**: Theme system (dark/light mode)
18. **2-18**: Layout state management

### Phase 4: Graph Management (Tasks 2-19 through 2-24)
19. **2-19**: Graph store and CRUD operations
20. **2-20**: Graph list view component
21. **2-21**: Graph creation and editing forms
22. **2-22**: Graph deletion with confirmation
23. **2-23**: Graph metadata management
24. **2-24**: Backend API integration for graphs

### Phase 5: React Flow Integration (Tasks 2-25 through 2-30)
25. **2-25**: React Flow setup and configuration
26. **2-26**: Node definitions from backend API
27. **2-27**: Basic node types (Crew, Agent, Task, LLM)
28. **2-28**: Node creation and deletion
29. **2-29**: Edge connections and validation
30. **2-30**: Graph canvas controls and interactions

### Phase 6: Advanced Graph Editor (Tasks 2-31 through 2-36)
31. **2-31**: Node property panels and forms
32. **2-32**: Field visibility and dynamic forms
33. **2-33**: Node validation and error display
34. **2-34**: Real-time graph synchronization
35. **2-35**: Undo/redo functionality
36. **2-36**: Graph export and import features

### Phase 7: UI/UX Enhancements (Tasks 2-37 through 2-42)
37. **2-37**: Loading states and skeletons
38. **2-38**: Error boundaries and error handling
39. **2-39**: Toast notifications system
40. **2-40**: Confirmation dialogs and modals
41. **2-41**: Keyboard shortcuts and accessibility
42. **2-42**: Mobile responsiveness optimization

### Phase 8: Testing & Quality (Tasks 2-43 through 2-48)
43. **2-43**: Unit tests for components and hooks
44. **2-44**: Integration tests for stores and API
45. **2-45**: E2E tests for complete workflows
46. **2-46**: Performance testing and optimization
47. **2-47**: Accessibility testing and compliance
48. **2-48**: E2E CoS Test for complete PBI verification

## AI Agent Instructions

### Environment: Windows with PowerShell
- Use PowerShell commands for all terminal operations
- Use `bun` for package management
- Use Windows-style paths when needed
- Vite dev server runs on `bun run dev`

### Response Style: CONCISE
- Keep all responses brief and to the point
- No lengthy explanations unless specifically requested
- Focus on actionable items and direct answers
- Use bullet points or numbered lists for clarity
- Avoid verbose descriptions
- **Use as few command/tool calls as possible** - batch operations when feasible

### Frontend-Specific Requirements:
- **React Router v6** is mandatory - no other routing library
- All components must be TypeScript with proper types
- Use functional components with hooks only
- Implement proper error boundaries
- Follow React best practices and performance patterns
- All API calls must handle loading and error states

### For Each Task:
1. **Before Starting**: Confirm PBI association and get User approval
2. **Research Phase**: For external packages (React Flow, Zustand, etc.), create `<task_id>-<package>-guide.md` in `docs/delivery/PBI-002/guides/`
3. **Implementation**: Follow task scope exactly, no gold-plating
4. **Testing**: Implement tests per task's test plan
5. **Documentation**: Update component documentation and storybook
6. **Status Updates**: Maintain status in both index and individual task files
7. **Completion**: Commit with format `<task_id> <task_description>`

### File Structure Required:
```
docs/delivery/PBI-002/
├── prd.md                           # PBI detail document
├── tasks.md                         # Task index
├── guides/                          # Package research guides
│   ├── 2-25-react-flow-guide.md
│   ├── 2-3-router-v6-guide.md
│   └── ...
└── tasks/                           # Individual task files
    ├── PBI-002-1.md                 # Task 2-1 details
    ├── PBI-002-2.md                 # Task 2-2 details
    └── ...

frontend/
├── src/
│   ├── components/                  # Reusable components
│   ├── pages/                       # Page components
│   ├── layouts/                     # Layout components
│   ├── stores/                      # Zustand stores
│   ├── hooks/                       # Custom hooks
│   ├── services/                    # API services
│   ├── types/                       # TypeScript types
│   ├── utils/                       # Utility functions
│   └── assets/                      # Static assets
├── tests/                           # Test files
├── public/                          # Public assets
└── docs/                           # Component documentation
```

### Technical Constraints:
- React Router v6 with data router pattern
- TypeScript strict mode enabled
- All components must be accessible (WCAG 2.1)
- Mobile-first responsive design
- Performance budget: < 3s initial load
- Bundle size optimization required
- SEO-friendly routing structure

### Backend API Integration:
- Base API URL: `http://localhost:8000/api` as env variable
- Authentication: JWT Bearer tokens
- Available endpoints:
  - `POST /auth/register` - User registration (pseudo → passphrase generation)
  - `POST /auth/login` - User login (passphrase-only authentication)
  - `POST /auth/refresh` - JWT token refresh for session management
  - `GET /graphs` - List user graphs
  - `POST /graphs` - Create graph
  - `PUT /graphs/{id}` - Update graph
  - `DELETE /graphs/{id}` - Delete graph
  - `GET /graph-nodes` - Get node definitions structure

### Success Metrics:
- Each task passes its defined test plan
- All routes work correctly with React Router v6
- **Pseudo/passphrase authentication flow is intuitive and secure**
- **Registration clearly displays generated passphrase with save instructions**
- **Login works seamlessly with passphrase-only input**
- Graph editor provides intuitive visual interface
- Application is responsive across all device sizes
- Performance meets defined budget constraints
- Accessibility score of 95+ on Lighthouse

## Next Steps
1. User approves PBI-002 (Proposed → Agreed)
2. Create PBI detail document (`docs/delivery/PBI-002/prd.md`)
3. Create task index (`docs/delivery/PBI-002/tasks.md`)
4. Begin with Task 2-1: Project setup with Vite + React + TypeScript

## Questions for User Approval:
1. Does the pseudo/passphrase authentication system understanding look accurate?
2. Are the authentication UI requirements appropriate for user experience?
3. Should any authentication-related tasks be combined or further split?
4. Do you approve moving PBI-002 from Proposed to Agreed status?
5. Are there any additional React libraries or tools you'd prefer to include? 
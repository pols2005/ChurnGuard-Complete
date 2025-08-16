# ChurnGuard UI Enhancement API Reference

## Context Providers

### ThemeProvider

Provides theme management functionality throughout the application.

```jsx
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
```

#### Props
- `children`: React.ReactNode - Child components

#### Hook: useTheme()

Returns theme management functions and state.

**Return Object:**
```typescript
{
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: string) => void;
  resolvedTheme: 'light' | 'dark';
}
```

**Example:**
```jsx
function MyComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  
  return (
    <div className={`theme-${resolvedTheme}`}>
      Current theme: {theme}
      <button onClick={() => setTheme('dark')}>
        Switch to Dark
      </button>
    </div>
  );
}
```

---

### OrganizationProvider

Manages organization branding and white-labeling settings.

```jsx
import { OrganizationProvider, useOrganization } from './contexts/OrganizationContext';
```

#### Hook: useOrganization()

**Return Object:**
```typescript
{
  organization: {
    name: string;
    logoUrl: string;
    primaryColor: string;
    secondaryColor: string;
    customCss: string;
    tier: 'starter' | 'professional' | 'enterprise';
  };
  updateOrganization: (updates: Partial<Organization>) => void;
  resetToDefault: () => void;
}
```

**Example:**
```jsx
function BrandedHeader() {
  const { organization, updateOrganization } = useOrganization();
  
  const handleColorChange = (color) => {
    updateOrganization({ primaryColor: color });
  };
  
  return (
    <header style={{ 
      backgroundColor: organization.primaryColor,
      color: 'white'
    }}>
      {organization.logoUrl && (
        <img src={organization.logoUrl} alt="Logo" className="h-8" />
      )}
      <h1>{organization.name}</h1>
    </header>
  );
}
```

---

### SubscriptionProvider

Handles subscription tiers and feature access control.

```jsx
import { SubscriptionProvider, useSubscription, SUBSCRIPTION_TIERS } from './contexts/SubscriptionContext';
```

#### Hook: useSubscription()

**Return Object:**
```typescript
{
  currentTier: 'starter' | 'professional' | 'enterprise';
  usage: {
    users: number;
    dataExports: number;
    apiCalls: number;
  };
  hasFeature: (feature: string) => boolean;
  canUse: (feature: string, count?: number) => boolean;
  incrementUsage: (feature: string, amount?: number) => void;
  upgradeTo: (tier: string) => void;
  getCurrentTierInfo: () => TierInfo;
  getUpgradeOptions: () => TierInfo[];
  SUBSCRIPTION_TIERS: object;
}
```

**Example:**
```jsx
function PremiumButton() {
  const { hasFeature, upgradeTo, currentTier } = useSubscription();
  
  if (!hasFeature('advancedAnalytics')) {
    return (
      <button onClick={() => upgradeTo('professional')}>
        Upgrade to Professional for Advanced Analytics
      </button>
    );
  }
  
  return <AdvancedAnalyticsButton />;
}
```

---

## Components

### FeatureGate

Controls access to premium features based on subscription tier.

```jsx
import FeatureGate from './components/FeatureGate';
```

#### Props
```typescript
{
  feature: string;                    // Feature key from SUBSCRIPTION_TIERS
  children: React.ReactNode;          // Premium content
  fallback?: React.ReactNode;         // Content for non-premium users
  showUpgradePrompt?: boolean;        // Show upgrade UI (default: true)
  requiredTier?: string;              // Override required tier message
}
```

**Example:**
```jsx
function CustomColorPicker() {
  return (
    <FeatureGate 
      feature="customColors" 
      requiredTier="professional"
      fallback={<BasicColorPicker />}
    >
      <AdvancedColorPicker />
    </FeatureGate>
  );
}
```

---

### ThemeToggle

Button component for switching between theme modes.

```jsx
import ThemeToggle from './components/ThemeToggle';
```

#### Props
- No required props - uses theme context internally

**Features:**
- Cycles through: Light → Dark → System
- Shows current theme icon
- Displays theme label on larger screens
- Tooltip with current theme info

**Example:**
```jsx
function AppHeader() {
  return (
    <header className="flex justify-between">
      <Logo />
      <ThemeToggle />
    </header>
  );
}
```

---

### OrganizationSettings

Modal component for configuring organization branding.

```jsx
import OrganizationSettings from './components/OrganizationSettings';
```

#### Props
```typescript
{
  isOpen: boolean;
  onClose: () => void;
}
```

**Features:**
- Organization name editing
- Logo upload (Professional+)
- Color customization (Professional+)
- Custom CSS injection (Enterprise)
- Real-time preview
- Usage dashboard integration

**Example:**
```jsx
function SettingsModal() {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Settings
      </button>
      <OrganizationSettings 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
      />
    </>
  );
}
```

---

### CustomizableLayout

Enterprise-level layout customization wrapper.

```jsx
import CustomizableLayout from './components/CustomizableLayout';
```

#### Props
```typescript
{
  children: React.ReactNode;
}
```

**Features (Enterprise only):**
- Dynamic grid columns (1-4)
- Sidebar positioning
- Widget arrangement
- Layout persistence
- Quick actions sidebar

**Example:**
```jsx
function Dashboard() {
  return (
    <CustomizableLayout>
      <CustomerForm />
      <AnalyticsWidget />
      <ChurnMeter />
      <ExportTools />
    </CustomizableLayout>
  );
}
```

---

### PremiumAnalytics

Advanced analytics dashboard with feature gating.

```jsx
import PremiumAnalytics from './components/PremiumAnalytics';
```

#### Props
```typescript
{
  data?: object;  // Optional analytics data
}
```

**Features:**
- Cohort analysis (Professional+)
- Customer segmentation (Professional+)
- Churn prediction insights (Professional+)
- Basic metrics (all tiers)

---

### PerformanceMonitor

Real-time performance tracking component.

```jsx
import PerformanceMonitor from './components/PerformanceMonitor';
```

#### Props
- No props - self-contained monitoring

**Metrics Tracked:**
- Load time
- Theme switch performance
- Memory usage
- API response times
- Frame rate
- Overall performance score

---

### UsageDashboard

Displays current subscription usage and limits.

```jsx
import UsageDashboard from './components/UsageDashboard';
```

#### Props
- No props - uses subscription context

**Features:**
- User count tracking
- Data export usage
- Feature availability status
- Upgrade prompts for limits
- Visual usage indicators

---

### ExportFeature

Data export functionality with subscription gating.

```jsx
import ExportFeature from './components/ExportFeature';
```

#### Props
```typescript
{
  data?: object;  // Data to export
}
```

**Features:**
- JSON export format
- CSV export format
- Professional+ feature gating
- Usage tracking integration
- Download progress indication

---

## Utility Functions

### Test Utilities

```jsx
import { 
  renderWithProviders, 
  mockApiResponses, 
  setupFetchMock,
  createMockCustomer,
  cleanup 
} from './test-utils';
```

#### renderWithProviders(component, options)
Renders components with all context providers for testing.

**Options:**
```typescript
{
  theme?: 'light' | 'dark' | 'system';
  subscription?: 'starter' | 'professional' | 'enterprise';
  organization?: Partial<Organization>;
}
```

#### setupFetchMock(responses)
Configures fetch mocking for API calls.

#### createMockCustomer(overrides)
Factory for creating test customer data.

---

## CSS Custom Properties

### Theme Variables

```css
/* Root variables */
:root {
  --brand-primary: #DAA520;           /* Gold primary color */
  --brand-primary-dark: #F4D03F;      /* Light gold for dark mode */
  --brand-secondary: #B8860B;         /* Dark gold secondary */
  --brand-secondary-dark: #F7DC6F;    /* Light secondary for dark mode */
  
  --background: #FFFFFF;              /* Light background */
  --background-light: #FFFFFF;        /* Explicit light background */
  --background-dark: #0F0F0F;         /* Dark background */
  
  --surface: #F8F9FA;                 /* Light surface */
  --surface-light: #F8F9FA;           /* Explicit light surface */
  --surface-dark: #1A1A1A;            /* Dark surface */
}

/* Dark mode overrides */
.dark {
  --background: var(--background-dark);
  --surface: var(--surface-dark);
  --brand-primary: var(--brand-primary-dark);
  --brand-secondary: var(--brand-secondary-dark);
}
```

### Organization Variables

```css
/* Set dynamically by OrganizationContext */
:root {
  --org-primary: var(--brand-primary);     /* Organization primary color */
  --org-secondary: var(--brand-secondary); /* Organization secondary color */
  --org-logo-url: '';                      /* Organization logo URL */
  --org-name: 'ChurnGuard';                /* Organization name */
}
```

### Usage in CSS

```css
.branded-button {
  background-color: var(--org-primary);
  border-color: var(--org-secondary);
  transition: all 0.2s ease;
}

.dark .branded-button {
  /* Automatically uses dark mode colors */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
```

---

## Configuration

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',  // Enable class-based dark mode
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          light: 'var(--brand-primary, #DAA520)',
          dark: 'var(--brand-primary-dark, #F4D03F)',
          DEFAULT: 'var(--brand-primary, #DAA520)'
        },
        // ... additional color definitions
      }
    },
  },
  plugins: [],
}
```

### Environment Configuration

```env
# Optional environment variables
REACT_APP_THEME_STORAGE_KEY=churnguard-theme
REACT_APP_ORG_STORAGE_KEY=churnguard-organization
REACT_APP_SUBSCRIPTION_STORAGE_KEY=churnguard-subscription-tier
REACT_APP_USAGE_STORAGE_KEY=churnguard-usage

# Performance monitoring
REACT_APP_PERFORMANCE_MONITORING=true
REACT_APP_PERFORMANCE_SAMPLING_RATE=0.1

# Analytics (optional)
REACT_APP_ANALYTICS_ENABLED=false
REACT_APP_ANALYTICS_ENDPOINT=your-analytics-endpoint
```

---

## Browser Support

### Minimum Requirements
- Chrome 76+ (CSS custom properties)
- Firefox 72+ (CSS custom properties)
- Safari 12.1+ (CSS custom properties)
- Edge 79+ (Chromium-based)

### Progressive Enhancement
- Graceful degradation for older browsers
- Fallback colors in CSS custom properties
- Feature detection for advanced capabilities

### Performance Considerations
- Uses `prefers-color-scheme` media query
- Optimized CSS transitions
- Minimal JavaScript for theme switching
- LocalStorage for theme persistence

---

## Migration Guide

### From v1.x to v2.x

1. **Update Dependencies**
   ```bash
   npm install next-themes
   ```

2. **Wrap App with Providers**
   ```jsx
   // Before
   <App />
   
   // After
   <SubscriptionProvider>
     <OrganizationProvider>
       <ThemeProvider>
         <App />
       </ThemeProvider>
     </OrganizationProvider>
   </SubscriptionProvider>
   ```

3. **Update CSS Classes**
   ```jsx
   // Before
   <div className="bg-gray-900 text-white">
   
   // After  
   <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
   ```

4. **Add Feature Gates**
   ```jsx
   // Before
   <PremiumFeature />
   
   // After
   <FeatureGate feature="advancedAnalytics">
     <PremiumFeature />
   </FeatureGate>
   ```

5. **Test Theme Switching**
   ```jsx
   // Add theme toggle to your header
   import ThemeToggle from './components/ThemeToggle';
   
   <header>
     <Logo />
     <ThemeToggle />
   </header>
   ```
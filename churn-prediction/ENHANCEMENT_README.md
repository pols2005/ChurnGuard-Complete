# ChurnGuard UI Enhancement & White-Labeling Platform

## 🚀 Overview

This enhanced version of ChurnGuard includes a comprehensive SaaS-ready UI enhancement system with dark/light mode support, white-labeling capabilities, subscription-based feature gating, and advanced layout customization.

## ✨ Features Implemented

### Phase 1: Dark/Light Mode Theme System
- **ThemeProvider**: React Context-based theme management
- **Theme Toggle**: Light/Dark/System preference switching
- **CSS Custom Properties**: Dynamic theming with CSS variables
- **Smooth Transitions**: 200ms transition animations
- **Local Storage Persistence**: Theme preferences saved automatically

### Phase 2: White-Labeling Infrastructure  
- **Organization Context**: Complete branding customization system
- **Logo Upload**: Support for custom organization logos
- **Color Customization**: Dynamic primary/secondary color changes
- **Organization Settings**: Comprehensive admin interface
- **Real-time Preview**: Instant branding changes preview

### Phase 3: SaaS Subscription Feature Gating
- **Three-Tier System**: Starter ($29), Professional ($99), Enterprise ($299)
- **FeatureGate Component**: Reusable component for gating premium features
- **Usage Tracking**: Monitor feature usage and limits
- **Upgrade Prompts**: Strategic upgrade conversion flows
- **Subscription Management**: Full tier management system

### Phase 4: Advanced Layout Customization
- **CustomizableLayout**: Enterprise-level layout configuration
- **Widget Dashboard**: Drag-and-drop widget arrangement
- **Performance Monitor**: Real-time performance tracking
- **Sidebar Configuration**: Flexible sidebar positioning
- **Grid System**: Dynamic column layouts (1-4 columns)

### Phase 5: Comprehensive Testing Strategy
- **Unit Tests**: Context providers, components, utilities
- **Integration Tests**: Full theme switching workflows
- **Test Utilities**: Comprehensive testing helpers
- **Mock Services**: Complete API and localStorage mocking
- **Performance Tests**: Theme switching and render performance

## 🏗️ Architecture

### Context Providers
```jsx
<SubscriptionProvider>
  <OrganizationProvider>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </OrganizationProvider>
</SubscriptionProvider>
```

### Theme System
- **CSS Variables**: Dynamic color system with fallbacks
- **Class-based**: Uses Tailwind's `dark:` classes
- **System Preference**: Respects user's OS theme setting
- **Performance**: <100ms theme switching target

### Subscription Tiers

| Feature | Starter | Professional | Enterprise |
|---------|---------|--------------|------------|
| Users | 5 | 25 | Unlimited |
| Theme Switching | ✅ | ✅ | ✅ |
| Logo Upload | ❌ | ✅ | ✅ |
| Custom Colors | ❌ | ✅ | ✅ |
| Custom CSS | ❌ | ❌ | ✅ |
| Advanced Analytics | ❌ | ✅ | ✅ |
| Layout Customization | ❌ | ❌ | ✅ |
| Data Export | ❌ | ✅ | ✅ |

## 🚦 Getting Started

### Prerequisites
- Node.js 16+
- npm or yarn
- React 18+

### Installation
```bash
# Install dependencies
npm install next-themes

# Update Tailwind config for dark mode
# (Already configured in tailwind.config.js)

# Run tests
npm test

# Start development server
npm start
```

### Basic Usage

#### Theme Implementation
```jsx
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

function MyComponent() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  
  return (
    <button onClick={() => setTheme('dark')}>
      Switch to Dark Mode
    </button>
  );
}
```

#### Feature Gating
```jsx
import FeatureGate from './components/FeatureGate';

function PremiumFeature() {
  return (
    <FeatureGate 
      feature="customColors" 
      requiredTier="professional"
      fallback={<BasicVersion />}
    >
      <PremiumVersion />
    </FeatureGate>
  );
}
```

#### Organization Branding
```jsx
import { useOrganization } from './contexts/OrganizationContext';

function BrandedHeader() {
  const { organization } = useOrganization();
  
  return (
    <header style={{ color: organization.primaryColor }}>
      {organization.logoUrl && (
        <img src={organization.logoUrl} alt="Logo" />
      )}
      <h1>{organization.name}</h1>
    </header>
  );
}
```

## 🎨 Customization

### CSS Variables
The system uses CSS custom properties for dynamic theming:

```css
:root {
  --brand-primary: #DAA520;
  --brand-primary-dark: #F4D03F;
  --brand-secondary: #B8860B;
  --brand-secondary-dark: #F7DC6F;
  --background: #FFFFFF;
  --background-dark: #0F0F0F;
  --surface: #F8F9FA;
  --surface-dark: #1A1A1A;
}
```

### Theme Configuration
Modify `src/contexts/ThemeContext.js` to customize theme behavior:

```jsx
// Theme persistence key
const THEME_STORAGE_KEY = 'churnguard-theme';

// Available theme options
const THEME_OPTIONS = ['light', 'dark', 'system'];
```

### Subscription Tier Customization
Update `src/contexts/SubscriptionContext.js` to modify pricing and features:

```jsx
export const SUBSCRIPTION_TIERS = {
  starter: {
    name: 'Starter',
    price: '$29/month',
    limits: {
      users: 5,
      customColors: false,
      // ...
    }
  }
  // ...
};
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test ThemeContext.test.js
```

### Test Structure
```
src/
  __tests__/
    ThemeContext.test.js
    FeatureGate.test.js
    ThemeIntegration.test.js
  test-utils.js
```

### Using Test Utilities
```jsx
import { renderWithProviders, mockApiResponses } from './test-utils';

test('renders with custom subscription tier', () => {
  renderWithProviders(<MyComponent />, {
    subscription: 'professional',
    organization: { name: 'Test Org' }
  });
});
```

## 📱 Components Reference

### Core Components
- **ThemeToggle**: Theme switching button
- **FeatureGate**: Subscription-based feature gating
- **OrganizationSettings**: Branding configuration interface
- **SettingsButton**: Settings panel trigger
- **CustomizableLayout**: Enterprise layout system
- **PerformanceMonitor**: Real-time performance tracking

### Utility Components
- **PremiumAnalytics**: Advanced analytics dashboard
- **ExportFeature**: Data export functionality
- **UsageDashboard**: Subscription usage tracking

## 🎯 Performance

### Targets
- Theme switching: <100ms
- Page load impact: <50ms
- Memory usage: <50MB for core features
- Bundle size increase: <150KB gzipped

### Optimization Features
- CSS transition optimization
- Component lazy loading
- Context provider optimization
- Memoized calculations

## 🔐 Security

### CSS Injection Protection
- DOMPurify for custom CSS sanitization
- Content Security Policy headers recommended
- Whitelist-based CSS property filtering

### Data Privacy
- Local storage encryption for sensitive settings
- No external theme or branding data transmission
- Opt-in analytics tracking only

## 🚀 Deployment

### Build Configuration
```bash
# Production build
npm run build

# Analyze bundle
npm run build -- --analyze
```

### Environment Variables
```env
REACT_APP_SUBSCRIPTION_ENDPOINT=your-api-endpoint
REACT_APP_ANALYTICS_KEY=your-analytics-key
```

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Code Standards
- ESLint configuration enforced
- Prettier formatting
- TypeScript-ready (JSDoc comments)
- 90%+ test coverage target

## 📊 Monitoring

### Success Metrics
- Theme switching adoption: 80% users try dark mode
- White-labeling usage: 60% enterprise customers customize
- Performance: <100ms theme switching
- Subscription conversion: 25% increase in upgrades

### Analytics Events
- Theme changes: `theme_switched`
- Feature gate interactions: `feature_gate_triggered`
- Upgrade button clicks: `upgrade_initiated`
- Branding changes: `organization_updated`

## 🐛 Troubleshooting

### Common Issues

**Theme not persisting**
- Check localStorage permissions
- Verify ThemeProvider wrapper
- Ensure theme context is available

**Feature gate not working**
- Verify subscription tier is set
- Check feature key in SUBSCRIPTION_TIERS
- Ensure SubscriptionProvider wrapper

**Performance issues**
- Check for theme transition conflicts
- Verify CSS custom property support
- Monitor memory usage in dev tools

**Styling conflicts**
- Ensure Tailwind dark mode is enabled
- Check CSS variable fallbacks
- Verify component class ordering

### Support
- GitHub Issues: Report bugs and feature requests
- Documentation: Check component JSDoc comments
- Performance: Use built-in PerformanceMonitor

## 📝 Changelog

### v2.0.0 (Latest)
- ✅ Complete dark/light mode system
- ✅ White-labeling infrastructure
- ✅ SaaS subscription feature gating
- ✅ Advanced layout customization
- ✅ Comprehensive testing suite
- ✅ Performance monitoring
- ✅ Documentation and guides

### Migration from v1.x
1. Update package.json dependencies
2. Add provider wrappers to App.js
3. Update CSS classes for dark mode
4. Configure subscription tiers
5. Test theme switching functionality

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions, issues, or contributions, please contact the development team or create an issue in the GitHub repository.
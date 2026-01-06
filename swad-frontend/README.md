# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

## Image Pipeline

**Swad of Tamil** uses a sophisticated image loading pipeline:

### API Contract
- `image_url`: Full-size image URL (absolute)
- `thumbnail_url`: Thumbnail version for lists/cards (absolute)
- Both fields are always present or null

### Frontend Implementation
- **LazyImage Component**: Progressive loading with blur-up effect
- **Skeleton Loading**: Animated gradient placeholder while loading
- **Error Handling**: Graceful fallback for broken images
- **Lazy Loading**: Only loads images in viewport

### Usage
```jsx
import LazyImage from './components/LazyImage';

// For full-size images
<LazyImage
  src={item.image_url}
  alt={item.name}
  className="w-full h-48 object-cover rounded-lg"
/>

// For thumbnails (lists/cards)
<LazyImage
  src={item.thumbnail_url}
  alt={item.name}
  className="w-20 h-20 object-cover rounded"
/>
```

### Performance Features
- ✅ Viewport-based lazy loading
- ✅ Blur-up transition effect
- ✅ Skeleton loading animation
- ✅ Automatic error handling
- ✅ Memory efficient

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

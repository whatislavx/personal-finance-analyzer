import { RouterProvider } from 'react-router';
import { router } from './routes';
import { AppProvider } from './context/AppContext';

export default function App() {
  return (
    <div className="dark">
      <AppProvider>
        <RouterProvider router={router} />
      </AppProvider>
    </div>
  );
}
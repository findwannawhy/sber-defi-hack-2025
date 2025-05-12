// Импорты React
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";

// Импорты роутера и React Query
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "@/shared/config/router/routeTree.gen";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

// Импорты провайдеров
import { AuthProvider } from '@/app/providers/AuthContext'

// Импорты Shadcn UI и Tailwind CSS
import "@/shared/styles/index.css";

// Создание экземпляров роутера и клиента React Query
const router = createRouter({ routeTree });
const queryClient = new QueryClient();

// Регистрация экземпляра роутера для типобезопасности
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Инициализация корневого элемента DOM
const rootElement = document.getElementById("root")!;

if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                <RouterProvider router={router} />
            </QueryClientProvider>
        </AuthProvider>
    </StrictMode>
  );
}

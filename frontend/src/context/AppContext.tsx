import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type AppContextValue = {
  title: string;
  setTitle: (t: string) => void;
  syncVersion: number;
  bumpSyncVersion: () => void;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [title, setTitle] = useState("Health Assistant");
  const [syncVersion, setSyncVersion] = useState(0);

  return (
    <AppContext.Provider
      value={{
        title,
        setTitle,
        syncVersion,
        bumpSyncVersion: () => setSyncVersion((v) => v + 1),
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within AppProvider");
  return ctx;
}

/** Call from a page to set the shared topbar title. */
export function usePageTitle(title: string) {
  const { setTitle } = useAppContext();
  useEffect(() => {
    setTitle(title);
  }, [title, setTitle]);
}

/** Call from a page to get the current sync counter — bump on sync, so pages can reload their data. */
export function useSyncVersion() {
  return useAppContext().syncVersion;
}

export function useHeader() {
  const { title, bumpSyncVersion } = useAppContext();
  return { title, bumpSyncVersion };
}
